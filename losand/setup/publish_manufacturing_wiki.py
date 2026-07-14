"""Publish the Arabic manufacturing manual into the installed Frappe Wiki app.

Runs automatically on `bench migrate` (see hooks.after_migrate), after
losand.setup.upload_wiki_images.run has uploaded the screenshots the manual
embeds. Safe to call repeatedly: pages are matched and updated by route
instead of duplicated.

Run manually:
    bench --site <site> execute losand.setup.publish_manufacturing_wiki.run
"""

from pathlib import Path

import frappe


PAGES = [
	("01-overview.md", "دليل نظام التصنيع", "manufacturing", "نظام التصنيع"),
	("02-roles-access.md", "الصلاحيات والوصول", "manufacturing/roles-access", "نظام التصنيع"),
	("03-daily-operation.md", "تشغيل دفعة إنتاج خطوة بخطوة", "manufacturing/daily-operation", "دليل الاستخدام"),
	("04-cost-stock.md", "التكلفة وحركات المخزون", "manufacturing/cost-stock", "دليل الاستخدام"),
	("05-master-data.md", "إعداد البيانات الأساسية", "manufacturing/master-data", "الإدارة والإعداد"),
	("06-audit-reporting.md", "الدفعات والتدقيق والتقارير", "manufacturing/audit-reporting", "الإدارة والإعداد"),
	("07-troubleshooting.md", "استكشاف الأخطاء ومعالجتها", "manufacturing/troubleshooting", "الدعم"),
	("08-checklists.md", "قوائم التحقق وقاموس الحقول", "manufacturing/checklists", "الدعم"),
]


def _manual_dir():
	return Path(__file__).resolve().parents[2] / "docs" / "wiki" / "manufacturing"


def run(space_route="wiki"):
	"""Create or update the manual pages and add them to an existing Wiki Space."""
	if "wiki" not in frappe.get_installed_apps():
		return {"space": None, "pages": []}

	space_name = frappe.db.get_value("Wiki Space", {"route": space_route}, "name")
	if space_name:
		space = frappe.get_doc("Wiki Space", space_name)
	else:
		# The Wiki app normally creates the default "wiki" space on its own
		# install; create it here too so migrate order can't strand this page set.
		space = frappe.get_doc({"doctype": "Wiki Space", "route": space_route}).insert(ignore_permissions=True)
	sidebar_by_page = {row.wiki_page: row for row in space.wiki_sidebars}
	routes = []

	for filename, title, suffix, group in PAGES:
		route = f"{space_route}/{suffix}"
		content = (_manual_dir() / filename).read_text(encoding="utf-8")
		page_name = frappe.db.get_value("Wiki Page", {"route": route}, "name")
		if page_name:
			page = frappe.get_doc("Wiki Page", page_name)
			page.title = title
			page.content = content
			page.published = 1
			page.allow_guest = 0
			page.meta_description = f"دليل استخدام نظام التصنيع: {title}"
			page.meta_keywords = "التصنيع, الإنتاج, المخزون, ERPNext, الأندلس"
			page.save(ignore_permissions=True)
		else:
			page = frappe.get_doc(
				{
					"doctype": "Wiki Page",
					"title": title,
					"route": route,
					"content": content,
					"published": 1,
					"allow_guest": 0,
					"meta_description": f"دليل استخدام نظام التصنيع: {title}",
					"meta_keywords": "التصنيع, الإنتاج, المخزون, ERPNext, الأندلس",
				}
			).insert(ignore_permissions=True)

		if page.name in sidebar_by_page:
			sidebar_by_page[page.name].parent_label = group
			sidebar_by_page[page.name].hide_on_sidebar = 0
		else:
			space.append(
				"wiki_sidebars",
				{"wiki_page": page.name, "parent_label": group, "hide_on_sidebar": 0},
			)
		routes.append(route)

	space.space_name = space.space_name or "دليل الأندلس"
	space.save(ignore_permissions=True)
	frappe.db.commit()
	return {"space": space_route, "pages": routes}
