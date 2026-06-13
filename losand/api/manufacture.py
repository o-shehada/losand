from __future__ import annotations

from datetime import datetime

import frappe
from frappe import _


@frappe.whitelist()
def get_current_session():
	return {
		"user": frappe.session.user,
		"authenticated": frappe.session.user != "Guest",
		"language": frappe.local.lang or "ar",
	}


@frappe.whitelist()
def get_food_logger_defaults():
	return {
		"products": [
			{"name": "Beef Burger", "label": _("Beef Burger")},
			{"name": "Chicken Burger", "label": _("Chicken Burger")},
			{"name": "Burger Buns", "label": _("Burger Buns")},
		]
	}


RAW_MATERIAL_GROUP = "Raw Material"


@frappe.whitelist()
def get_raw_materials(search: str | None = None):
	"""Return ERPNext Items under the Raw Material group (and its sub-groups),
	mapped to the shape the Food Logger frontend expects."""
	import html

	from frappe.utils.nestedset import get_descendants_of

	groups = [RAW_MATERIAL_GROUP]
	try:
		groups += get_descendants_of("Item Group", RAW_MATERIAL_GROUP)
	except Exception:
		pass

	filters = {"item_group": ["in", groups], "disabled": 0}
	or_filters = None
	if search:
		or_filters = {"item_name": ["like", f"%{search}%"], "item_code": ["like", f"%{search}%"]}

	items = frappe.get_all(
		"Item",
		filters=filters,
		or_filters=or_filters,
		fields=[
			"item_code",
			"item_name",
			"description",
			"stock_uom",
			"valuation_rate",
			"last_purchase_rate",
			"standard_rate",
		],
		order_by="item_name asc",
		limit_page_length=200,
	)

	result = []
	for it in items:
		rate = it.get("valuation_rate") or it.get("last_purchase_rate") or it.get("standard_rate") or 0
		result.append(
			{
				"item_code": it.get("item_code"),
				"name_ar": it.get("item_name") or it.get("item_code"),
				"name_en": html.unescape(frappe.utils.strip_html(it.get("description") or "")).strip(),
				"unit": it.get("stock_uom"),
				"rate": float(rate),
			}
		)
	return result


@frappe.whitelist()
def save_food_logger_batch(draft: dict, totals: dict):
	if frappe.session.user == "Guest":
		frappe.throw(_("Login required"), frappe.PermissionError)

	produced_qty = float(draft.get("producedQty") or 0)
	if produced_qty <= 0:
		frappe.throw(_("Produced quantity must be greater than zero"))

	batch_ref = draft.get("batchRef") or f"#B-{datetime.now().strftime('%Y%m%d%H%M%S')}"
	return {
		"batchRef": batch_ref,
		"product": draft.get("product"),
		"producedQty": produced_qty,
		"totalCost": float(totals.get("totalCost") or 0),
		"unitCost": float(totals.get("unitCost") or 0),
		"savedAt": frappe.utils.now_datetime().isoformat(),
		"savedBy": frappe.session.user,
	}
