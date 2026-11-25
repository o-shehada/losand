"""One row per production batch: what was produced, what it cost, what was wasted.

Waste (الهالك) is valued at the unit cost of the produced item it was taken from.
"""

import frappe
from frappe import _
from frappe.utils import flt, getdate

BATCH = "Los Andalus Production Batch"


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
		{"label": _("التاريخ"), "fieldname": "date", "fieldtype": "Date", "width": 95},
		{"label": _("الدفعة"), "fieldname": "name", "fieldtype": "Link", "options": BATCH, "width": 110},
		{"label": _("المحطة"), "fieldname": "workbench", "fieldtype": "Link", "options": "Workbench", "width": 150},
		{"label": _("مركز التكلفة"), "fieldname": "cost_center", "fieldtype": "Link", "options": "Cost Center", "width": 190},
		{"label": _("الحالة"), "fieldname": "status", "fieldtype": "Data", "width": 90},
		{"label": _("القطع المنتجة"), "fieldname": "produced", "fieldtype": "Float", "width": 100},
		{"label": _("الوزن (جم)"), "fieldname": "weight", "fieldtype": "Float", "width": 100},
		{"label": _("تكلفة المواد"), "fieldname": "raw_cost", "fieldtype": "Currency", "width": 110},
		{"label": _("تكلفة القطعة"), "fieldname": "unit_cost", "fieldtype": "Currency", "width": 110},
		{"label": _("القطع الهالكة"), "fieldname": "waste_qty", "fieldtype": "Float", "width": 100},
		{"label": _("قيمة الهالك"), "fieldname": "waste_value", "fieldtype": "Currency", "width": 110},
	]


def _rows(filters):
	conditions, values = "", {"from_date": filters.from_date, "to_date": filters.to_date}
	for field in ("workbench", "status"):
		if filters.get(field):
			conditions += f" AND b.{field} = %({field})s"
			values[field] = filters[field]
	data = frappe.db.sql(
		f"""
		SELECT DATE(b.creation) AS date, b.name, b.workbench, b.cost_center, b.status,
			b.total_produced_qty AS produced, b.total_output_weight AS weight,
			b.total_raw_cost AS raw_cost,
			(SELECT IFNULL(SUM(w.qty), 0) FROM `tabLos Andalus Production Waste` w
				WHERE w.parent = b.name) AS waste_qty,
			(SELECT IFNULL(SUM(w.qty * IFNULL(o.unit_cost, 0)), 0)
				FROM `tabLos Andalus Production Waste` w
				LEFT JOIN `tabLos Andalus Production Output` o
					ON o.parent = w.parent AND o.item_code = w.item_code
				WHERE w.parent = b.name) AS waste_value
		FROM `tab{BATCH}` b
		WHERE DATE(b.creation) BETWEEN %(from_date)s AND %(to_date)s {conditions}
		ORDER BY b.creation DESC
		""",
		values,
		as_dict=True,
	)
	for row in data:
		row.unit_cost = flt(row.raw_cost) / flt(row.produced) if flt(row.produced) else 0
	return data


def _chart(rows):
	by_bench = {}
	for r in rows:
		by_bench[r.workbench] = by_bench.get(r.workbench, 0) + flt(r.produced)
	return {
		"data": {"labels": list(by_bench), "datasets": [{"name": _("القطع المنتجة"), "values": list(by_bench.values())}]},
		"type": "bar",
	}
