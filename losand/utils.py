import frappe


def portal_lang():
	"""The POS and manufacturing portals are Arabic: answer their API calls (and so every
	error message) in Arabic whatever language the Desk user chose."""
	if frappe.request and frappe.request.path.startswith("/api/method/losand.api."):
		frappe.local.lang = "ar"
