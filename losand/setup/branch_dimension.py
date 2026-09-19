"""Make `Branch` an Accounting Dimension and let a POS Profile name its branch.

Every branch figure the reports need — revenue, payments, stock issued — is already
a Sales Invoice or a Stock Entry. Tagging those documents with a dimension is what
turns them into per-branch numbers, in our report AND in ERPNext's own (Trial
Balance, P&L, GL all group by dimension). So the branch is not a column we invent:
it is the standard ERPNext dimension over the standard `Branch` doctype.

Creating the Accounting Dimension is what installs the `branch` Link field on every
accounting doctype (erpnext make_dimension_in_accounting_doctypes) — we never create
those fields ourselves. What we add is `losand_branch` on POS Profile: the POS knows
which branch it is, and losand/api/pos.py stamps that value on the documents it
submits (see _branch_dimension).

Runs automatically on `bench migrate` (see hooks.after_migrate). Idempotent.

Run manually:
    bench --site <site> execute losand.setup.branch_dimension.run
"""

import frappe

DIMENSION_DOCTYPE = "Branch"
PROFILE_FIELD = "losand_branch"


def run():
	from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

	created = False
	if not frappe.db.exists("Accounting Dimension", {"document_type": DIMENSION_DOCTYPE}):
		dimension = frappe.new_doc("Accounting Dimension")
		dimension.document_type = DIMENSION_DOCTYPE
		dimension.insert(ignore_permissions=True)  # installs the `branch` field everywhere
		created = True

	create_custom_fields(
		{
			"POS Profile": [
				{
					"fieldname": PROFILE_FIELD,
					"label": "Branch",
					"fieldtype": "Link",
					"options": DIMENSION_DOCTYPE,
					"insert_after": "warehouse",
					"description": "Branch stamped on every Sales Invoice and Stock Entry this POS submits — the accounting dimension the branch reports group by.",
				}
			]
		},
		ignore_validate=True,
	)
	frappe.db.commit()
	return {"dimension_created": created, "field": PROFILE_FIELD}
