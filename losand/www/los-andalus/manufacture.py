import frappe


def get_context(context):
	context.no_cache = 1
	context.lang = frappe.local.lang or "ar"
	context.site_name = frappe.local.site
	context.csrf_token = frappe.sessions.get_csrf_token()
	currency = frappe.db.get_single_value("Global Defaults", "default_currency") or "LYD"
	symbol = frappe.db.get_value("Currency", currency, "symbol") or currency
	factory_name = frappe.db.get_single_value("Los Andalus Manufacture Settings", "factory_name") or "مصنع الغذاء الحديث"
	context.boot = {
		"user": frappe.session.user,
		"lang": context.lang,
		"currency": currency,
		"currency_symbol": symbol,
		"factory_name": factory_name,
	}
