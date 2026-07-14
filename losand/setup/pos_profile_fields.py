"""Add the POS screen item pickers to the standard ERPNext POS Profile.

The POS Profile stays the single source of truth for the register (see
losand/api/pos.py), so the lists that decide WHICH items each branch screen shows
live on it too rather than in a separate settings doctype:

  - losand_stocktake_items — raw materials counted on الجرد اليومي
  - losand_waste_items     — ready items written off as الهالك
  - losand_receiving_items — raw materials offered on استلام الطلبات

Each has its OWN child doctype rather than a shared one, because the item filter
lives on the child's link field: the stocktake/receiving pickers only offer Items
flagged is_raw_material, the waste picker only is_final_product.

All three are plain `Table` grids, NOT `Table MultiSelect`. That is load-bearing:
the link control applies `this.df.link_filters` (frappe link.js), and for a Table
MultiSelect `this.df` is the PARENT field — so the child link field's filters are
silently ignored and the picker offers every Item. A grid builds its row controls
from the child's own docfields (frappe grid_row.js), so the filters apply.

Leaving a list EMPTY shows NOTHING on that screen — the lists are opt-in per branch,
so an unconfigured profile gets an empty screen instead of every item in the
warehouse. (This is deliberately NOT how the profile's own item_groups behave.)

Runs automatically on `bench migrate` (see hooks.after_migrate). Idempotent.

Run manually:
    bench --site <site> execute losand.setup.pos_profile_fields.run
"""

import frappe

STOCKTAKE_FIELD = "losand_stocktake_items"
WASTE_FIELD = "losand_waste_items"
RECEIVING_FIELD = "losand_receiving_items"


def run():
	from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

	create_custom_fields(
		{
			"POS Profile": [
				{
					# fieldname kept from when this section only held the stocktake list —
					# renaming it would orphan the installed Custom Field for no gain.
					"fieldname": "losand_stocktake_section",
					"label": "Los Andalus — Item Lists",
					"fieldtype": "Section Break",
					"insert_after": "hide_unavailable_items",
					"collapsible": 1,
				},
				{
					"fieldname": STOCKTAKE_FIELD,
					"label": "Stocktake Items (Raw Materials)",
					"fieldtype": "Table",
					"options": "Los Andalus POS Stocktake Item",
					"insert_after": "losand_stocktake_section",
					"description": "Raw materials counted in the daily stocktake (الجرد اليومي). Leave empty and the stocktake table shows nothing.",
				},
				{
					"fieldname": WASTE_FIELD,
					"label": "Waste Items (Ready Products)",
					"fieldtype": "Table",
					"options": "Los Andalus POS Waste Item",
					"insert_after": STOCKTAKE_FIELD,
					"description": "Ready products that can be written off as waste (الهالك). Leave empty and the waste table shows nothing.",
				},
				{
					"fieldname": RECEIVING_FIELD,
					"label": "Receiving Items (Raw Materials)",
					"fieldtype": "Table",
					"options": "Los Andalus POS Receiving Item",
					"insert_after": WASTE_FIELD,
					"description": "Raw materials offered on the goods receipt screen (استلام الطلبات). Leave empty and the receiving picker shows nothing.",
				},
			]
		},
		ignore_validate=True,
	)
	frappe.db.commit()
	return {"fields": [STOCKTAKE_FIELD, WASTE_FIELD, RECEIVING_FIELD]}
