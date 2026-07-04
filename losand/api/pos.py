from __future__ import annotations

import json

import frappe
from frappe import _
from frappe.utils import flt

from losand.api.manufacture import _last_receipt_rate, _stock_map, _stock_rows, cfg

# Phase 0 of wiring the losand POS portal to ERPNext. Reads only — real items,
# prices, and stock for the register. Config comes from the stock ERPNext
# POS Profile (no custom doctype). Invoicing arrives in Phase 1 the posawesome
# way (server-side Sales Invoice submit).


def _require_login():
	if frappe.session.user == "Guest":
		frappe.throw(_("Login required"), frappe.PermissionError)


def _resolve_pos_profile(name=None):
	"""Pick the POS Profile: explicit arg → one the user is applicable for →
	first enabled for the default company."""
	if name and frappe.db.exists("POS Profile", name):
		return frappe.get_cached_doc("POS Profile", name)

	linked = frappe.get_all(
		"POS Profile User",
		filters={"user": frappe.session.user, "parenttype": "POS Profile"},
		pluck="parent",
	)
	for p in linked:
		if not frappe.db.get_value("POS Profile", p, "disabled"):
			return frappe.get_cached_doc("POS Profile", p)

	filters = {"disabled": 0}
	company = frappe.defaults.get_global_default("company")
	if company:
		filters["company"] = company
	first = frappe.get_all("POS Profile", filters=filters, limit=1, pluck="name")
	if first:
		return frappe.get_cached_doc("POS Profile", first[0])

	frappe.throw(_("No POS Profile is configured. Create one in ERPNext first."))


@frappe.whitelist()
def get_pos_config(pos_profile=None):
	"""POS Profile config the register needs: warehouse, price list, currency,
	payment methods, default customer. Nothing hardcoded — all from the profile."""
	_require_login()
	p = _resolve_pos_profile(pos_profile)
	symbol = frappe.db.get_value("Currency", p.currency, "symbol") or p.currency
	return {
		"pos_profile": p.name,
		"company": p.company,
		"warehouse": p.warehouse,
		"currency": p.currency,
		"currency_symbol": symbol,
		"price_list": p.selling_price_list,
		"customer": p.customer,
		"payments": [
			{"mode_of_payment": r.mode_of_payment, "default": bool(r.default)}
			for r in p.payments
		],
		"item_groups": [r.item_group for r in (p.item_groups or [])],
	}


@frappe.whitelist()
def get_products(pos_profile=None, item_group=None, search=None):
	"""Sellable items for the register, with price (POS Profile price list) and
	stock (POS Profile warehouse). Categories = the profile's item groups, or the
	groups present when the profile does not restrict them."""
	_require_login()
	p = _resolve_pos_profile(pos_profile)
	price_list = p.selling_price_list
	warehouse = p.warehouse
	allowed_groups = [r.item_group for r in (p.item_groups or [])]

	filters = [["disabled", "=", 0], ["is_sales_item", "=", 1]]
	if item_group and item_group != "all":
		filters.append(["item_group", "=", item_group])
	elif allowed_groups:
		filters.append(["item_group", "in", allowed_groups])
	if search:
		filters.append(["item_name", "like", f"%{search}%"])

	items = frappe.get_all(
		"Item",
		filters=filters,
		fields=["item_code", "item_name", "item_group", "image", "stock_uom"],
		order_by="item_name asc",
	)
	codes = [i.item_code for i in items]

	price_map = {}
	if codes and price_list:
		for pr in frappe.get_all(
			"Item Price",
			filters={"price_list": price_list, "selling": 1, "item_code": ["in", codes]},
			fields=["item_code", "price_list_rate"],
		):
			price_map.setdefault(pr.item_code, pr.price_list_rate)

	stock = _stock_map(codes, warehouse) if warehouse else {}

	products = [
		{
			"id": i.item_code,
			"name": i.item_name,
			"category": i.item_group,
			"price": float(price_map.get(i.item_code) or 0),
			"img": i.image,
			"uom": i.stock_uom,
			"available_qty": float(stock.get(i.item_code, {}).get("qty") or 0),
		}
		for i in items
	]

	groups = allowed_groups or sorted({i.item_group for i in items})
	categories = [{"key": g, "label": g} for g in groups]
	return {"categories": categories, "products": products}


