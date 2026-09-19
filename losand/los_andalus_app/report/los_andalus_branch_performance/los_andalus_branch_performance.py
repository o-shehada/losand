"""Branch performance: what each branch sold, took in, and consumed — per day, shift
and cashier.

One row = one day × POS Profile × cashier. Money comes from the POS Sales Invoices
that cashier submitted (revenue and the split across Cash / بطاقة / بريستو / بطاقة
هدايا), the shift columns from the POS Opening Entry and the Los Andalus POS Closing
that reconciled it, and the stock columns from the Stock Ledger of the branch
warehouse — value in (transfers received), value out (the end-of-day count and waste),
and the opening/closing valuation of the warehouse itself.

الربح = الإيراد − قيمة المخزون الخارج: the branch sells without moving stock
(POS Profile update_stock = 0), so its cost of the day is exactly what the end-of-day
count issued out of the warehouse. That is why the count matters — an uncounted day
shows revenue with no cost and an inflated profit.

The stock valuation of a warehouse belongs to the day, not to a person, so الافتتاح /
الإغلاق (المخزون) print once per day × branch, on that group's last row.
"""

import frappe
from frappe import _
from frappe.utils import flt, getdate

# The payment split the branches actually use. Anything else lands in "أخرى" rather
# than being silently dropped — an unbucketed mode must still show up in the totals.
GIFT_MODE = "بطاقة هدايا"
PRESTO_MODES = {"بريستو", "Presto"}


def execute(filters=None):
	filters = frappe._dict(filters or {})
	if not filters.from_date or not filters.to_date:
		frappe.throw(_("Set both From Date and To Date."))
	if getdate(filters.from_date) > getdate(filters.to_date):
		frappe.throw(_("From Date must be before To Date."))
	return _columns(), _rows(filters)


def _columns():
	return [
		{"label": _("التاريخ"), "fieldname": "posting_date", "fieldtype": "Date", "width": 95},
		{"label": _("الفرع"), "fieldname": "branch", "fieldtype": "Link", "options": "Branch", "width": 110},
		{"label": _("نقطة البيع"), "fieldname": "pos_profile", "fieldtype": "Link", "options": "POS Profile", "width": 120},
		{"label": _("الكاشير"), "fieldname": "user", "fieldtype": "Link", "options": "User", "width": 150},
		{"label": _("الوردية"), "fieldname": "opening_entry", "fieldtype": "Link", "options": "POS Opening Entry", "width": 130},
		{"label": _("الإغلاق"), "fieldname": "closing_entry", "fieldtype": "Link", "options": "Los Andalus POS Closing", "width": 130},
		{"label": _("رصيد الافتتاح"), "fieldname": "opening_float", "fieldtype": "Currency", "width": 110},
		{"label": _("الفواتير"), "fieldname": "invoices", "fieldtype": "Int", "width": 80},
		{"label": _("الإيراد"), "fieldname": "revenue", "fieldtype": "Currency", "width": 110},
		{"label": _("كاش"), "fieldname": "cash", "fieldtype": "Currency", "width": 100},
		{"label": _("بطاقة"), "fieldname": "card", "fieldtype": "Currency", "width": 100},
		{"label": _("بريستو"), "fieldname": "presto", "fieldtype": "Currency", "width": 100},
		{"label": _("بطاقة هدايا"), "fieldname": "gift", "fieldtype": "Currency", "width": 100},
		{"label": _("أخرى"), "fieldname": "other", "fieldtype": "Currency", "width": 90},
		{"label": _("الكاش المعدود"), "fieldname": "counted_cash", "fieldtype": "Currency", "width": 110},
		{"label": _("فرق الكاش"), "fieldname": "cash_difference", "fieldtype": "Currency", "width": 100},
		{"label": _("المخزون افتتاحًا"), "fieldname": "stock_open", "fieldtype": "Currency", "width": 120},
		{"label": _("وارد للمخزن"), "fieldname": "stock_in", "fieldtype": "Currency", "width": 110},
		{"label": _("خارج من المخزن"), "fieldname": "stock_out", "fieldtype": "Currency", "width": 120},
		{"label": _("الكمية الخارجة"), "fieldname": "qty_out", "fieldtype": "Float", "width": 110},
		{"label": _("المخزون إغلاقًا"), "fieldname": "stock_close", "fieldtype": "Currency", "width": 120},
		{"label": _("الربح"), "fieldname": "profit", "fieldtype": "Currency", "width": 110},
	]


def _dimension_fields():
	from erpnext.accounts.doctype.accounting_dimension.accounting_dimension import (
		get_accounting_dimensions,
	)

	return get_accounting_dimensions()


