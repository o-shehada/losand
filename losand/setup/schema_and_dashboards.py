"""Custom fields, Number Cards and Dashboard Charts the app depends on, created from code.

The app ships no fixtures: nothing here is exported site data. Everything is created on
`bench migrate` (hooks.after_migrate) and is idempotent. Custom fields are re-applied each
run; Number Cards and Dashboard Charts are only created when missing, so edits made in the
Desk are kept.
"""

import json

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

CUSTOM_FIELDS = {
	"Item": [
		{"fieldname": "is_final_product", "fieldtype": "Check", "label": "Is Final Product", "insert_after": "stock_uom"},
		{
			"fieldname": "product_category",
			"fieldtype": "Link",
			"label": "Product Category",
			"options": "Product Category",
			"insert_after": "is_final_product",
		},
		{"fieldname": "is_raw_material", "fieldtype": "Check", "label": "Is Raw Material", "insert_after": "product_category"},
		{
			"fieldname": "classification",
			"fieldtype": "Table MultiSelect",
			"label": "Raw Materials",
			"options": "Los Andalus Item Raw Material",
			"insert_after": "product_category",
		},
	],
	"Sales Invoice Item": [
		{
			"fieldname": "losand_kitchen_note",
			"fieldtype": "Small Text",
			"label": "Kitchen Note",
			"insert_after": "description",
			"description": "Free-text prep instructions from POS customization (e.g. no onions) — line-level, shown only on the kitchen ticket.",
		}
	],
	"Sales Invoice": [
		{"fieldname": "losand_pos_request_id", "fieldtype": "Data", "label": "Losand POS Request ID", "insert_after": "po_no"}
	],
	"Stock Entry": [
		{
			"fieldname": "custom_production_batch",
			"fieldtype": "Link",
			"label": "Production Batch",
			"options": "Los Andalus Production Batch",
			"insert_after": "company",
		},
		{
			"fieldname": "custom_workbench",
			"fieldtype": "Link",
			"label": "Workbench",
			"options": "Workbench",
			"insert_after": "custom_production_batch",
		},
	],
}


def _card(label, document_type, function, filters, based_on=None):
	return {
		"doctype": "Number Card",
		"name": label,
		"label": label,
		"type": "Document Type",
		"document_type": document_type,
		"function": function,
		"aggregate_function_based_on": based_on,
		"filters_json": json.dumps(filters),
		"is_public": 1,
		"is_standard": 0,
		"show_percentage_stats": 1,
		"stats_time_interval": "Daily",
	}


BATCH = "Los Andalus Production Batch"
NUMBER_CARDS = [
	_card("LA Batches Today", BATCH, "Count", [[BATCH, "creation", "Timespan", "today"]]),
	_card("LA Total Produced", BATCH, "Sum", [[BATCH, "status", "=", "Completed"]], "total_produced_qty"),
	_card("LA Production Cost", BATCH, "Sum", [[BATCH, "status", "=", "Completed"]], "total_raw_cost"),
	_card("LA FG Stock Value", "Bin", "Sum", [["Bin", "warehouse", "=", "Finished Goods - LA"]], "stock_value"),
]

DASHBOARD_CHARTS = [
	{
		"doctype": "Dashboard Chart",
		"name": "LA Daily Production",
		"chart_name": "LA Daily Production",
		"chart_type": "Sum",
		"document_type": BATCH,
		"based_on": "creation",
		"value_based_on": "total_produced_qty",
		"type": "Bar",
		"timeseries": 1,
		"time_interval": "Daily",
		"timespan": "Last Month",
		"filters_json": "[]",
		"is_public": 1,
		"is_standard": 0,
	},
	{
		"doctype": "Dashboard Chart",
		"name": "LA Batches by Status",
		"chart_name": "LA Batches by Status",
		"chart_type": "Group By",
		"document_type": BATCH,
		"group_by_type": "Count",
		"group_by_based_on": "status",
		"type": "Donut",
		"timeseries": 0,
		"time_interval": "Yearly",
		"timespan": "Last Year",
		"filters_json": "[]",
		"is_public": 1,
		"is_standard": 0,
	},
]


def run():
	create_custom_fields(CUSTOM_FIELDS)
	for doc in NUMBER_CARDS + DASHBOARD_CHARTS:
		if not frappe.db.exists(doc["doctype"], doc["name"]):
			frappe.get_doc(doc).insert(ignore_permissions=True)
