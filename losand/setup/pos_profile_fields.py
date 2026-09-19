"""Add the POS waste picker to the standard ERPNext POS Profile.

The POS Profile stays the single source of truth for the register (see
losand/api/pos.py), so the one list that decides WHICH items a branch screen shows
lives on it too rather than in a separate settings doctype:

  - losand_waste_items — ready items written off as الهالك

The other two screens need no picker: receiving (استلام الطلبات) lists the draft
Material Transfers addressed to the profile's warehouse, and the end-of-day count
(الجرد اليومي) lists whatever that warehouse holds. Waste stays opt-in because it
is not a count of the shelf — it is a short list of what a branch is allowed to
declare as spoiled.

It is a plain `Table` grid, NOT a `Table MultiSelect`. That is load-bearing: the
link control applies `this.df.link_filters` (frappe link.js), and for a Table
MultiSelect `this.df` is the PARENT field — so the child link field's filter to
is_final_product is silently ignored and the picker offers every Item. A grid
builds its row controls from the child's own docfields (frappe grid_row.js), so
the filter applies.

Leaving the list EMPTY shows NOTHING on the waste screen. (This is deliberately
NOT how the profile's own item_groups behave.)

Runs automatically on `bench migrate` (see hooks.after_migrate). Idempotent.

Run manually:
    bench --site <site> execute losand.setup.pos_profile_fields.run
"""

import frappe

WASTE_FIELD = "losand_waste_items"

# Pickers that used to drive a screen and no longer do: receiving reads draft
# transfers, the count sheet reads the branch warehouse. Deleted on migrate so an
# installed site does not keep offering a list nothing reads.
DROPPED_FIELDS = ("losand_receiving_items", "losand_stocktake_items")
DROPPED_DOCTYPES = ("Los Andalus POS Receiving Item", "Los Andalus POS Stocktake Item")


def run():
	from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

	create_custom_fields(
		{
			"POS Profile": [
				{
					# fieldname kept from when this section held the stocktake list —
					# renaming it would orphan the installed Custom Field for no gain.
					"fieldname": "losand_stocktake_section",
					"label": "Los Andalus — Item Lists",
					"fieldtype": "Section Break",
					"insert_after": "hide_unavailable_items",
					"collapsible": 0,
				},
				{
					"fieldname": WASTE_FIELD,
					"label": "Waste Items (Ready Products)",
					"fieldtype": "Table",
					"options": "Los Andalus POS Waste Item",
					"insert_after": "losand_stocktake_section",
					"description": "Ready products that can be written off as waste (الهالك). Leave empty and the waste table shows nothing.",
				},
			]
		},
		ignore_validate=True,
	)
	for fieldname in DROPPED_FIELDS:
		name = frappe.db.get_value("Custom Field", {"dt": "POS Profile", "fieldname": fieldname})
		if name:
			frappe.delete_doc("Custom Field", name, ignore_permissions=True)
	for doctype in DROPPED_DOCTYPES:
		if frappe.db.exists("DocType", doctype):
			frappe.delete_doc("DocType", doctype, ignore_permissions=True, force=True)
	frappe.db.commit()
	return {"fields": [WASTE_FIELD]}
