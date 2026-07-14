from __future__ import annotations

import json

import frappe
from frappe import _
from frappe.utils import cint, flt

from losand.api.manufacture import _last_receipt_rate, _stock_map, _stock_rows, cfg
from losand.setup.publish_print_formats import RECEIPT_FORMAT_NAME

# The portal uses the standard ERPNext POS Profile as its single source of truth
# and submits server-side Sales Invoices.


def _require_login():
	if frappe.session.user == "Guest":
		frappe.throw(_("Login required"), frappe.PermissionError)


POS_MANAGER_ROLES = {"POS Manager", "System Manager"}


def _require_pos_manager():
	"""Gate for actions that reverse a submitted invoice's stock/GL impact
	(return, edit, delete) — any cashier can view history, only a supervisor
	can void or rewrite what already posted."""
	if not POS_MANAGER_ROLES & set(frappe.get_roles()):
		frappe.throw(_("Only a POS Manager can do this."), frappe.PermissionError)


def _resolve_pos_profile(name=None):
	"""Pick the POS Profile: explicit arg → one the user is applicable for →
	first enabled for the default company."""
	if name:
		if not frappe.db.exists("POS Profile", name):
			frappe.throw(_("POS Profile {0} does not exist.").format(name))
		if frappe.db.get_value("POS Profile", name, "disabled"):
			frappe.throw(_("POS Profile {0} is disabled.").format(name))
		assigned_users = frappe.get_all(
			"POS Profile User", filters={"parent": name, "parenttype": "POS Profile"}, pluck="user"
		)
		if assigned_users and frappe.session.user not in assigned_users:
			frappe.throw(_("POS Profile {0} is not assigned to this user.").format(name), frappe.PermissionError)
		return frappe.get_cached_doc("POS Profile", name)

	linked = frappe.get_all(
		"POS Profile User",
		filters={"user": frappe.session.user, "parenttype": "POS Profile"},
		fields=["parent", "default"],
		order_by="`default` desc, idx asc",
	)
	for row in linked:
		if not frappe.db.get_value("POS Profile", row.parent, "disabled"):
			return frappe.get_cached_doc("POS Profile", row.parent)

	filters = {"disabled": 0}
	company = frappe.defaults.get_global_default("company")
	if company:
		filters["company"] = company
	first = frappe.get_all("POS Profile", filters=filters, limit=1, pluck="name")
	if first:
		return frappe.get_cached_doc("POS Profile", first[0])

	frappe.throw(_("No POS Profile is configured. Create one in ERPNext first."))


def _expanded_groups(doctype, configured):
	"""Expand configured tree nodes to include descendants."""
	if not configured:
		return []

	groups = set()
	for group in configured:
		bounds = frappe.db.get_value(doctype, group, ["lft", "rgt"], as_dict=True)
		if not bounds:
			continue
		groups.update(
			frappe.get_all(
				doctype,
				filters=[["lft", ">=", bounds.lft], ["rgt", "<=", bounds.rgt]],
				pluck="name",
			)
		)
	return sorted(groups)


def _expanded_item_groups(profile):
	"""Profile item groups include their descendants, matching ERPNext POS."""
	return _expanded_groups("Item Group", [row.item_group for row in (profile.item_groups or [])])