# ---------------------------------------------------------------------------
# Phase 1 — POS shift gate + order submission (server-side Sales Invoice)
# ---------------------------------------------------------------------------
def _open_shift():
	"""The current user's open POS Opening Entry (native ERPNext) that has not been
	closed by a Los Andalus POS Closing, or None."""
	rows = frappe.get_all(
		"POS Opening Entry",
		filters={"user": frappe.session.user, "pos_closing_entry": ["in", ["", None]], "docstatus": 1},
		fields=["name", "company", "pos_profile", "period_start_date"],
		order_by="period_start_date desc",
	)
	for r in rows:
		if not frappe.db.exists("Los Andalus POS Closing", {"opening_entry": r.name}):
			return r
	return None


ADDON_GROUP = "POS Add-ons"  # business-data Item Group — whatever Items live here are the paid add-ons


@frappe.whitelist()
def get_extras(pos_profile=None):
	"""Paid add-on items (extra cheese, bacon…) = real Items in the add-on group,
	priced from the profile price list. Empty if the group/items are not set up —
	the register then keeps add-on checkout blocked rather than guessing a price."""
	_require_login()
	if not frappe.db.exists("Item Group", ADDON_GROUP):
		return []
	p = _resolve_pos_profile(pos_profile)
	items = frappe.get_all(
		"Item",
		filters={"item_group": ADDON_GROUP, "disabled": 0, "is_sales_item": 1},
		fields=["item_code", "item_name"],
		order_by="item_name asc",
	)
	codes = [i.item_code for i in items]
	price_map = {}
	if codes and p.selling_price_list:
		for pr in frappe.get_all(
			"Item Price",
			filters={"price_list": p.selling_price_list, "selling": 1, "item_code": ["in", codes]},
			fields=["item_code", "price_list_rate"],
		):
			price_map.setdefault(pr.item_code, pr.price_list_rate)
	return [
		{"id": i.item_code, "item_code": i.item_code, "name": i.item_name, "price": float(price_map.get(i.item_code) or 0)}
		for i in items
	]


GIFT_MODE = "Gift Card"  # Mode of Payment used to tender a redeemed gift card


@frappe.whitelist()
def check_gift_card(code):
	"""Look up a gift card by its code — returns its redeemable balance, or errors."""
	_require_login()
	gc = frappe.db.get_value(
		"Los Andalus Gift Card", {"card_no": code, "is_active": 1}, ["card_no", "balance"], as_dict=True
	)
	if not gc:
		frappe.throw(_("Invalid or inactive gift card."))
	return {"card_no": gc.card_no, "balance": float(gc.balance or 0)}


def _ensure_gift_mode(company):
	"""Ensure a 'Gift Card' Mode of Payment exists, backed by a liability account for
	the company (redemption debits the prepaid gift-card liability)."""
	abbr = frappe.db.get_value("Company", company, "abbr")
	acc_name = f"Gift Card Liability - {abbr}"
	if not frappe.db.exists("Account", acc_name):
		parent = frappe.db.get_value(
			"Account", {"company": company, "account_name": "Current Liabilities", "is_group": 1}, "name"
		) or frappe.db.get_value("Account", {"company": company, "root_type": "Liability", "is_group": 1}, "name")
		frappe.get_doc(
			{
				"doctype": "Account",
				"account_name": "Gift Card Liability",
				"company": company,
				"parent_account": parent,
				"root_type": "Liability",
				"is_group": 0,
			}
		).insert(ignore_permissions=True)
	if not frappe.db.exists("Mode of Payment", GIFT_MODE):
		frappe.get_doc(
			{
				"doctype": "Mode of Payment",
				"mode_of_payment": GIFT_MODE,
				"type": "General",
				"accounts": [{"company": company, "default_account": acc_name}],
			}
		).insert(ignore_permissions=True)
	else:
		mop = frappe.get_doc("Mode of Payment", GIFT_MODE)
		if not any(a.company == company for a in mop.accounts):
			mop.append("accounts", {"company": company, "default_account": acc_name})
			mop.save(ignore_permissions=True)
	return acc_name


@frappe.whitelist()
def check_opening_shift():
	"""Gate for entering the POS: returns the open shift or None."""
	_require_login()
	return _open_shift()


