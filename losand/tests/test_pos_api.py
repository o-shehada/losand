import unittest

import frappe

from losand.api.pos import _resolve_pos_profile, get_pos_config, get_products


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
