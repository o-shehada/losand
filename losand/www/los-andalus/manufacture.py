import json

import frappe


def get_context(context):
	context.no_cache = 1
	context.lang = frappe.local.lang or "ar"
	context.site_name = frappe.local.site
	context.boot = {
		"user": frappe.session.user,
		"lang": context.lang,
	}
	context.boot_json = json.dumps(context.boot)
