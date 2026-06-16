from __future__ import annotations

import frappe
from frappe import _

# Defaults used only as fallbacks when the Settings single is empty.
DEFAULT_COMPANY = "Los Andalus"
DEFAULT_SOURCE_WAREHOUSE = "Stores - LA"
DEFAULT_WIP_WAREHOUSE = "Work In Progress - LA"
DEFAULT_FG_WAREHOUSE = "Finished Goods - LA"
DEFAULT_RAW_MATERIAL_GROUP = "Raw Material"
DEFAULT_FACTORY_NAME = "مصنع الغذاء الحديث"


def cfg():
	"""Resolved config from the Settings single, with safe fallbacks. Warehouses now come
	from the Workbench; the settings warehouses are only fallbacks."""
	s = frappe.get_cached_doc("Los Andalus Manufacture Settings")
	company = s.company or frappe.defaults.get_global_default("company") or DEFAULT_COMPANY
	return frappe._dict(
		company=company,
		source=s.source_warehouse or DEFAULT_SOURCE_WAREHOUSE,
		wip=s.wip_warehouse or DEFAULT_WIP_WAREHOUSE,
		fg=s.fg_warehouse or DEFAULT_FG_WAREHOUSE,
		raw_group=s.raw_material_group or DEFAULT_RAW_MATERIAL_GROUP,
		factory_name=s.factory_name or DEFAULT_FACTORY_NAME,
		clearing=s.production_clearing_account,
	)


# Roles allowed to POST production (create stock). Operators below may only draft/enter.
PRODUCE_ROLES = {"System Manager", "Manufacturing Manager", "Manufacture Supervisor"}
ENTER_ROLES = PRODUCE_ROLES | {"Manufacturing User", "Manufacture Operator", "Stock User"}


def _roles():
	return set(frappe.get_roles())


def can_produce():
	return bool(_roles() & PRODUCE_ROLES)


def can_enter():
	return bool(_roles() & ENTER_ROLES)


@frappe.whitelist()
def get_current_session():
	return {
		"user": frappe.session.user,
		"authenticated": frappe.session.user != "Guest",
		"language": frappe.local.lang or "ar",
		"can_produce": can_produce(),
		"can_enter": can_enter(),
	}


def _stock_map(codes, warehouse):
	qty_map = {}
	if codes:
		for b in frappe.get_all(
			"Bin",
			filters={"item_code": ["in", codes], "warehouse": warehouse},
			fields=["item_code", "actual_qty"],
		):
			qty_map[b.item_code] = qty_map.get(b.item_code, 0) + (b.actual_qty or 0)
	return qty_map


# ---------------------------------------------------------------------------
# Phase 1 — read APIs
# ---------------------------------------------------------------------------
@frappe.whitelist()
def get_workbenches():
	"""Enabled workbenches the user can produce at: category + 3 warehouses + shifts."""
	result = []
	for w in frappe.get_all("Workbench", filters={"disabled": 0}, order_by="workbench_name", pluck="name"):
		wb = frappe.get_cached_doc("Workbench", w)
		shifts = sorted({r.shift for r in wb.staff if r.shift} | {r.shift for r in wb.workers if r.shift})
		if not shifts:
			shifts = frappe.get_all("Shift", pluck="name")
		result.append(
			{
				"name": wb.name,
				"category": wb.product_category,
				"raw_warehouse": wb.raw_material_warehouse,
				"mfg_warehouse": wb.manufacturing_warehouse,
				"fg_warehouse": wb.fg_warehouse,
				"shifts": shifts,
			}
		)
	return result


@frappe.whitelist()
def get_final_products(category):
	"""Independent final-product items for a category (per weight)."""
	items = frappe.get_all(
		"Item",
		filters={"is_final_product": 1, "product_category": category, "disabled": 0},
		fields=["item_code", "item_name", "weight_per_unit", "weight_uom", "image", "valuation_rate"],
		order_by="weight_per_unit asc",
	)
	return [
		{
			"item_code": i.item_code,
			"name": i.item_name,
			"weight": float(i.weight_per_unit or 0),
			"weight_uom": i.weight_uom,
			"image": i.image,
			"rate": float(i.valuation_rate or 0),
		}
		for i in items
	]


@frappe.whitelist()
def get_category_raw_materials(category, warehouse=None):
	"""Raw materials whose classification includes the category, with valuation + stock."""
	import html

	warehouse = warehouse or cfg().source
	items = frappe.get_all(
		"Item",
		filters=[
			["is_raw_material", "=", 1],
			["disabled", "=", 0],
			["Los Andalus Item Category", "product_category", "=", category],
		],
		fields=["item_code", "item_name", "description", "stock_uom", "valuation_rate"],
		order_by="item_name asc",
	)
	codes = [i.item_code for i in items]
	qty_map = _stock_map(codes, warehouse)
	return [
		{
			"item_code": i.item_code,
			"name_ar": i.item_name,
			"name_en": html.unescape(frappe.utils.strip_html(i.description or "")).strip(),
			"unit": i.stock_uom,
			"rate": float(i.valuation_rate or 0),
			"available_qty": float(qty_map.get(i.item_code, 0)),
		}
		for i in items
	]


