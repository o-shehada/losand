"""Move legacy raw-material category links onto their final products."""

from collections import defaultdict

import frappe


def execute():
	by_category = defaultdict(set)
	for row in frappe.get_all(
		"Los Andalus Item Category",
		filters={"parenttype": "Item", "parentfield": "classification"},
		fields=["parent", "product_category"],
	):
		if row.parent and row.product_category:
			by_category[row.product_category].add(row.parent)

	for category, raw_materials in by_category.items():
		for item_name in frappe.get_all(
			"Item",
			filters={"is_final_product": 1, "product_category": category},
			pluck="name",
		):
			item = frappe.get_doc("Item", item_name)
			existing = {row.raw_material for row in item.classification if row.raw_material}
			for raw_material in sorted(raw_materials - existing):
				item.append("classification", {"raw_material": raw_material})
			if raw_materials - existing:
				item.save(ignore_permissions=True)
