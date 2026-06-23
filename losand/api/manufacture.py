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
	"""Per item+warehouse {qty, rate} from Bin. rate = warehouse moving-avg valuation
	(set by each Material Receipt into that warehouse), NOT the company-wide Item.valuation_rate."""
	out = {}
	if codes:
		for b in frappe.get_all(
			"Bin",
			filters={"item_code": ["in", codes], "warehouse": warehouse},
			fields=["item_code", "actual_qty", "valuation_rate"],
		):
			e = out.setdefault(b.item_code, {"qty": 0.0, "rate": 0.0})
			e["qty"] += b.actual_qty or 0
			if b.valuation_rate:
				e["rate"] = float(b.valuation_rate)
	return out


def _last_receipt_rate(code, warehouse):
	"""Rate of the LAST stock receipt of an item into a warehouse (latest purchase price),
	NOT the moving-average. Reads the most recent incoming Stock Ledger Entry. Falls back to
	the Bin moving-avg valuation, then None. NOTE: this is a DISPLAY/preview rate — the actual
	consumption posted by submit_batch is still valued at moving-avg by ERPNext's ledger."""
	if not (code and warehouse):
		return None
	rows = frappe.get_all(
		"Stock Ledger Entry",
		filters={"item_code": code, "warehouse": warehouse, "actual_qty": [">", 0], "is_cancelled": 0},
		fields=["incoming_rate"],
		order_by="posting_date desc, posting_time desc, creation desc",
		limit=1,
	)
	if rows and rows[0].incoming_rate:
		return float(rows[0].incoming_rate)
	r = frappe.db.get_value("Bin", {"item_code": code, "warehouse": warehouse}, "valuation_rate")
	return float(r) if r else None


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
	"""Raw materials declared on the final products of the category, with valuation + stock."""
	import html

	warehouse = warehouse or cfg().source
	# union of raw materials listed in `classification` across all final products in the category
	rm_codes = frappe.get_all(
		"Los Andalus Item Raw Material",
		filters={
			"parenttype": "Item",
			"parentfield": "classification",
			"parent": ["in", frappe.get_all("Item", {"is_final_product": 1, "product_category": category, "disabled": 0}, pluck="name")],
		},
		pluck="raw_material",
		distinct=True,
	)
	items = frappe.get_all(
		"Item",
		filters=[
			["item_code", "in", rm_codes],
			["disabled", "=", 0],
		],
		fields=["item_code", "item_name", "description", "stock_uom", "valuation_rate"],
		order_by="item_name asc",
	) if rm_codes else []
	codes = [i.item_code for i in items]
	bin_map = _stock_map(codes, warehouse)
	return [
		{
			"item_code": i.item_code,
			"name_ar": i.item_name,
			"name_en": html.unescape(frappe.utils.strip_html(i.description or "")).strip(),
			"unit": i.stock_uom,
			# last receipt rate into the warehouse, fall back to item master rate
			"rate": float(_last_receipt_rate(i.item_code, warehouse) or i.valuation_rate or 0),
			"available_qty": float(bin_map.get(i.item_code, {}).get("qty") or 0),
		}
		for i in items
	]


