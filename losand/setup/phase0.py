"""Phase-0 scaffold for the no-BOM manufacture redesign.

Creates (idempotently) on the site:
  - Item custom fields: is_final_product, is_raw_material, product_category, classification
  - a Production Clearing account
  - sample data: Product Categories, Shifts, batch-tracked final + raw Items, Workbenches
  - disables the old templates/variants and old non-batch raw items

Run:  bench --site <site> execute losand.setup.phase0.run
"""

import re

import frappe

COMPANY = "Los Andalus"
WEIGHT_UOM = "جم"
FG_GROUP = "Products"
RM_GROUP = "Raw Material"
WAREHOUSES = ("Stores - LA", "Work In Progress - LA", "Finished Goods - LA")

CATEGORIES = ["Chicken Burger", "Beef Burger", "Bread", "Sauce"]
SHIFTS = [("Morning", "08:00:00", "16:00:00"), ("Evening", "16:00:00", "23:59:00")]

# code/name, category, weight (g), shelf life days
FINAL_PRODUCTS = [
	("Chicken Burger 200g", "Chicken Burger", 200, 5),
	("Chicken Burger 120g", "Chicken Burger", 120, 5),
	("Beef Burger 150g", "Beef Burger", 150, 5),
	("Beef Burger 120g", "Beef Burger", 120, 5),
	("Burger Buns 80g", "Bread", 80, 7),
	("BBQ Sauce 50g", "Sauce", 50, 30),
]

# code/name, uom, valuation rate, [categories]
RAW_MATERIALS = [
	("Chicken Mince", "كجم", 30, ["Chicken Burger"]),
	("Beef Mince", "كجم", 45, ["Beef Burger"]),
	("Fresh Eggs", "حبة", 0.75, ["Chicken Burger", "Beef Burger", "Bread"]),
	("Spices", "جم", 0.12, ["Chicken Burger", "Beef Burger", "Sauce"]),
	("Vegetable Oil", "لتر", 8.5, ["Chicken Burger", "Beef Burger", "Bread"]),
	("Bread Crumbs", "كجم", 12, ["Chicken Burger", "Beef Burger"]),
	("Flour", "كجم", 3, ["Bread"]),
	("Tomato", "كجم", 5, ["Sauce"]),
]

# workbench name, category
WORKBENCHES = [
	("Chicken Workbench", "Chicken Burger"),
	("Beef Workbench", "Beef Burger"),
	("Bread Workbench", "Bread"),
	("Sauce Workbench", "Sauce"),
]


def _series(code):
	return re.sub(r"[^A-Za-z0-9]", "", code).upper()[:10] + "-.#####"


def _ensure_custom_fields():
	from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

	create_custom_fields(
		{
			"Item": [
				{"fieldname": "is_final_product", "label": "Is Final Product", "fieldtype": "Check", "insert_after": "stock_uom"},
				{"fieldname": "product_category", "label": "Product Category", "fieldtype": "Link", "options": "Product Category", "insert_after": "is_final_product", "depends_on": "eval:doc.is_final_product"},
				{"fieldname": "is_raw_material", "label": "Is Raw Material", "fieldtype": "Check", "insert_after": "product_category"},
				{"fieldname": "classification", "label": "Classification (final products it serves)", "fieldtype": "Table MultiSelect", "options": "Los Andalus Item Category", "insert_after": "is_raw_material", "depends_on": "eval:doc.is_raw_material"},
			]
		},
		ignore_validate=True,
	)


def _ensure_clearing_account():
	existing = frappe.db.get_value("Account", {"company": COMPANY, "account_name": "Production Clearing"}, "name")
	if existing:
		return existing
	sa = frappe.db.get_value("Account", {"company": COMPANY, "account_type": "Stock Adjustment", "is_group": 0}, "parent_account")
	parent = sa or frappe.db.get_value("Account", {"company": COMPANY, "root_type": "Expense", "is_group": 1}, "name")
	acc = frappe.get_doc(
		{
			"doctype": "Account",
			"account_name": "Production Clearing",
			"company": COMPANY,
			"parent_account": parent,
			"root_type": "Expense",
			"account_type": "Stock Adjustment",
			"is_group": 0,
		}
	).insert(ignore_permissions=True)
	return acc.name