@frappe.whitelist()
def create_opening_shift(pos_profile, company, balances):
	"""Open the till — POS Opening Entry with opening cash per mode of payment."""
	_require_login()
	if isinstance(balances, str):
		balances = json.loads(balances)
	existing = _open_shift()
	if existing:
		return existing
	doc = frappe.get_doc(
		{
			"doctype": "POS Opening Entry",
			"period_start_date": frappe.utils.now_datetime(),
			"posting_date": frappe.utils.getdate(),
			"user": frappe.session.user,
			"pos_profile": pos_profile,
			"company": company,
			"balance_details": [
				{"mode_of_payment": b["mode_of_payment"], "opening_amount": flt(b.get("opening_amount"))}
				for b in balances
			],
		}
	)
	doc.flags.ignore_permissions = True
	doc.submit()
	return {"name": doc.name, "company": doc.company, "pos_profile": doc.pos_profile}


def _resolve_customer(profile):
	"""POS Profile customer, else a Walk-In Customer (created once if missing)."""
	if profile.customer:
		return profile.customer
	name = "Walk-In Customer"
	if not frappe.db.exists("Customer", name):
		frappe.get_doc(
			{
				"doctype": "Customer",
				"customer_name": name,
				"customer_group": "All Customer Groups",
				"territory": "All Territories",
				"customer_type": "Individual",
			}
		).insert(ignore_permissions=True)
	return name


def _order_result(si, idempotent=False, gift_applied=0.0):
	return {
		"name": si.name,
		"grand_total": float(si.grand_total or 0),
		"paid_amount": float(si.paid_amount or 0),
		"change_amount": float(si.change_amount or 0),
		"gift_applied": float(gift_applied or 0),
		"idempotent": idempotent,
	}


@frappe.whitelist()
def submit_order(cart, payments, discount=0, pos_profile=None, request_id=None, table=None, gift_card=None):
	"""Build + submit a POS Sales Invoice server-side (posawesome pattern). Server
	prices from the profile price list — no client rate is trusted. Phase 1 handles
	base items only; item add-ons and gift cards are Phase 2 (the frontend blocks
	checkout when either is present so shown total always equals submitted total)."""
	_require_login()
	if isinstance(cart, str):
		cart = json.loads(cart)
	if isinstance(payments, str):
		payments = json.loads(payments)

	shift = _open_shift()
	if not shift:
		frappe.throw(_("Open a POS shift before selling."))

	# Idempotency: check-first (blocks double-click / retry) — the primary guard.
	if request_id:
		existing = frappe.db.get_value("Sales Invoice", {"losand_pos_request_id": request_id}, "name")
		if existing:
			return _order_result(frappe.get_doc("Sales Invoice", existing), idempotent=True)

	p = _resolve_pos_profile(pos_profile or shift.get("pos_profile"))
	si = frappe.new_doc("Sales Invoice")
	si.is_pos = 1
	si.update_stock = 1
	si.pos_profile = p.name
	si.company = p.company
	si.customer = _resolve_customer(p)
	si.selling_price_list = p.selling_price_list
	si.currency = p.currency
	if p.warehouse:
		si.set_warehouse = p.warehouse
	if request_id:
		si.losand_pos_request_id = request_id
	if table:
		si.po_no = table  # ponytail: stash dine-in table on po_no until a real field exists

	# Base items + flattened add-on lines both arrive here as {item_code, qty}. Never
	# skip a non-empty code: a bad code must FAIL the order, not silently drop a paid
	# line (that would undercharge vs what the customer was shown).
	for line in cart:
		code = line.get("item_code") or line.get("id")
		qty = flt(line.get("qty") or 1)
		if not code or qty <= 0:
			frappe.throw(_("Invalid cart line."))
		if not frappe.db.exists("Item", code):
			frappe.throw(_("Unknown item: {0}").format(code))
		# Batch-tracked FG (from the factory) must carry a batch. Reuse the manufacture
		# FEFO allocator: one SI row per batch. Non-stock add-ons return a single
		# (None, qty) row. No rate is passed — the server prices from the price list.
		for batch_no, q in _stock_rows(code, p.warehouse, qty):
			row = {"item_code": code, "qty": q}
			if batch_no:
				row.update({"use_serial_batch_fields": 1, "batch_no": batch_no, "warehouse": p.warehouse})
			si.append("items", row)
	if not si.get("items"):
		frappe.throw(_("Cart is empty."))

	disc = flt(discount)
	if disc > 0:
		si.apply_discount_on = "Grand Total"
		si.discount_amount = disc  # ERPNext's flat additional-discount field

	si.flags.ignore_permissions = True
	si.set_missing_values()
	si.calculate_taxes_and_totals()

	# Payments: gift card is tendered first (min of balance and total), the selected
	# mode covers the rest. Split is computed against the SERVER grand_total, so it is
	# correct regardless of what the client showed.
	gc = None
	gift_applied = 0.0
	if gift_card:
		gc = frappe.db.get_value(
			"Los Andalus Gift Card", {"card_no": gift_card, "is_active": 1}, ["name", "balance"], as_dict=True
		)
		if not gc:
			frappe.throw(_("Invalid or inactive gift card."))
		gift_applied = min(flt(gc.balance), flt(si.grand_total))
		if gift_applied > 0:
			_ensure_gift_mode(si.company)
			si.append("payments", {"mode_of_payment": GIFT_MODE, "amount": gift_applied})

	remaining = flt(si.grand_total) - gift_applied
	if remaining > 0:
		mode = payments[0]["mode_of_payment"] if payments else "Cash"
		si.append("payments", {"mode_of_payment": mode, "amount": remaining})

	si.insert(ignore_permissions=True)  # validate() recomputes paid/change from payments
	si.submit()
	# Decrement the card only after the invoice is submitted; an earlier failure rolls
	# back with the transaction (no commit yet), so the balance is never lost.
	if gc and gift_applied > 0:
		frappe.db.set_value("Los Andalus Gift Card", gc.name, "balance", flt(gc.balance) - gift_applied)
	frappe.db.commit()
	return _order_result(si, gift_applied=gift_applied)