# ---------------------------------------------------------------------------
# Batch persistence (draft). Real stock posting is Phase 2 (submit_batch).
# ---------------------------------------------------------------------------
def _compute_and_fill(batch, payload):
	"""Fill outputs/materials/losses child tables + compute C, W, and weight-allocated cost."""
	raw_wh = batch.raw_material_warehouse
	# Raw materials consumed → C
	total_raw_cost = 0.0
	batch.set("materials", [])
	for m in payload.get("raw_materials") or []:
		code = m.get("item_code")
		qty = float(m.get("qty") if m.get("qty") is not None else m.get("actual") or 0)
		if not code or qty <= 0:
			continue
		info = frappe.db.get_value("Item", code, ["item_name", "stock_uom", "valuation_rate"], as_dict=True) or {}
		# last receipt rate into the warehouse (preview); client rate / item master are fallbacks
		rate = _last_receipt_rate(code, raw_wh)
		if rate is None:
			rate = float(m.get("rate") if m.get("rate") is not None else info.get("valuation_rate") or 0)
		amount = qty * rate
		total_raw_cost += amount
		batch.append("materials", {"item_code": code, "item_name": info.get("item_name"), "unit": info.get("stock_uom"), "qty": qty, "rate": rate, "amount": amount})

	# Raw material loss (الفاقد) → also part of C, but stored separately for analysis.
	batch.set("losses", [])
	for l in payload.get("losses") or []:
		code = l.get("item_code")
		qty = float(l.get("qty") or 0)
		if not code or qty <= 0:
			continue
		info = frappe.db.get_value("Item", code, ["item_name", "stock_uom", "valuation_rate"], as_dict=True) or {}
		rate = _last_receipt_rate(code, raw_wh)
		if rate is None:
			rate = float(l.get("rate") if l.get("rate") is not None else info.get("valuation_rate") or 0)
		amount = qty * rate
		total_raw_cost += amount
		batch.append(
			"losses",
			{
				"item_code": code,
				"item_name": info.get("item_name"),
				"qty": qty,
				"unit": info.get("stock_uom") or l.get("unit"),
				"rate": rate,
				"amount": amount,
				"reason": l.get("reason"),
			},
		)

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

	batch.total_raw_cost = total_raw_cost
	batch.total_output_weight = total_weight
	batch.total_produced_qty = sum(float(f.get("qty") or 0) for f in payload.get("finished_products") or [])


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


def _fefo_rows(item_code, warehouse, qty):
	"""Allocate qty across available batches in a warehouse, earliest expiry first."""
	from erpnext.stock.doctype.batch.batch import get_batch_qty

	batches = frappe.get_all(
		"Batch",
		filters={"item": item_code, "disabled": 0},
		fields=["name"],
		order_by="ifnull(expiry_date, '2999-12-31') asc, creation asc",
	)
	rows = []
	remaining = frappe.utils.flt(qty)
	for b in batches:
		if remaining <= 0:
			break
		avail = frappe.utils.flt(get_batch_qty(b.name, warehouse) or 0)
		if avail <= 0:
			continue
		take = min(remaining, avail)
		rows.append((b.name, take))
		remaining -= take
	if remaining > 1e-6:
		frappe.throw(_("Not enough batch stock of {0} in {1} (short {2}).").format(item_code, warehouse, remaining))
	return rows


def _material_issue_rows(batch):
	"""Combine consumed raw materials and same-item loss rows for one stock deduction."""
	combined = {}
	for row in list(batch.materials or []) + list(batch.losses or []):
		qty = frappe.utils.flt(row.qty)
		if not row.item_code or qty <= 0:
			continue
		if row.item_code not in combined:
			combined[row.item_code] = frappe._dict(item_code=row.item_code, qty=0)
		combined[row.item_code].qty += qty
	return list(combined.values())


