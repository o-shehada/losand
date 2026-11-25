import frappe


def portal_lang():
	"""The POS and manufacturing portals are Arabic: answer their API calls (and so every
	error message) in Arabic whatever language the Desk user chose."""
	if frappe.request and frappe.request.path.startswith("/api/method/losand.api."):
		frappe.local.lang = "ar"


def _as_system(doc, action):
	"""Run doc.submit() / doc.cancel() as the system user, then restore the real one.

	ERPNext's stock and invoice submit create Serial and Batch Bundles and similar
	records as the *current user*, so portal-only roles (cashier, supervisor) are refused
	by ERPNext's own permissions. The document is still created, and so owned, by the real
	user; callers authorise the action themselves (role / profile / workbench checks)."""
	user = frappe.session.user
	frappe.set_user("Administrator")
	try:
		getattr(doc, action)()
	finally:
		frappe.set_user(user)


def submit_as_system(doc):
	_as_system(doc, "submit")


def cancel_as_system(doc):
	_as_system(doc, "cancel")
