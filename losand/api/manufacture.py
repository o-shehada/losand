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

	# Available stock per item, summed across all warehouses.
	codes = [it.get("item_code") for it in items]
	qty_map = {}
	if codes:
		for b in frappe.get_all(
			"Bin", filters={"item_code": ["in", codes]}, fields=["item_code", "actual_qty"]
		):
			qty_map[b.item_code] = qty_map.get(b.item_code, 0) + (b.actual_qty or 0)

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
				"available_qty": float(qty_map.get(it.get("item_code"), 0)),
			}
		)
	return result


def _stock_map(codes):
	qty_map = {}
	if codes:
		for b in frappe.get_all(
			"Bin", filters={"item_code": ["in", codes]}, fields=["item_code", "actual_qty"]
		):
			qty_map[b.item_code] = qty_map.get(b.item_code, 0) + (b.actual_qty or 0)
	return qty_map


@frappe.whitelist()
def get_allowed_products():
	"""Final-product templates the user may produce, each with its weight variants
	and the flagged default variant. (Role filtering comes in Phase 2.)"""
	templates = frappe.get_all(
		"Item", filters={"has_variants": 1, "disabled": 0}, fields=["item_code", "item_name", "image"]
	)
	result = []
	for t in templates:
		variants = frappe.get_all(
			"Item",
			filters={"variant_of": t.item_code, "disabled": 0},
			fields=["item_code", "weight_per_unit", "custom_is_default_variant"],
			order_by="weight_per_unit asc",
		)
		if not variants:
			continue
		default = next((v for v in variants if v.custom_is_default_variant), variants[0])
		result.append(
			{
				"code": t.item_code,
				"name_ar": t.item_name,
				"name_en": t.item_code,
				"image": t.image,
				"default_variant": default.item_code,
				"default_weight": default.weight_per_unit,
				"variants": [
					{
						"variant": v.item_code,
						"weight": v.weight_per_unit,
						"label": f"{int(v.weight_per_unit or 0)} جم",
					}
					for v in variants
				],
			}
		)
	return result


@frappe.whitelist()
def get_variant_bom(variant: str):
	"""Planned per-piece materials for a product variant, from its default BOM,
	enriched with current unit cost and available stock."""
	import html

	weight = frappe.db.get_value("Item", variant, "weight_per_unit")
	bom_name = frappe.db.get_value("Item", variant, "default_bom") or frappe.db.get_value(
		"BOM", {"item": variant, "is_active": 1, "is_default": 1}, "name"
	)

	materials = []
	if bom_name:
		bom = frappe.get_doc("BOM", bom_name)
		base = bom.quantity or 1
		codes = [d.item_code for d in bom.items]
		details = {
			d.name: d
			for d in frappe.get_all(
				"Item",
				filters={"item_code": ["in", codes]},
				fields=["item_code as name", "item_name", "description", "stock_uom", "valuation_rate"],
			)
		}
		qty_map = _stock_map(codes)
		for d in bom.items:
			info = details.get(d.item_code, frappe._dict())
			materials.append(
				{
					"item_code": d.item_code,
					"name_ar": info.get("item_name") or d.item_code,
					"name_en": html.unescape(frappe.utils.strip_html(info.get("description") or "")).strip(),
					"unit": d.uom or info.get("stock_uom"),
					"per_piece": (d.qty or 0) / base,
					"rate": float(info.get("valuation_rate") or d.rate or 0),
					"available_qty": float(qty_map.get(d.item_code, 0)),
				}
			)

	return {"variant": variant, "weight": weight, "bom": bom_name, "materials": materials}


COMPANY = "Los Andalus"
SOURCE_WAREHOUSE = "Stores - LA"
WIP_WAREHOUSE = "Work In Progress - LA"
FG_WAREHOUSE = "Finished Goods - LA"


