import unittest

import frappe

from losand.api.pos import (
	_resolve_pos_profile,
	get_stocktake_items,
	save_stocktake,
	confirm_transfer,
	get_pos_config,
	get_products,
	get_transfer,
	list_incoming_transfers,
)


PROFILE_BEHAVIOR_KEYS = {
	"allow_discount_change",
	"allow_partial_payment",
	"allow_rate_change",
	"apply_discount_on",
	"auto_add_item_to_cart",
	"disable_grand_total_to_default_mop",
	"disable_rounded_total",
	"hide_images",
	"hide_unavailable_items",
	"ignore_pricing_rule",
	"print_receipt_on_order_complete",
	"update_stock",
	"validate_stock_on_save",
}


class TestPosAPI(unittest.TestCase):
	def setUp(self):
		frappe.set_user("Administrator")

	def test_pos_config_exposes_standard_behavior_settings(self):
		config = get_pos_config()
		self.assertLessEqual(PROFILE_BEHAVIOR_KEYS, set(config))
		self.assertTrue(config["payments"])
		self.assertTrue(config["company"])
		self.assertTrue(config["currency"])
		self.assertTrue(config["price_list"])

	def test_products_honor_hide_unavailable_items(self):
		profile = _resolve_pos_profile()
		if not profile.hide_unavailable_items:
			self.skipTest("Active profile does not hide unavailable items")
		if not profile.update_stock:
			self.skipTest("Profile does not track stock — availability is not read")
		result = get_products(profile.name)
		self.assertTrue(
			all(
				not product["is_stock_item"] or product["available_qty"] > 0
				for product in result["products"]
			)
		)

	def test_disabled_profile_cannot_be_selected_explicitly(self):
		disabled = frappe.get_all(
			"POS Profile",
			filters={"disabled": 1},
			limit=1,
			pluck="name",
		)
		if not disabled:
			self.skipTest("No disabled POS Profile exists")
		with self.assertRaises(frappe.ValidationError):
			_resolve_pos_profile(disabled[0])


class TestPosReceiving(unittest.TestCase):
	"""استلام الطلبات: draft Material Transfers addressed to the branch warehouse are
	received (and submitted) from the POS, at the qty that actually arrived."""

	def setUp(self):
		frappe.set_user("Administrator")
		self.profile = _resolve_pos_profile()
		if not self.profile.warehouse:
			self.skipTest("Active POS Profile has no warehouse")

	def _stocked_item(self):
		"""An item with stock in some OTHER warehouse — the transfer's source."""
		rows = frappe.get_all(
			"Bin",
			filters={"actual_qty": [">", 5], "warehouse": ["!=", self.profile.warehouse]},
			fields=["item_code", "warehouse"],
			limit=20,
		)
		today = frappe.utils.nowdate()
		for row in rows:
			item = frappe.db.get_value("Item", row.item_code, ["disabled", "end_of_life"], as_dict=True)
			if item and not item.disabled and (not item.end_of_life or str(item.end_of_life) > today):
				return row
		return None

	def _draft_transfer(self, source, qty=4):
		se = frappe.new_doc("Stock Entry")
		se.stock_entry_type = "Material Transfer"
		se.company = self.profile.company
		se.from_warehouse = source.warehouse
		se.to_warehouse = self.profile.warehouse
		se.append(
			"items",
			{
				"item_code": source.item_code,
				"qty": qty,
				"s_warehouse": source.warehouse,
				"t_warehouse": self.profile.warehouse,
			},
		)
		se.insert(ignore_permissions=True)
		# confirm_transfer commits, so nothing rolls back: drop whatever is still a draft
		# at the end of the test instead of leaving it in the branch's receiving inbox.
		self.addCleanup(self._drop_if_draft, se.name)
		return se

	def _drop_if_draft(self, name):
		if frappe.db.get_value("Stock Entry", name, "docstatus") == 0:
			frappe.delete_doc("Stock Entry", name, force=True, ignore_permissions=True)
			frappe.db.commit()

	def test_draft_transfer_is_received_at_the_edited_qty(self):
		source = self._stocked_item()
		if not source:
			self.skipTest("No stocked item outside the POS warehouse")
		se = self._draft_transfer(source)

		self.assertIn(se.name, [t["name"] for t in list_incoming_transfers()["transfers"]])
		detail = get_transfer(se.name)
		self.assertEqual(len(detail["items"]), 1)
		self.assertEqual(detail["items"][0]["sent_qty"], 4)

		# short receipt: 4 sent, 3 arrived
		result = confirm_transfer(se.name, [{"row": detail["items"][0]["row"], "qty": 3}])
		self.assertEqual(result["total_qty"], 3)

		doc = frappe.get_doc("Stock Entry", se.name)
		self.assertEqual(doc.docstatus, 1)
		self.assertEqual(doc.items[0].qty, 3)
		self.assertIn("تعديل عند الاستلام", doc.remarks or "")
		self.assertNotIn(se.name, [t["name"] for t in list_incoming_transfers()["transfers"]])

	def test_transfer_to_another_warehouse_is_refused(self):
		other = frappe.get_all(
			"Warehouse",
			filters={"is_group": 0, "name": ["!=", self.profile.warehouse], "company": self.profile.company},
			limit=1,
			pluck="name",
		)
		source = self._stocked_item()
		if not other or not source:
			self.skipTest("No second warehouse / stocked item to build the transfer")
		se = self._draft_transfer(source)
		se.db_set("to_warehouse", other[0])
		frappe.db.set_value("Stock Entry Detail", se.items[0].name, "t_warehouse", other[0])
		with self.assertRaises(frappe.PermissionError):
			get_transfer(se.name)

	def test_receiving_nothing_is_refused(self):
		source = self._stocked_item()
		if not source:
			self.skipTest("No stocked item outside the POS warehouse")
		se = self._draft_transfer(source)
		with self.assertRaises(frappe.ValidationError):
			confirm_transfer(se.name, [{"row": se.items[0].name, "qty": 0}])