# ---------------------------------------------------------------------------
# Phase 3 — inventory ops: stocktake (Stock Reconciliation) + receiving (Stock Entry)
# ---------------------------------------------------------------------------
def _inv_warehouse(warehouse=None):
	"""Inventory ops run on the ingredient store (raw materials), not the FG/POS
	warehouse — you count and receive ingredients, you sell finished goods."""
	return warehouse or cfg().source


@frappe.whitelist()
def get_inventory(warehouse=None):
	"""Stock items in the store with their system qty — for the stocktake table and
	the receiving item picker. `batched` items can be received but not yet counted."""
	_require_login()
	wh = _inv_warehouse(warehouse)
	bins = {b.item_code: b.actual_qty for b in frappe.get_all("Bin", filters={"warehouse": wh}, fields=["item_code", "actual_qty"])}
	codes = list(bins)
	items = (
		frappe.get_all(
			"Item",
			filters={"item_code": ["in", codes], "disabled": 0, "is_stock_item": 1},
			fields=["item_code", "item_name", "item_group", "stock_uom", "has_batch_no", "safety_stock"],
			order_by="item_name asc",
		)
		if codes
		else []
	)
	return {
		"warehouse": wh,
		"items": [
			{
				"id": i.item_code,
				"name": i.item_name,
				"category": i.item_group,
				"uom": i.stock_uom,
				"system_qty": float(bins.get(i.item_code) or 0),
				"warn": float(i.safety_stock or 0),  # reorder/low-stock threshold, if set
				"batched": bool(i.has_batch_no),
			}
			for i in items
		],
	}


@frappe.whitelist()
def save_stocktake(counts, warehouse=None):
	"""End-of-shift count → adjust each counted item to its counted qty by posting the
	DIFFERENCE: Material Issue (FEFO across batches) for shortages, Material Receipt
	for surplus. Batch-capable — shortages consume existing batches, surplus lands in
	a new one. Difference is valued against the Stock Adjustment account.
	ponytail: a difference Stock Entry, not a formal Stock Reconciliation — chosen
	because every store item is batch-tracked and a per-item total can't drive
	reconciliation without per-batch input. Per-batch stocktake is the audit-grade upgrade."""
	_require_login()
	if isinstance(counts, str):
		counts = json.loads(counts)
	wh = _inv_warehouse(warehouse)
	company = frappe.db.get_value("Warehouse", wh, "company") or cfg().company
	adj = cfg().clearing or frappe.db.get_value(
		"Account", {"company": company, "account_type": "Stock Adjustment", "is_group": 0}, "name"
	)

	shortages, surplus = [], []
	counted_n = 0
	for c in counts:
		code = c.get("item_code") or c.get("id")
		counted = c.get("counted")
		if not code or counted in (None, ""):
			continue
		if not frappe.db.exists("Item", code):
			frappe.throw(_("Unknown item: {0}").format(code))
		counted_n += 1
		system = flt(frappe.db.get_value("Bin", {"item_code": code, "warehouse": wh}, "actual_qty") or 0)
		diff = flt(counted) - system
		if abs(diff) < 1e-9:
			continue
		(surplus if diff > 0 else shortages).append((code, abs(diff)))

	entries = []
	if shortages:
		se = frappe.new_doc("Stock Entry")
		se.stock_entry_type = "Material Issue"
		se.company = company
		se.from_warehouse = wh
		for code, q in shortages:
			for batch_no, qq in _stock_rows(code, wh, q):
				row = {"item_code": code, "qty": qq, "s_warehouse": wh, "expense_account": adj}
				if batch_no:
					row.update({"use_serial_batch_fields": 1, "batch_no": batch_no})
				se.append("items", row)
		se.flags.ignore_permissions = True
		se.insert(ignore_permissions=True)
		se.submit()
		entries.append(se.name)
	if surplus:
		se = frappe.new_doc("Stock Entry")
		se.stock_entry_type = "Material Receipt"
		se.company = company
		se.to_warehouse = wh
		for code, q in surplus:
			row = {"item_code": code, "qty": q, "t_warehouse": wh, "expense_account": adj}
			rate = _last_receipt_rate(code, wh)
			if rate:
				row["basic_rate"] = rate
			if frappe.db.get_value("Item", code, "has_batch_no"):
				row["use_serial_batch_fields"] = 1
			se.append("items", row)
		se.flags.ignore_permissions = True
		se.insert(ignore_permissions=True)
		se.submit()
		entries.append(se.name)

	if not entries:
		frappe.throw(_("No stock differences to post."))
	frappe.db.commit()
	return {"entries": entries, "counted": counted_n}