def _profiles(filters):
	"""POS Profiles in scope → their branch and warehouse. The branch is the accounting
	dimension on the profile (losand_branch); the warehouse is what the branch's stock
	columns are measured on."""
	profile_filters = {}
	if filters.company:
		profile_filters["company"] = filters.company
	if filters.pos_profile:
		profile_filters["name"] = filters.pos_profile
	fields = ["name", "company", "warehouse"]
	if frappe.get_meta("POS Profile").has_field("losand_branch"):
		fields.append("losand_branch")
	rows = frappe.get_all("POS Profile", filters=profile_filters, fields=fields)
	profiles = {
		row.name: frappe._dict(
			company=row.company,
			warehouse=row.warehouse,
			branch=row.get("losand_branch"),
		)
		for row in rows
	}
	if filters.branch:
		profiles = {name: p for name, p in profiles.items() if p.branch == filters.branch}
	return profiles


def _invoice_rows(filters, profiles):
	"""Submitted POS invoices in the window, grouped into (date, profile, cashier)."""
	invoice_filters = [
		["docstatus", "=", 1],
		["is_pos", "=", 1],
		["posting_date", "between", [filters.from_date, filters.to_date]],
		["pos_profile", "in", list(profiles)],
	]
	if filters.company:
		invoice_filters.append(["company", "=", filters.company])
	if filters.user:
		invoice_filters.append(["owner", "=", filters.user])
	# Any other accounting dimension the site defines (cost center, project, one added
	# later) filters the revenue side too — the report never needs to know their names.
	meta = frappe.get_meta("Sales Invoice")
	for fieldname in _dimension_fields():
		value = filters.get(fieldname)
		if value and meta.has_field(fieldname):
			invoice_filters.append([fieldname, "in", value if isinstance(value, list) else [value]])
	return frappe.get_all(
		"Sales Invoice",
		filters=invoice_filters,
		fields=["name", "posting_date", "pos_profile", "owner", "grand_total", "is_return"],
	)


def _payment_split(invoice_names):
	"""Invoice → {bucket: amount}. Buckets follow the Mode of Payment TYPE (Cash /
	Bank), with بريستو and the gift card called out by name — both are type General
	and would otherwise disappear into "أخرى"."""
	if not invoice_names:
		return {}
	types = {
		row.name: row.type for row in frappe.get_all("Mode of Payment", fields=["name", "type"])
	}
	split = {}
	for row in frappe.get_all(
		"Sales Invoice Payment",
		filters={"parent": ["in", invoice_names], "parenttype": "Sales Invoice"},
		fields=["parent", "mode_of_payment", "amount"],
	):
		mode = row.mode_of_payment
		if mode in PRESTO_MODES:
			bucket = "presto"
		elif mode == GIFT_MODE or mode == "Gift Card":
			bucket = "gift"
		elif types.get(mode) == "Cash":
			bucket = "cash"
		elif types.get(mode) == "Bank":
			bucket = "card"
		else:
			bucket = "other"
		split.setdefault(row.parent, {})
		split[row.parent][bucket] = split[row.parent].get(bucket, 0.0) + flt(row.amount)
	return split


def _shifts(filters, profiles):
	"""(date, profile, user) → shift: opening entry, its cash float, and the closing
	that reconciled it (if the shift was closed)."""
	openings = frappe.get_all(
		"POS Opening Entry",
		filters=[
			["docstatus", "<", 2],
			["pos_profile", "in", list(profiles)],
			["period_start_date", "between", [filters.from_date, f"{filters.to_date} 23:59:59"]],
		],
		fields=["name", "pos_profile", "user", "period_start_date"],
	)
	if not openings:
		return {}

	names = [o.name for o in openings]
	floats = {}
	for row in frappe.get_all(
		"POS Opening Entry Detail",
		filters={"parent": ["in", names], "parenttype": "POS Opening Entry"},
		fields=["parent", "mode_of_payment", "opening_amount"],
	):
		floats[row.parent] = floats.get(row.parent, 0.0) + flt(row.opening_amount)

	closings = {
		row.opening_entry: row
		for row in frappe.get_all(
			"Los Andalus POS Closing",
			filters={"opening_entry": ["in", names]},
			fields=["name", "opening_entry", "counted_cash", "difference"],
		)
	}

	shifts = {}
	for opening in openings:
		closing = closings.get(opening.name)
		shifts[(getdate(opening.period_start_date), opening.pos_profile, opening.user)] = frappe._dict(
			opening_entry=opening.name,
			opening_float=floats.get(opening.name, 0.0),
			closing_entry=closing.name if closing else None,
			counted_cash=flt(closing.counted_cash) if closing else 0.0,
			cash_difference=flt(closing.difference) if closing else 0.0,
		)
	return shifts