def _ensure_categories():
	for c in CATEGORIES:
		if not frappe.db.exists("Product Category", c):
			frappe.get_doc({"doctype": "Product Category", "category_name": c}).insert(ignore_permissions=True)


def _ensure_shifts():
	for name, start, end in SHIFTS:
		if not frappe.db.exists("Shift", name):
			frappe.get_doc({"doctype": "Shift", "shift_name": name, "start_time": start, "end_time": end}).insert(ignore_permissions=True)


def _ensure_final_products():
	for code, cat, weight, shelf in FINAL_PRODUCTS:
		if frappe.db.exists("Item", code):
			continue
		frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": code,
				"item_name": code,
				"item_group": FG_GROUP,
				"stock_uom": "Nos",
				"is_stock_item": 1,
				"is_final_product": 1,
				"product_category": cat,
				"weight_per_unit": weight,
				"weight_uom": WEIGHT_UOM,
				"has_batch_no": 1,
				"create_new_batch": 1,
				"batch_number_series": _series(code),
				"shelf_life_in_days": shelf,
			}
		).insert(ignore_permissions=True)


def _ensure_raw_materials():
	for code, uom, rate, cats in RAW_MATERIALS:
		if frappe.db.exists("Item", code):
			continue
		doc = frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": code,
				"item_name": code,
				"item_group": RM_GROUP,
				"stock_uom": uom,
				"is_stock_item": 1,
				"is_raw_material": 1,
				"include_item_in_manufacturing": 1,
				"valuation_rate": rate,
				"has_batch_no": 1,
				"create_new_batch": 1,
				"batch_number_series": _series(code),
				"shelf_life_in_days": 30,
			}
		)
		for c in cats:
			doc.append("classification", {"product_category": c})
		doc.insert(ignore_permissions=True)


def _ensure_workbenches():
	rm_wh, wip_wh, fg_wh = WAREHOUSES
	for name, cat in WORKBENCHES:
		if frappe.db.exists("Workbench", name):
			continue
		frappe.get_doc(
			{
				"doctype": "Workbench",
				"workbench_name": name,
				"product_category": cat,
				"raw_material_warehouse": rm_wh,
				"manufacturing_warehouse": wip_wh,
				"fg_warehouse": fg_wh,
				"staff": [{"user": "Administrator", "shift": "Morning"}],
			}
		).insert(ignore_permissions=True)


def _disable_legacy():
	# Old templates + their variants, and the old non-batch RM-* items.
	legacy = frappe.get_all(
		"Item",
		filters={"disabled": 0},
		or_filters={"has_variants": 1, "variant_of": ["is", "set"], "item_code": ["like", "RM-%"]},
		pluck="name",
	)
	for it in legacy:
		frappe.db.set_value("Item", it, "disabled", 1)


def run():
	_ensure_custom_fields()
	clearing = _ensure_clearing_account()
	frappe.db.set_value("Los Andalus Manufacture Settings", None, "production_clearing_account", clearing)
	_ensure_categories()
	_ensure_shifts()
	_ensure_final_products()
	_ensure_raw_materials()
	_ensure_workbenches()
	_disable_legacy()
	frappe.db.commit()
	summary = {
		"clearing_account": clearing,
		"categories": frappe.db.count("Product Category"),
		"shifts": frappe.db.count("Shift"),
		"final_products": frappe.db.count("Item", {"is_final_product": 1}),
		"raw_materials": frappe.db.count("Item", {"is_raw_material": 1}),
		"workbenches": frappe.db.count("Workbench"),
	}
	print("PHASE0_DONE", frappe.as_json(summary))
	return summary