class TestPosStocktake(unittest.TestCase):
	"""الجرد اليومي: the count sheet is the branch warehouse, and saving it issues the
	difference between the shelf and the system out of that warehouse."""

	def setUp(self):
		frappe.set_user("Administrator")
		self.profile = _resolve_pos_profile()
		if not self.profile.warehouse:
			self.skipTest("Active POS Profile has no warehouse")

	def test_sheet_lists_what_the_branch_warehouse_holds(self):
		sheet = get_stocktake_items()
		self.assertEqual(sheet["warehouse"], self.profile.warehouse)
		expected = set(frappe.get_all("Bin", filters={"warehouse": self.profile.warehouse}, pluck="item_code"))
		self.assertTrue({row["id"] for row in sheet["items"]} <= expected)

	def test_counting_short_issues_the_difference(self):
		stocked = next(
			(
				row
				for row in get_stocktake_items()["items"]
				if row["system_qty"] >= 2 and not frappe.db.get_value("Item", row["id"], "disabled")
			),
			None,
		)
		if not stocked:
			self.skipTest("Branch warehouse holds nothing to count down")
		before = stocked["system_qty"]
		result = save_stocktake([{"item_code": stocked["id"], "counted": before - 1}])
		self.assertTrue(result["entries"])

		entry = frappe.get_doc("Stock Entry", result["entries"][0])
		self.addCleanup(self._reverse, entry.name)
		self.assertEqual(entry.stock_entry_type, "Material Issue")
		self.assertEqual(entry.from_warehouse, self.profile.warehouse)
		self.assertEqual(sum(row.qty for row in entry.items), 1)
		if entry.meta.has_field("branch") and self.profile.get("losand_branch"):
			self.assertEqual(entry.branch, self.profile.losand_branch)

	def _reverse(self, name):
		"""Put the counted-out qty back, so running the suite does not drain the branch."""
		issue = frappe.get_doc("Stock Entry", name)
		back = frappe.new_doc("Stock Entry")
		back.stock_entry_type = "Material Receipt"
		back.company = issue.company
		back.to_warehouse = issue.from_warehouse
		for row in issue.items:
			back.append(
				"items",
				{
					"item_code": row.item_code,
					"qty": row.qty,
					"t_warehouse": issue.from_warehouse,
					"basic_rate": row.basic_rate or row.valuation_rate,
				},
			)
		back.flags.ignore_permissions = True
		back.insert(ignore_permissions=True)
		back.submit()
		frappe.db.commit()