@frappe.whitelist()
def get_pos_config(pos_profile=None):
	"""Return the standard ERPNext POS Profile settings used by the portal.

	Operational flags stay flat in the response so every POS screen consumes one
	source of truth. Accounting defaults are applied to the invoice server-side.
	"""
	_require_login()
	p = _resolve_pos_profile(pos_profile)
	symbol = frappe.db.get_value("Currency", p.currency, "symbol") or p.currency
	mop_types = {
		r.mode_of_payment: frappe.get_cached_value("Mode of Payment", r.mode_of_payment, "type")
		for r in p.payments
	}
	return {
		"pos_profile": p.name,
		"is_pos_manager": bool(POS_MANAGER_ROLES & set(frappe.get_roles())),
		"company": p.company,
		"warehouse": p.warehouse,
		"currency": p.currency,
		"currency_symbol": symbol,
		"price_list": p.selling_price_list,
		"customer": p.customer,
		"country": p.country,
		"disabled": bool(p.disabled),
		"company_address": p.company_address,
		"campaign": p.campaign,
		"applicable_users": [
			{"user": row.user, "default": bool(row.default)}
			for row in (p.applicable_for_users or [])
		],
		"payments": [
			{
				"mode_of_payment": r.mode_of_payment,
				"default": bool(r.default),
				"type": mop_types.get(r.mode_of_payment),
			}
			for r in p.payments
		],
		"item_groups": [r.item_group for r in (p.item_groups or [])],
		"customer_groups": [r.customer_group for r in (p.customer_groups or [])],
		"hide_images": bool(p.hide_images),
		"hide_unavailable_items": bool(p.hide_unavailable_items),
		"auto_add_item_to_cart": bool(p.auto_add_item_to_cart),
		"validate_stock_on_save": bool(p.validate_stock_on_save),
		"print_receipt_on_order_complete": bool(p.print_receipt_on_order_complete),
		"update_stock": bool(p.update_stock),
		"ignore_pricing_rule": bool(p.ignore_pricing_rule),
		"allow_rate_change": bool(p.allow_rate_change),
		"allow_discount_change": bool(p.allow_discount_change),
		"disable_grand_total_to_default_mop": bool(p.disable_grand_total_to_default_mop),
		"allow_partial_payment": bool(p.allow_partial_payment),
		# Resolved server-side so the clients don't each carry a default. Falls back to
		# our receipt, not ERPNext's stock "POS Invoice" (which is registered against the
		# POS Invoice doctype, not Sales Invoice).
		"print_format": p.print_format or RECEIPT_FORMAT_NAME,
		"letter_head": p.letter_head,
		"terms_and_conditions": p.tc_name,
		"print_heading": p.select_print_heading,
		"taxes_and_charges": p.taxes_and_charges,
		"tax_category": p.tax_category,
		"apply_discount_on": p.apply_discount_on,
		"disable_rounded_total": bool(p.disable_rounded_total),
		"write_off_account": p.write_off_account,
		"write_off_cost_center": p.write_off_cost_center,
		"write_off_limit": float(p.write_off_limit or 0),
		"account_for_change_amount": p.account_for_change_amount,
		"income_account": p.income_account,
		"expense_account": p.expense_account,
		"cost_center": p.cost_center,
		"project": p.project,
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
	allowed_groups = _expanded_item_groups(p)

	filters = [
		["disabled", "=", 0],
		["is_sales_item", "=", 1],
		["has_variants", "=", 0],
		["is_fixed_asset", "=", 0],
	]
	if item_group and item_group != "all":
		if allowed_groups and item_group not in allowed_groups:
			return {"categories": [], "products": []}
		filters.append(["item_group", "=", item_group])
	elif allowed_groups:
		filters.append(["item_group", "in", allowed_groups])
	if search:
		filters.append(["item_name", "like", f"%{search}%"])

	items = frappe.get_all(
		"Item",
		filters=filters,
		fields=["item_code", "item_name", "item_group", "image", "stock_uom", "is_stock_item"],
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

	products = []
	for i in items:
		available_qty = float(stock.get(i.item_code, {}).get("qty") or 0)
		if p.hide_unavailable_items and i.is_stock_item and available_qty <= 0:
			continue
		products.append({
			"id": i.item_code,
			"name": i.item_name,
			"category": i.item_group,
			"price": float(price_map.get(i.item_code) or 0),
			"img": None if p.hide_images else i.image,
			"uom": i.stock_uom,
			"is_stock_item": bool(i.is_stock_item),
			"available_qty": available_qty,
		})

	groups = sorted({product["category"] for product in products})
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
	allowed_groups = _expanded_item_groups(p)
	if allowed_groups and ADDON_GROUP not in allowed_groups:
		return []
	items = frappe.get_all(
		"Item",
		filters={"item_group": ADDON_GROUP, "disabled": 0, "is_sales_item": 1},
		fields=["item_code", "item_name", "stock_uom", "is_stock_item"],
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
	stock = _stock_map(codes, p.warehouse) if p.warehouse else {}
	extras = []
	for item in items:
		available_qty = float(stock.get(item.item_code, {}).get("qty") or 0)
		if p.hide_unavailable_items and item.is_stock_item and available_qty <= 0:
			continue
		extras.append(
			{
				"id": item.item_code,
				"item_code": item.item_code,
				"name": item.item_name,
				"price": float(price_map.get(item.item_code) or 0),
				"uom": item.stock_uom,
				"available_qty": available_qty,
			}
		)
	return extras


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
	profile = _resolve_pos_profile(pos_profile)
	if company != profile.company:
		frappe.throw(_("Company must match POS Profile {0}.").format(profile.name))
	allowed_modes = {row.mode_of_payment for row in profile.payments}
	for balance in balances:
		if balance.get("mode_of_payment") not in allowed_modes:
			frappe.throw(
				_("Payment method {0} is not allowed by POS Profile {1}.").format(
					balance.get("mode_of_payment"), profile.name
				)
			)
	doc = frappe.get_doc(
		{
			"doctype": "POS Opening Entry",
			"period_start_date": frappe.utils.now_datetime(),
			"posting_date": frappe.utils.getdate(),
			"user": frappe.session.user,
			"pos_profile": profile.name,
			"company": profile.company,
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
	allowed_groups = _expanded_groups(
		"Customer Group", [row.customer_group for row in (profile.customer_groups or [])]
	)
	if profile.customer:
		customer_group = frappe.db.get_value("Customer", profile.customer, "customer_group")
		if allowed_groups and customer_group not in allowed_groups:
			frappe.throw(
				_("Default customer {0} is outside the customer groups allowed by POS Profile {1}.").format(
					profile.customer, profile.name
				)
			)
		return profile.customer

	if allowed_groups:
		customer = frappe.get_all(
			"Customer",
			filters={"disabled": 0, "customer_group": ["in", allowed_groups]},
			order_by="customer_name asc",
			limit=1,
			pluck="name",
		)
		if customer:
			return customer[0]
		frappe.throw(_("No enabled customer exists in the customer groups allowed by POS Profile {0}.").format(profile.name))

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
	payable_total = flt(si.rounded_total) or flt(si.grand_total)
	return {
		"name": si.name,
		"net_total": float(si.net_total or 0),
		"taxes": float(si.total_taxes_and_charges or 0),
		"grand_total": float(si.grand_total or 0),
		"rounded_total": float(si.rounded_total or si.grand_total or 0),
		"payable_total": float(payable_total),
		"paid_amount": float(si.paid_amount or 0),
		"change_amount": float(si.change_amount or 0),
		"gift_applied": float(gift_applied or 0),
		"idempotent": idempotent,
	}


@frappe.whitelist()
def preview_order(cart, discount=0, pos_profile=None):
	"""Calculate the cart with the active profile without writing a document.

	This keeps taxes, pricing rules, discount basis, and rounded totals shown in
	the custom UI aligned with the Sales Invoice that checkout will submit.
	"""
	_require_login()
	if isinstance(cart, str):
		cart = json.loads(cart)

	p = _resolve_pos_profile(pos_profile)
	si = frappe.new_doc("Sales Invoice")
	si.is_pos = 1
	si.update_stock = cint(p.update_stock)
	si.pos_profile = p.name
	si.company = p.company
	si.customer = _resolve_customer(p)
	si.selling_price_list = p.selling_price_list
	si.currency = p.currency
	if p.warehouse:
		si.set_warehouse = p.warehouse

	for line in cart:
		code = line.get("item_code") or line.get("id")
		qty = flt(line.get("qty") or 1)
		client_rate = line.get("rate")
		if not code or qty <= 0 or not frappe.db.exists("Item", code):
			frappe.throw(_("Invalid cart line."))
		if client_rate is not None and not p.allow_rate_change:
			frappe.throw(_("Rate changes are not allowed by POS Profile {0}.").format(p.name))
		if p.update_stock and p.validate_stock_on_save:
			_stock_rows(code, p.warehouse, qty)
		row = {"item_code": code, "qty": qty}
		if client_rate is not None:
			row.update({"rate": flt(client_rate), "price_list_rate": flt(client_rate)})
		si.append("items", row)

	disc = flt(discount)
	if disc > 0:
		if not p.allow_discount_change:
			frappe.throw(_("Discount changes are not allowed by POS Profile {0}.").format(p.name))
		si.apply_discount_on = p.apply_discount_on or "Grand Total"
		si.discount_amount = disc

	si.flags.ignore_permissions = True
	si.set_missing_values()
	si.calculate_taxes_and_totals()
	return {
		"net_total": float(si.net_total or 0),
		"taxes": float(si.total_taxes_and_charges or 0),
		"grand_total": float(si.grand_total or 0),
		"rounded_total": float(si.rounded_total or si.grand_total or 0),
	}


@frappe.whitelist()
def submit_order(cart, payments, discount=0, pos_profile=None, request_id=None, table=None, gift_card=None):
	"""Build and submit a POS Sales Invoice using the active POS Profile.

	Client rates and discounts are accepted only when their corresponding profile
	permissions are enabled; all other pricing and accounting defaults are server
	derived.
	"""
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
	si.update_stock = cint(p.update_stock)
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

	for fieldname in (
		"account_for_change_amount",
		"apply_discount_on",
		"campaign",
		"company_address",
		"cost_center",
		"disable_rounded_total",
		"ignore_pricing_rule",
		"letter_head",
		"project",
		"select_print_heading",
		"tax_category",
		"taxes_and_charges",
		"tc_name",
		"write_off_account",
		"write_off_cost_center",
	):
		if si.meta.has_field(fieldname):
			si.set(fieldname, p.get(fieldname))

	# Base items + flattened add-on lines both arrive here as {item_code, qty}. Never
	# skip a non-empty code: a bad code must FAIL the order, not silently drop a paid
	# line (that would undercharge vs what the customer was shown).
	for line in cart:
		code = line.get("item_code") or line.get("id")
		qty = flt(line.get("qty") or 1)
		client_rate = line.get("rate")
		if not code or qty <= 0:
			frappe.throw(_("Invalid cart line."))
		if not frappe.db.exists("Item", code):
			frappe.throw(_("Unknown item: {0}").format(code))
		if client_rate is not None and not p.allow_rate_change:
			frappe.throw(_("Rate changes are not allowed by POS Profile {0}.").format(p.name))
		# Batch-tracked FG (from the factory) must carry a batch. Reuse the manufacture
		# FEFO allocator: one SI row per batch. Non-stock add-ons return a single
		# (None, qty) row. A client rate is only present when the profile permits it.
		stock_rows = _stock_rows(code, p.warehouse, qty) if p.update_stock else [(None, qty)]
		note = line.get("note")
		for batch_no, q in stock_rows:
			row = {"item_code": code, "qty": q}
			if client_rate is not None:
				row.update({"rate": flt(client_rate), "price_list_rate": flt(client_rate)})
			if batch_no:
				row.update({"use_serial_batch_fields": 1, "batch_no": batch_no, "warehouse": p.warehouse})
			if note:
				row["losand_kitchen_note"] = note
			si.append("items", row)
	if not si.get("items"):
		frappe.throw(_("Cart is empty."))

	disc = flt(discount)
	if disc > 0:
		if not p.allow_discount_change:
			frappe.throw(_("Discount changes are not allowed by POS Profile {0}.").format(p.name))
		si.apply_discount_on = p.apply_discount_on or "Grand Total"
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
		payable_total = flt(si.rounded_total) or flt(si.grand_total)
		gift_applied = min(flt(gc.balance), payable_total)
		if gift_applied > 0:
			_ensure_gift_mode(si.company)
			si.append("payments", {"mode_of_payment": GIFT_MODE, "amount": gift_applied})

	payable_total = flt(si.rounded_total) or flt(si.grand_total)
	remaining = payable_total - gift_applied
	if remaining > 0:
		allowed_modes = {row.mode_of_payment for row in p.payments}
		default_mode = next((row.mode_of_payment for row in p.payments if row.default), None)
		requested = payments or ([{"mode_of_payment": default_mode}] if default_mode else [])
		if not requested:
			frappe.throw(_("No payment method is configured in POS Profile {0}.").format(p.name))

		amounts_supplied = any(row.get("amount") not in (None, "") for row in requested)
		for index, payment in enumerate(requested):
			mode = payment.get("mode_of_payment")
			if mode not in allowed_modes:
				frappe.throw(_("Payment method {0} is not allowed by POS Profile {1}.").format(mode, p.name))
			amount = flt(payment.get("amount")) if amounts_supplied else (remaining if index == 0 else 0)
			if amount > 0:
				si.append("payments", {"mode_of_payment": mode, "amount": amount})

		paid = sum(flt(row.amount) for row in si.payments)
		if paid + 1e-9 < payable_total and not p.allow_partial_payment:
			frappe.throw(_("Partial payment is not allowed by POS Profile {0}.").format(p.name))

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
	profile = _resolve_pos_profile(shift.get("pos_profile"))
	symbol = frappe.db.get_value("Currency", profile.currency, "symbol") or profile.currency
	_opening, start, end, sales_total, count, recon = _shift_reconciliation(shift)
	return {
		"opening_entry": shift["name"],
		"pos_profile": shift.get("pos_profile"),
		"period_start": str(start),
		"sales_total": sales_total,
		"invoice_count": count,
		"reconciliation": recon,
		"currency": profile.currency,
		"currency_symbol": symbol,
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


# ---------------------------------------------------------------------------
# Phase 5 — invoice history for the current shift + return / edit / delete
# ---------------------------------------------------------------------------
@frappe.whitelist()
def get_shift_invoices():
	"""Sales Invoices created during the CURRENT open shift, for the cashier's
	history screen. Read-only — any logged-in POS user can see it; the
	destructive actions below (return/edit/delete) are supervisor-gated."""
	_require_login()
	shift = _open_shift()
	if not shift:
		frappe.throw(_("No open shift."))
	opening = frappe.get_doc("POS Opening Entry", shift["name"])
	return frappe.get_all(
		"Sales Invoice",
		filters={
			"is_pos": 1,
			"pos_profile": opening.pos_profile,
			"owner": frappe.session.user,
			"creation": ["between", [opening.period_start_date, frappe.utils.now_datetime()]],
			"docstatus": ["!=", 2],
		},
		fields=["name", "customer", "grand_total", "paid_amount", "posting_date", "po_no", "docstatus", "is_return"],
		order_by="creation desc",
	)


@frappe.whitelist()
def return_invoice(invoice):
	"""Create and submit a return (credit note) against a submitted POS invoice —
	the audit-safe way to undo a sale: the original stays on record, a negative
	invoice offsets its stock and GL impact. Supervisor-only."""
	_require_login()
	_require_pos_manager()
	from erpnext.controllers.sales_and_purchase_return import make_return_doc

	original = frappe.get_doc("Sales Invoice", invoice)
	if original.docstatus != 1:
		frappe.throw(_("Only a submitted invoice can be returned."))
	return_doc = make_return_doc("Sales Invoice", invoice)
	return_doc.flags.ignore_permissions = True
	return_doc.insert(ignore_permissions=True)
	return_doc.submit()
	frappe.db.commit()
	return {"name": return_doc.name, "return_against": invoice}


@frappe.whitelist()
def edit_invoice(invoice):
	"""Cancel a submitted invoice and hand its item lines back to the register so
	the cashier can re-key and re-submit a corrected order. Supervisor-only —
	cancelling reverses the original's stock and GL impact.

	ponytail: per-piece add-ons/notes aren't reconstructable (they were already
	flattened into plain Item rows at checkout, same simplification as elsewhere
	in this app) — the cart comes back as flat item/qty/rate lines, not the
	original pieces/extras structure. The cashier re-applies any customization."""
	_require_login()
	_require_pos_manager()
	doc = frappe.get_doc("Sales Invoice", invoice)
	if doc.docstatus != 1:
		frappe.throw(_("Only a submitted invoice can be edited."))
	merged = {}
	for row in doc.items:
		line = merged.setdefault(
			row.item_code, {"item_code": row.item_code, "item_name": row.item_name, "qty": 0, "rate": row.rate}
		)
		line["qty"] += flt(row.qty)
	table = doc.po_no
	doc.flags.ignore_permissions = True
	doc.cancel()
	frappe.db.commit()
	return {"cart": list(merged.values()), "table": table}


@frappe.whitelist()
def delete_invoice(invoice):
	"""Cancel (if submitted) and permanently delete an invoice — fully unwinds the
	transaction rather than leaving an audit trail. Supervisor-only, irreversible."""
	_require_login()
	_require_pos_manager()
	doc = frappe.get_doc("Sales Invoice", invoice)
	if doc.docstatus == 1:
		doc.flags.ignore_permissions = True
		doc.cancel()
	frappe.delete_doc("Sales Invoice", invoice, ignore_permissions=True, force=True)
	frappe.db.commit()
	return {"name": invoice}