def _stock_movement(filters, warehouses):
	"""Per (date, warehouse, user): value in, value out, qty out — and per (date,
	warehouse) the opening/closing valuation of the warehouse itself.

	Movement is attributed to the user who POSTED it (the cashier who confirmed the
	transfer or saved the count), so it lines up with that cashier's row. The
	valuation snapshot belongs to the warehouse, not to a person."""
	if not warehouses:
		return {}, {}

	opening_value = {
		wh: flt(
			frappe.db.get_value(
				"Stock Ledger Entry",
				{"warehouse": wh, "is_cancelled": 0, "posting_date": ["<", filters.from_date]},
				"sum(stock_value_difference)",
			)
			or 0
		)
		for wh in warehouses
	}

	entries = frappe.get_all(
		"Stock Ledger Entry",
		filters=[
			["is_cancelled", "=", 0],
			["warehouse", "in", list(warehouses)],
			["posting_date", "between", [filters.from_date, filters.to_date]],
		],
		fields=["warehouse", "posting_date", "owner", "actual_qty", "stock_value_difference"],
		order_by="posting_date asc",
	)

	movement, daily = {}, {}
	for sle in entries:
		date = getdate(sle.posting_date)
		value = flt(sle.stock_value_difference)
		bucket = movement.setdefault(
			(date, sle.warehouse, sle.owner), frappe._dict(stock_in=0.0, stock_out=0.0, qty_out=0.0)
		)
		if value >= 0:
			bucket.stock_in += value
		else:
			bucket.stock_out += -value
		if flt(sle.actual_qty) < 0:
			bucket.qty_out += -flt(sle.actual_qty)
		daily.setdefault((date, sle.warehouse), 0.0)
		daily[(date, sle.warehouse)] += value

	# Roll the opening valuation forward day by day so each row's المخزون افتتاحًا is
	# the value the warehouse actually started that day with.
	snapshots, running = {}, dict(opening_value)
	for (date, wh) in sorted(daily, key=lambda k: (k[1], k[0])):
		snapshots[(date, wh)] = frappe._dict(
			stock_open=running[wh], stock_close=running[wh] + daily[(date, wh)]
		)
		running[wh] += daily[(date, wh)]
	return movement, snapshots


def _rows(filters):
	profiles = _profiles(filters)
	if not profiles:
		return []

	invoices = _invoice_rows(filters, profiles)
	split = _payment_split([i.name for i in invoices])
	shifts = _shifts(filters, profiles)
	warehouses = {p.warehouse for p in profiles.values() if p.warehouse}
	movement, snapshots = _stock_movement(filters, warehouses)

	rows = {}

	def row_for(date, pos_profile, user):
		key = (date, pos_profile, user)
		if key not in rows:
			profile = profiles[pos_profile]
			shift = shifts.get(key) or frappe._dict()
			rows[key] = frappe._dict(
				posting_date=date,
				branch=profile.branch,
				pos_profile=pos_profile,
				user=user,
				opening_entry=shift.get("opening_entry"),
				closing_entry=shift.get("closing_entry"),
				opening_float=flt(shift.get("opening_float")),
				counted_cash=flt(shift.get("counted_cash")),
				cash_difference=flt(shift.get("cash_difference")),
				invoices=0,
				revenue=0.0,
				cash=0.0,
				card=0.0,
				presto=0.0,
				gift=0.0,
				other=0.0,
				stock_in=0.0,
				stock_out=0.0,
				qty_out=0.0,
				stock_open=None,
				stock_close=None,
				profit=0.0,
			)
		return rows[key]

	for invoice in invoices:
		row = row_for(getdate(invoice.posting_date), invoice.pos_profile, invoice.owner)
		row.invoices += 1
		row.revenue += flt(invoice.grand_total)
		for bucket, amount in (split.get(invoice.name) or {}).items():
			row[bucket] += amount

	# A shift with no sales is still a shift — the report must show the branch opened
	# and took nothing, not hide the day entirely.
	for (date, pos_profile, user) in shifts:
		if pos_profile in profiles and (not filters.user or filters.user == user):
			row_for(date, pos_profile, user)

	warehouse_profile = {}
	for name, profile in profiles.items():
		if profile.warehouse:
			warehouse_profile.setdefault(profile.warehouse, name)

	for (date, warehouse, user), moved in movement.items():
		pos_profile = warehouse_profile.get(warehouse)
		if not pos_profile or (filters.user and filters.user != user):
			continue
		row = row_for(date, pos_profile, user)
		row.stock_in += moved.stock_in
		row.stock_out += moved.stock_out
		row.qty_out += moved.qty_out

	data = [rows[key] for key in sorted(rows, key=lambda k: (k[0], k[1], k[2] or ""))]
	for row in data:
		row.profit = row.revenue - row.stock_out

	# One valuation snapshot per day × branch, on the group's last row.
	seen = {}
	for index, row in enumerate(data):
		warehouse = profiles[row.pos_profile].warehouse
		if warehouse:
			seen[(row.posting_date, warehouse)] = index
	for (date, warehouse), index in seen.items():
		snapshot = snapshots.get((date, warehouse))
		if snapshot:
			data[index].stock_open = snapshot.stock_open
			data[index].stock_close = snapshot.stock_close
	return data
