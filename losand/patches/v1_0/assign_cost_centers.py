"""Give every POS Profile (branch) and Workbench (production line) its own Cost Center.

Posting code books each stock/invoice row to the profile's or workbench's Cost Center
(see api/pos.py _stamp_branch, api/manufacture.py submit_batch). The records are site
data, so this creates them on any site that lacks them. Idempotent: anything that already
has a Cost Center is left alone.
"""

import frappe


def _cost_center(name, company):
	"""Leaf Cost Center named `name` under the company's root group (ERPNext adds the abbreviation)."""
	abbr = frappe.get_cached_value("Company", company, "abbr")
	full = f"{name} - {abbr}"
	if not frappe.db.exists("Cost Center", full):
		parent = frappe.db.get_value(
			"Cost Center", {"company": company, "is_group": 1, "parent_cost_center": ["in", ["", None]]}, "name"
		)
		frappe.get_doc(
			{
				"doctype": "Cost Center",
				"cost_center_name": name,
				"company": company,
				"parent_cost_center": parent,
				"is_group": 0,
			}
		).insert(ignore_permissions=True)
	return full


def execute():
	for profile in frappe.get_all("POS Profile", fields=["name", "company", "losand_branch", "cost_center"]):
		if not profile.cost_center and profile.company:
			cc = _cost_center(profile.losand_branch or profile.name, profile.company)
			frappe.db.set_value("POS Profile", profile.name, "cost_center", cc)

	company = frappe.defaults.get_global_default("company")
	if not company:
		return
	for wb in frappe.get_all("Workbench", fields=["name", "cost_center"]):
		if not wb.cost_center:
			frappe.db.set_value("Workbench", wb.name, "cost_center", _cost_center(f"إنتاج - {wb.name}", company))
