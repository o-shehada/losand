import os
import re

import frappe

# The Vite build (frappeui buildConfig) injects the hashed asset tags into the
# sibling manufacture.html only. The POS portal rides the same bundle, so we
# read those tags back out at render time — they stay in sync on every rebuild.
# Match the hashed Vite bundle directly (the head also carries a Font Awesome
# stylesheet link, so we key off the index-<hash> filename, not the tag).
_ASSET_RE = {
	"js": re.compile(r'src="([^"]*index-[\w-]+\.js)"'),
	"css": re.compile(r'href="([^"]*index-[\w-]+\.css)"'),
}


def _built_assets():
	path = os.path.join(os.path.dirname(__file__), "manufacture.html")
	try:
		with open(path, encoding="utf-8") as f:
			html = f.read()
	except OSError:
		return "", ""
	js = _ASSET_RE["js"].search(html)
	css = _ASSET_RE["css"].search(html)
	return (js.group(1) if js else ""), (css.group(1) if css else "")


def get_context(context):
	context.no_cache = 1
	context.lang = frappe.local.lang or "ar"
	context.site_name = frappe.local.site
	context.csrf_token = frappe.sessions.get_csrf_token()
	context.app_js, context.app_css = _built_assets()
	currency = frappe.db.get_single_value("Global Defaults", "default_currency") or "LYD"
	symbol = frappe.db.get_value("Currency", currency, "symbol") or currency
	factory_name = frappe.db.get_single_value("Los Andalus Manufacture Settings", "factory_name") or "مطعم الأندلس"
	context.boot = {
		"user": frappe.session.user,
		"lang": context.lang,
		"currency": currency,
		"currency_symbol": symbol,
		"factory_name": factory_name,
	}
