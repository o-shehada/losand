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