@frappe.whitelist()
def receive_goods(lines, supplier=None, note=None, warehouse=None):
	"""Morning goods receipt → Stock Entry (Material Receipt) into the store."""
	_require_login()
	if isinstance(lines, str):
		lines = json.loads(lines)
	wh = _inv_warehouse(warehouse)
	company = frappe.db.get_value("Warehouse", wh, "company") or cfg().company
	se = frappe.new_doc("Stock Entry")
	se.stock_entry_type = "Material Receipt"
	se.company = company
	se.to_warehouse = wh
	remarks = " / ".join(x for x in [f"المورّد: {supplier}" if supplier else "", note or ""] if x)
	if remarks:
		se.remarks = remarks
	for line in lines:
		code = line.get("item_code") or line.get("id")
		qty = flt(line.get("qty"))
		if not code or qty <= 0:
			continue
		if not frappe.db.exists("Item", code):
			frappe.throw(_("Unknown item: {0}").format(code))
		row = {"item_code": code, "qty": qty, "t_warehouse": wh}
		rate = _last_receipt_rate(code, wh)
		if rate:
			row["basic_rate"] = rate
		if frappe.db.get_value("Item", code, "has_batch_no"):
			row["use_serial_batch_fields"] = 1  # ERPNext auto-creates the batch on receipt
		se.append("items", row)
	if not se.get("items"):
		frappe.throw(_("No items to receive."))
	se.flags.ignore_permissions = True
	se.insert(ignore_permissions=True)
	se.submit()
	frappe.db.commit()
	return {"name": se.name, "lines": len(se.items)}


# ---------------------------------------------------------------------------
# Phase 4 — parked orders (persisted holds) + shift close (reconciliation)
# ---------------------------------------------------------------------------
@frappe.whitelist()
def park_order(payload, table=None, total=0, pos_profile=None):
	"""Persist the current order (full cart JSON) so it survives navigation/reload.
	The payload only restores the register UI — money is always re-priced server-side
	at checkout — so it is stored verbatim, not validated here."""
	_require_login()
	shift = _open_shift()
	if not shift:
		frappe.throw(_("Open a POS shift first."))
	p = _resolve_pos_profile(pos_profile or shift.get("pos_profile"))
	doc = frappe.get_doc(
		{
			"doctype": "Los Andalus Parked Order",
			"pos_profile": p.name,
			"user": frappe.session.user,
			"table_label": table,
			"total": flt(total),
			"payload": payload if isinstance(payload, str) else json.dumps(payload),
		}
	)
	doc.flags.ignore_permissions = True
	doc.insert(ignore_permissions=True)
	frappe.db.commit()
	return {"name": doc.name}


@frappe.whitelist()
def list_parked():
	"""The current user's parked orders."""
	_require_login()
	return frappe.get_all(
		"Los Andalus Parked Order",
		filters={"user": frappe.session.user},
		fields=["name", "table_label", "total"],
		order_by="creation desc",
	)


def _own_parked(name):
	if frappe.db.get_value("Los Andalus Parked Order", name, "user") != frappe.session.user:
		frappe.throw(_("Not your parked order."), frappe.PermissionError)


