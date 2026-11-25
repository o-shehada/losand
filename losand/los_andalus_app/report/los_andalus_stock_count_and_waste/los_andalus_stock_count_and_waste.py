"""Daily stock count result and waste (الهالك) per branch.

Count figures come from the Los Andalus Stocktake records. Waste is the هالك Material
Issues posted out of the branch's POS warehouse (api/pos.py save_waste).
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
		{"label": _("التاريخ"), "fieldname": "date", "fieldtype": "Date", "width": 95},
		{"label": _("نقطة البيع"), "fieldname": "pos_profile", "fieldtype": "Link", "options": "POS Profile", "width": 130},
		{"label": _("الفرع"), "fieldname": "branch", "fieldtype": "Link", "options": "Branch", "width": 110},
		{"label": _("عدد الجرود"), "fieldname": "counts", "fieldtype": "Int", "width": 90},
		{"label": _("أصناف مجرودة"), "fieldname": "counted_items", "fieldtype": "Int", "width": 110},
		{"label": _("أصناف بفرق"), "fieldname": "variance_items", "fieldtype": "Int", "width": 100},
		{"label": _("قيمة النقص"), "fieldname": "shortage", "fieldtype": "Currency", "width": 110},
		{"label": _("قيمة الزيادة"), "fieldname": "surplus", "fieldtype": "Currency", "width": 110},
		{"label": _("قيمة الهالك"), "fieldname": "waste", "fieldtype": "Currency", "width": 110},
		{"label": _("إجمالي الفاقد"), "fieldname": "loss", "fieldtype": "Currency", "width": 120},
	]


def _rows(filters):
	profile_cond, values = "", {"from_date": filters.from_date, "to_date": filters.to_date}
	if filters.pos_profile:
		profile_cond = " AND pos_profile = %(pos_profile)s"
		values["pos_profile"] = filters.pos_profile

	profiles = {
		p.name: p
		for p in frappe.get_all("POS Profile", fields=["name", "warehouse", "losand_branch"])
		if not filters.pos_profile or p.name == filters.pos_profile
	}
	rows = {}

	def row(date, profile):
		p = profiles.get(profile)
		return rows.setdefault(
			(str(date), profile),
			frappe._dict(date=date, pos_profile=profile, branch=p.losand_branch if p else None, counts=0,
				counted_items=0, variance_items=0, shortage=0, surplus=0, waste=0),
		)

	for s in frappe.db.sql(
		f"""
		SELECT DATE(creation) AS date, pos_profile, COUNT(*) AS counts, SUM(counted_items) AS counted_items,
			SUM(variance_items) AS variance_items, SUM(shortage_value) AS shortage, SUM(surplus_value) AS surplus
		FROM `tabLos Andalus Stocktake`
		WHERE DATE(creation) BETWEEN %(from_date)s AND %(to_date)s {profile_cond}
		GROUP BY DATE(creation), pos_profile
		""",
		values,
		as_dict=True,
	):
		r = row(s.date, s.pos_profile)
		r.counts, r.counted_items, r.variance_items = s.counts, s.counted_items, s.variance_items
		r.shortage, r.surplus = flt(s.shortage), flt(s.surplus)

	for name, p in profiles.items():
		if not p.warehouse:
			continue
		for w in frappe.db.sql(
			"""
			SELECT DATE(creation) AS date, SUM(total_amount) AS value
			FROM `tabStock Entry`
			WHERE docstatus = 1 AND purpose = 'Material Issue' AND from_warehouse = %(wh)s
				AND remarks LIKE %(remark)s AND remarks NOT LIKE 'هالك إنتاج%%' AND DATE(creation) BETWEEN %(from_date)s AND %(to_date)s
			GROUP BY DATE(creation)
			""",
			{"wh": p.warehouse, "remark": "هالك%", **values},
			as_dict=True,
		):
			row(w.date, name).waste = flt(w.value)

	out = sorted(rows.values(), key=lambda r: (str(r.date), r.pos_profile or ""), reverse=True)
	for r in out:
		r.loss = r.shortage - r.surplus + r.waste
	return out


def _chart(rows):
	by_profile = {}
	for r in rows:
		by_profile[r.pos_profile] = by_profile.get(r.pos_profile, 0) + flt(r.loss)
	return {
		"data": {"labels": list(by_profile), "datasets": [{"name": _("إجمالي الفاقد"), "values": list(by_profile.values())}]},
		"type": "bar",
	}
