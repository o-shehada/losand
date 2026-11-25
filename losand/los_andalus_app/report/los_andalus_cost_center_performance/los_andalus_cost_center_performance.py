"""Income, expense and net result per Cost Center, straight from the GL.

Branches and production lines each have their own Cost Center (see api/pos.py
_stamp_branch and api/manufacture.py submit_batch), so this is the per-branch and
per-line profit and loss.
"""

import frappe
from frappe import _
from frappe.utils import flt, getdate


def execute(filters=None):
	filters = frappe._dict(filters or {})
	if not filters.from_date or not filters.to_date:
		frappe.throw(_("Set both From Date and To Date."))
	if getdate(filters.from_date) > getdate(filters.to_date):
		frappe.throw(_("From Date must be before To Date."))
	rows = _rows(filters)
	return _columns(), rows, None, _chart(rows)


def _columns():
	return [
		{"label": _("مركز التكلفة"), "fieldname": "cost_center", "fieldtype": "Link", "options": "Cost Center", "width": 240},
		{"label": _("الإيراد"), "fieldname": "income", "fieldtype": "Currency", "width": 130},
		{"label": _("المصروف"), "fieldname": "expense", "fieldtype": "Currency", "width": 130},
		{"label": _("الصافي"), "fieldname": "net", "fieldtype": "Currency", "width": 130},
		{"label": _("الهامش %"), "fieldname": "margin", "fieldtype": "Percent", "width": 100},
	]


def _rows(filters):
	conditions = ""
	values = {"company": filters.company, "from_date": filters.from_date, "to_date": filters.to_date}
	if filters.cost_center:
		conditions = " AND gle.cost_center = %(cost_center)s"
		values["cost_center"] = filters.cost_center
	data = frappe.db.sql(
		f"""
		SELECT gle.cost_center,
			SUM(CASE WHEN acc.root_type = 'Income' THEN gle.credit - gle.debit ELSE 0 END) AS income,
			SUM(CASE WHEN acc.root_type = 'Expense' THEN gle.debit - gle.credit ELSE 0 END) AS expense
		FROM `tabGL Entry` gle
		JOIN `tabAccount` acc ON acc.name = gle.account
		WHERE gle.is_cancelled = 0 AND gle.company = %(company)s
			AND gle.posting_date BETWEEN %(from_date)s AND %(to_date)s
			AND acc.root_type IN ('Income', 'Expense')
			AND IFNULL(gle.cost_center, '') != '' {conditions}
		GROUP BY gle.cost_center
		ORDER BY gle.cost_center
		""",
		values,
		as_dict=True,
	)
	for row in data:
		row.income, row.expense = flt(row.income), flt(row.expense)
		row.net = row.income - row.expense
		row.margin = (row.net / row.income * 100) if row.income else 0
	return data


def _chart(rows):
	return {
		"data": {
			"labels": [r.cost_center for r in rows],
			"datasets": [
				{"name": _("الإيراد"), "values": [r.income for r in rows]},
				{"name": _("المصروف"), "values": [r.expense for r in rows]},
			],
		},
		"type": "bar",
	}