# ---------------------------------------------------------------------------
# Batch persistence (draft). Real stock posting is Phase 2 (submit_batch).
# ---------------------------------------------------------------------------
def _compute_and_fill(batch, payload):
	"""Fill outputs/materials/losses child tables + compute C, W, and weight-allocated cost."""
	# Raw materials consumed → C
	total_raw_cost = 0.0
	batch.set("materials", [])
	for m in payload.get("raw_materials") or []:
		code = m.get("item_code")
		qty = float(m.get("qty") if m.get("qty") is not None else m.get("actual") or 0)
		if not code or qty <= 0:
			continue
		info = frappe.db.get_value("Item", code, ["item_name", "stock_uom", "valuation_rate"], as_dict=True) or {}
		rate = float(m.get("rate") if m.get("rate") is not None else info.get("valuation_rate") or 0)
		amount = qty * rate
		total_raw_cost += amount
		batch.append("materials", {"item_code": code, "item_name": info.get("item_name"), "unit": info.get("stock_uom"), "qty": qty, "rate": rate, "amount": amount})

	# Finished products → total output weight W
	outputs = []
	total_weight = 0.0
	for f in payload.get("finished_products") or []:
		code = f.get("item_code")
		qty = float(f.get("qty") or 0)
		if not code or qty <= 0:
			continue
		info = frappe.db.get_value("Item", code, ["item_name", "weight_per_unit"], as_dict=True) or {}
		weight = float(f.get("weight") if f.get("weight") is not None else info.get("weight_per_unit") or 0)
		total_weight += qty * weight
		outputs.append((code, info.get("item_name"), qty, weight))

	cost_per_g = (total_raw_cost / total_weight) if total_weight else 0.0
	batch.set("outputs", [])
	for code, name, qty, weight in outputs:
		unit_cost = weight * cost_per_g
		batch.append("outputs", {"item_code": code, "item_name": name, "qty": qty, "weight_per_unit": weight, "unit_cost": unit_cost, "amount": unit_cost * qty})

	# Loss (recorded only)
	batch.set("losses", [])
	for l in payload.get("losses") or []:
		q = float(l.get("qty") or 0)
		if q <= 0 and not l.get("reason"):
			continue
		batch.append("losses", {"reason": l.get("reason"), "qty": q, "unit": l.get("unit") or "كجم", "rate": cost_per_g * 1000, "amount": q * 1000 * cost_per_g})

	batch.total_raw_cost = total_raw_cost
	batch.total_output_weight = total_weight


@frappe.whitelist()
def save_draft(payload):
	"""Create/update a Draft Production Batch (no stock movement)."""
	import json

	if isinstance(payload, str):
		payload = json.loads(payload)
	if frappe.session.user == "Guest":
		frappe.throw(_("Login required"), frappe.PermissionError)
	if not can_enter():
		frappe.throw(_("You do not have permission to enter production data."), frappe.PermissionError)

	wb_name = payload.get("workbench")
	if not wb_name:
		frappe.throw(_("Select a workbench first"))
	wb = frappe.get_cached_doc("Workbench", wb_name)

	name = payload.get("batchName")
	batch = (
		frappe.get_doc("Los Andalus Production Batch", name)
		if name and frappe.db.exists("Los Andalus Production Batch", name)
		else frappe.new_doc("Los Andalus Production Batch")
	)
	batch.update(
		{
			"workbench": wb.name,
			"product_category": wb.product_category,
			"shift": payload.get("shift"),
			"raw_material_warehouse": wb.raw_material_warehouse,
			"manufacturing_warehouse": wb.manufacturing_warehouse,
			"fg_warehouse": wb.fg_warehouse,
			"batch_reference": payload.get("batchRef"),
			"operator": frappe.session.user,
			"status": "Draft",
			"notes": payload.get("notes"),
		}
	)
	_compute_and_fill(batch, payload)
	batch.save(ignore_permissions=True)
	frappe.db.commit()
	return {
		"batchName": batch.name,
		"status": batch.status,
		"totalRawCost": batch.total_raw_cost,
		"totalOutputWeight": batch.total_output_weight,
	}


@frappe.whitelist()
def submit_batch(payload, totals=None):
	"""Phase 2: posts Material Transfer → Issue → Receipt (FEFO, weight cost). Not yet implemented."""
	frappe.throw(_("Production posting is implemented in Phase 2 (Transfer → Issue → Receipt)."))