@frappe.whitelist()
def submit_batch(payload, totals=None):
	"""Post the production cycle: Material Transfer (raw→WIP) → Material Issue (consume, FEFO)
	→ Material Receipt (finished goods at weight-allocated cost). Ties everything to a
	Los Andalus Production Batch. Issue + Receipt share the clearing account so the GL nets to zero."""
	import json

	from frappe.utils import flt

	if isinstance(payload, str):
		payload = json.loads(payload)
	if frappe.session.user == "Guest":
		frappe.throw(_("Login required"), frappe.PermissionError)
	if not can_produce():
		frappe.throw(_("You do not have permission to produce (Manufacture Supervisor role required)."), frappe.PermissionError)

	wb_name = payload.get("workbench")
	if not wb_name:
		frappe.throw(_("Select a workbench first"))
	wb = frappe.get_cached_doc("Workbench", wb_name)
	c = cfg()
	clearing = c.clearing or frappe.db.get_value("Account", {"company": c.company, "account_type": "Stock Adjustment", "is_group": 0}, "name")
	rm_wh, wip_wh, fg_wh = wb.raw_material_warehouse, wb.manufacturing_warehouse, wb.fg_warehouse

	# Build the batch (Draft) with computed children
	batch = frappe.new_doc("Los Andalus Production Batch")
	batch.update(
		{
			"workbench": wb.name,
			"product_category": wb.product_category,
			"shift": payload.get("shift"),
			"raw_material_warehouse": rm_wh,
			"manufacturing_warehouse": wip_wh,
			"fg_warehouse": fg_wh,
			"batch_reference": payload.get("batchRef"),
			"operator": frappe.session.user,
			"status": "Draft",
			"notes": payload.get("notes"),
		}
	)
	_compute_and_fill(batch, payload)
	if not batch.materials:
		frappe.throw(_("Enter at least one raw material consumed"))
	if not batch.outputs:
		frappe.throw(_("Enter at least one finished product"))
	batch.insert(ignore_permissions=True)
	material_issue_rows = _material_issue_rows(batch)

	def _make(ste_type, from_wh=None, to_wh=None):
		se = frappe.new_doc("Stock Entry")
		se.stock_entry_type = ste_type
		se.company = c.company
		se.custom_production_batch = batch.name
		se.custom_workbench = wb.name
		if from_wh:
			se.from_warehouse = from_wh
		if to_wh:
			se.to_warehouse = to_wh
		return se

	try:
		# 1) Material Transfer raw → WIP (FEFO from raw warehouse)
		transfer = _make("Material Transfer", rm_wh, wip_wh)
		for m in material_issue_rows:
			for batch_no, q in _fefo_rows(m.item_code, rm_wh, m.qty):
				transfer.append("items", {"item_code": m.item_code, "qty": q, "s_warehouse": rm_wh, "t_warehouse": wip_wh, "use_serial_batch_fields": 1, "batch_no": batch_no})
		transfer.insert(ignore_permissions=True)
		transfer.submit()
		batch.db_set("transfer_entry", transfer.name)
		batch.db_set("status", "Transferred")

		# 2) Material Issue from WIP (FEFO) — value = C
		issue = _make("Material Issue", wip_wh, None)
		for m in material_issue_rows:
			for batch_no, q in _fefo_rows(m.item_code, wip_wh, m.qty):
				issue.append("items", {"item_code": m.item_code, "qty": q, "s_warehouse": wip_wh, "use_serial_batch_fields": 1, "batch_no": batch_no, "expense_account": clearing})
		issue.insert(ignore_permissions=True)
		issue.submit()
		issue.reload()
		c_actual = sum(flt(i.amount) for i in issue.items)
		batch.db_set("issue_entry", issue.name)
		batch.db_set("status", "Issued")

		# 3) Material Receipt finished goods at weight-allocated cost (auto-create FG batches)
		total_weight = flt(batch.total_output_weight) or 1
		cost_per_g = c_actual / total_weight
		receipt = _make("Material Receipt", None, fg_wh)
		for o in batch.outputs:
			receipt.append("items", {"item_code": o.item_code, "qty": o.qty, "t_warehouse": fg_wh, "basic_rate": flt(o.weight_per_unit) * cost_per_g, "use_serial_batch_fields": 1, "expense_account": clearing})
		receipt.insert(ignore_permissions=True)
		receipt.submit()
		receipt.reload()
		batch.db_set("receipt_entry", receipt.name)

		# Write back ERPNext-actual cost + FG batch numbers
		batch.db_set("total_raw_cost", c_actual)
		fg_batch = {}
		for o in batch.outputs:
			bn = frappe.get_all("Batch", filters={"item": o.item_code}, order_by="creation desc", limit=1, pluck="name")
			fg_batch[o.item_code] = bn[0] if bn else None
		for o in batch.outputs:
			unit_cost = flt(o.weight_per_unit) * cost_per_g
			o.db_set("unit_cost", unit_cost)
			o.db_set("amount", unit_cost * flt(o.qty))
			o.db_set("batch_no", fg_batch.get(o.item_code))
		batch.db_set("status", "Completed")
		frappe.db.commit()
	except Exception:
		batch.db_set("status", "Failed")
		batch.db_set("error_log", frappe.get_traceback())
		frappe.db.commit()
		raise

	return {
		"batchName": batch.name,
		"status": batch.status,
		"transferEntry": batch.transfer_entry,
		"issueEntry": batch.issue_entry,
		"receiptEntry": batch.receipt_entry,
		"totalRawCost": batch.total_raw_cost,
		"totalOutputWeight": batch.total_output_weight,
		"draft": payload,
	}