@frappe.whitelist()
def submit_batch(draft, totals=None):
	"""Phase-2: turn a Food Logger draft into real ERPNext production documents.

	Creates (and submits): Work Order -> Material Transfer for Manufacture (actual qty)
	-> Manufacture Stock Entry, all tied together by a Los Andalus Production Batch log.
	Returns the batch confirmation with ERPNext's authoritative per-piece cost.
	"""
	import json

	from erpnext.manufacturing.doctype.work_order.work_order import make_stock_entry

	if isinstance(draft, str):
		draft = json.loads(draft)
	if isinstance(totals, str):
		totals = json.loads(totals or "{}")

	if frappe.session.user == "Guest":
		frappe.throw(_("Login required"), frappe.PermissionError)

	variant = draft.get("variant")
	qty = float(draft.get("producedQty") or 0)
	materials = draft.get("materials") or []

	if not variant:
		frappe.throw(_("Select a product variant first"))
	if qty <= 0:
		frappe.throw(_("Produced quantity must be greater than zero"))

	bom_no = frappe.db.get_value("Item", variant, "default_bom")
	if not bom_no:
		frappe.throw(_("No active BOM found for {0}").format(variant))

	# Stock guard (defence in depth; UI also blocks this)
	for m in materials:
		actual = float(m.get("actual") or 0)
		if actual <= 0:
			continue
		on_hand = frappe.db.get_value("Bin", {"item_code": m.get("item_code"), "warehouse": SOURCE_WAREHOUSE}, "actual_qty") or 0
		if actual > on_hand:
			frappe.throw(
				_("Not enough stock of {0}: need {1}, available {2}").format(m.get("name_ar") or m.get("item_code"), actual, on_hand)
			)

	batch = frappe.new_doc("Los Andalus Production Batch")
	batch.update(
		{
			"product": draft.get("product"),
			"product_name": draft.get("productName"),
			"variant": variant,
			"bom": bom_no,
			"batch_reference": draft.get("batchRef"),
			"produced_qty": qty,
			"weight": draft.get("weight") or 0,
			"source_warehouse": SOURCE_WAREHOUSE,
			"wip_warehouse": WIP_WAREHOUSE,
			"target_warehouse": FG_WAREHOUSE,
			"operator": frappe.session.user,
			"status": "Draft",
			"materials_json": json.dumps(materials, ensure_ascii=False),
			"waste_json": json.dumps(draft.get("waste") or [], ensure_ascii=False),
			"loss_json": json.dumps(draft.get("loss") or [], ensure_ascii=False),
			"notes": draft.get("notes"),
		}
	)
	batch.insert(ignore_permissions=True)

	try:
		# 1) Work Order
		wo = frappe.new_doc("Work Order")
		wo.update(
			{
				"production_item": variant,
				"bom_no": bom_no,
				"qty": qty,
				"company": COMPANY,
				"source_warehouse": SOURCE_WAREHOUSE,
				"wip_warehouse": WIP_WAREHOUSE,
				"fg_warehouse": FG_WAREHOUSE,
			}
		)
		wo.insert(ignore_permissions=True)
		wo.submit()
		batch.db_set("work_order", wo.name)
		batch.db_set("status", "WO Created")

		# 2) Material Transfer for Manufacture, overridden with ACTUAL consumption
		actual_map = {m.get("item_code"): float(m.get("actual") or 0) for m in materials}
		transfer = frappe.get_doc(make_stock_entry(wo.name, "Material Transfer for Manufacture", qty))
		kept = []
		for it in transfer.items:
			a = actual_map.get(it.item_code)
			if a is None or a <= 0:
				continue
			it.qty = a
			kept.append(it)
		transfer.items = kept
		bom_codes = {it.item_code for it in transfer.items}
		for code, a in actual_map.items():
			if a > 0 and code not in bom_codes:
				transfer.append("items", {"item_code": code, "qty": a, "s_warehouse": SOURCE_WAREHOUSE, "t_warehouse": WIP_WAREHOUSE})
		transfer.insert(ignore_permissions=True)
		transfer.submit()
		batch.db_set("material_transfer_entry", transfer.name)
		batch.db_set("status", "Materials Transferred")

		# 3) Manufacture (consumes transferred from WIP, receives FG; ERPNext costs it)
		manufacture = frappe.get_doc(make_stock_entry(wo.name, "Manufacture", qty))
		manufacture.insert(ignore_permissions=True)
		manufacture.submit()
		batch.db_set("manufacture_entry", manufacture.name)

		# ERPNext-computed finished-good valuation = authoritative per-piece cost
		unit_cost = 0.0
		for it in manufacture.items:
			if it.is_finished_item or (it.t_warehouse and it.item_code == variant):
				unit_cost = float(it.valuation_rate or 0)
				break
		total_cost = unit_cost * qty
		batch.db_set("unit_cost", unit_cost)
		batch.db_set("total_cost", total_cost)
		batch.db_set("status", "Completed")
		frappe.db.commit()
	except Exception:
		batch.db_set("status", "Failed")
		batch.db_set("error_log", frappe.get_traceback())
		frappe.db.commit()
		raise

	return {
		"batchName": batch.name,
		"batchRef": draft.get("batchRef"),
		"product": draft.get("product"),
		"productName": draft.get("productName"),
		"variant": variant,
		"weight": draft.get("weight"),
		"producedQty": qty,
		"workOrder": batch.work_order,
		"manufactureEntry": batch.manufacture_entry,
		"unitCost": batch.unit_cost,
		"totalCost": batch.total_cost,
		"savedBy": frappe.session.user,
		"savedAt": frappe.utils.now_datetime().isoformat(),
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
		"productName": draft.get("productName"),
		"variant": draft.get("variant"),
		"weight": draft.get("weight"),
		"producedQty": produced_qty,
		"totalCost": float(totals.get("totalCost") or 0),
		"unitCost": float(totals.get("unitCost") or 0),
		"savedAt": frappe.utils.now_datetime().isoformat(),
		"savedBy": frappe.session.user,
	}