@frappe.whitelist()
def resume_order(name):
	"""Return a parked order's payload and remove it — it moves back to the register."""
	_require_login()
	_own_parked(name)
	payload = frappe.db.get_value("Los Andalus Parked Order", name, "payload")
	frappe.delete_doc("Los Andalus Parked Order", name, ignore_permissions=True, force=True)
	frappe.db.commit()
	return {"name": name, "payload": json.loads(payload) if payload else None}


@frappe.whitelist()
def discard_parked(name):
	"""Delete a parked order without resuming it."""
	_require_login()
	_own_parked(name)
	frappe.delete_doc("Los Andalus Parked Order", name, ignore_permissions=True, force=True)
	frappe.db.commit()
	return {"name": name}


def _shift_reconciliation(shift):
	"""Aggregate the open shift's POS sales in its time window, per mode of payment:
	expected = opening float + cash taken. Reconciliation-only — GL/stock already
	posted at each sale, so nothing is settled here."""
	opening = frappe.get_doc("POS Opening Entry", shift["name"])
	start = opening.period_start_date
	end = frappe.utils.now_datetime()
	opening_map = {b.mode_of_payment: flt(b.opening_amount) for b in opening.balance_details}

	sis = frappe.get_all(
		"Sales Invoice",
		filters={
			"is_pos": 1,
			"docstatus": 1,
			"pos_profile": opening.pos_profile,
			"owner": frappe.session.user,
			"creation": ["between", [start, end]],
		},
		fields=["name", "grand_total"],
	)
	sales_total = sum(flt(s.grand_total) for s in sis)
	mode_sales = {}
	for s in sis:
		for pay in frappe.get_all(
			"Sales Invoice Payment", filters={"parent": s.name}, fields=["mode_of_payment", "amount"]
		):
			mode_sales[pay.mode_of_payment] = mode_sales.get(pay.mode_of_payment, 0) + flt(pay.amount)

	modes = sorted(set(opening_map) | set(mode_sales))
	recon = [
		{
			"mode": m,
			"opening": opening_map.get(m, 0.0),
			"sales": mode_sales.get(m, 0.0),
			"expected": opening_map.get(m, 0.0) + mode_sales.get(m, 0.0),
		}
		for m in modes
	]
	return opening, start, end, sales_total, len(sis), recon


@frappe.whitelist()
def get_shift_summary():
	"""Preview totals for the close-shift screen (before counting cash)."""
	_require_login()
	shift = _open_shift()
	if not shift:
		frappe.throw(_("No open shift."))
	_opening, start, end, sales_total, count, recon = _shift_reconciliation(shift)
	return {
		"opening_entry": shift["name"],
		"pos_profile": shift.get("pos_profile"),
		"period_start": str(start),
		"sales_total": sales_total,
		"invoice_count": count,
		"reconciliation": recon,
	}


@frappe.whitelist()
def close_shift(counted=None):
	"""Close the open shift: record expected-vs-counted per mode and mark the shift
	closed (a Los Andalus POS Closing referencing the opening entry). `counted` is an
	optional {mode: amount} map; unspecified modes default to their expected amount."""
	_require_login()
	if isinstance(counted, str):
		counted = json.loads(counted)
	counted = counted or {}
	shift = _open_shift()
	if not shift:
		frappe.throw(_("No open shift."))
	opening, start, end, sales_total, _count, recon = _shift_reconciliation(shift)

	expected_cash = counted_cash = 0.0
	for r in recon:
		r["counted"] = flt(counted.get(r["mode"], r["expected"]))
		r["difference"] = r["counted"] - r["expected"]
		if r["mode"] == "Cash":
			expected_cash = r["expected"]
			counted_cash = r["counted"]

	doc = frappe.get_doc(
		{
			"doctype": "Los Andalus POS Closing",
			"opening_entry": opening.name,
			"pos_profile": opening.pos_profile,
			"user": frappe.session.user,
			"period_start": start,
			"period_end": end,
			"sales_total": sales_total,
			"expected_cash": expected_cash,
			"counted_cash": counted_cash,
			"difference": counted_cash - expected_cash,
			"reconciliation": json.dumps(recon, ensure_ascii=False),
		}
	)
	doc.flags.ignore_permissions = True
	doc.insert(ignore_permissions=True)
	frappe.db.commit()
	return {"name": doc.name, "sales_total": sales_total, "reconciliation": recon}
