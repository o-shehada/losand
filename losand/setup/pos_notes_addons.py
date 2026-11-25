"""Add-on restriction field on Item + seed the free kitchen notes.

- Item.losand_addon_groups: Item Groups (one per line) an add-on may be sold with.
  Empty = any item (today's behaviour).
- Los Andalus Kitchen Note: the free notes the POS used to hard-code; seeded once.

Idempotent; runs on `bench migrate` (hooks.after_migrate).
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

SEED_NOTES = ["بدون كاتشب", "بدون مايونيز", "بدون بصل", "بدون بيض", "بدون خس", "خبز محمص"]


def run():
	create_custom_fields(
		{
			"Item": [
				{
					"fieldname": "losand_addon_groups",
					"label": "Add-on Allowed Item Groups",
					"fieldtype": "Small Text",
					"insert_after": "item_group",
					"depends_on": "eval:doc.item_group=='POS Add-ons'",
					"description": "One Item Group per line. This add-on is offered only on items of these groups. Empty = any item.",
				}
			]
		}
	)
	if not frappe.db.count("Los Andalus Kitchen Note"):
		for note in SEED_NOTES:
			frappe.get_doc({"doctype": "Los Andalus Kitchen Note", "note": note, "enabled": 1}).insert(ignore_permissions=True)
