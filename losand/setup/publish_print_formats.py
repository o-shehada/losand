"""Publish the Los Andalus Print Formats for POS Sales Invoices.

  - Los Andalus POS Invoice    — the customer receipt (pos_invoice.html)
  - Los Andalus Kitchen Ticket — the no-price prep ticket (kitchen_ticket.html)

Runs automatically on `bench migrate` (see hooks.after_migrate). Safe to call
repeatedly: formats are matched and updated by name instead of duplicated.

Run manually:
    bench --site <site> execute losand.setup.publish_print_formats.run
"""

from pathlib import Path

import frappe

FORMAT_NAME = "Los Andalus Kitchen Ticket"
RECEIPT_FORMAT_NAME = "Los Andalus POS Invoice"

# Print Format name -> template file sitting next to this module.
FORMATS = {
	RECEIPT_FORMAT_NAME: "pos_invoice.html",
	FORMAT_NAME: "kitchen_ticket.html",
}


def _html(filename):
	return (Path(__file__).resolve().parent / filename).read_text(encoding="utf-8")


def _publish(name, filename):
	if frappe.db.exists("Print Format", name):
		doc = frappe.get_doc("Print Format", name)
	else:
		doc = frappe.new_doc("Print Format")
		doc.name = name  # Print Format autonames by prompt (the name IS the label)

	doc.doc_type = "Sales Invoice"
	doc.print_format_type = "Jinja"
	doc.custom_format = 1  # without this Frappe ignores `html` and auto-renders the standard layout
	doc.html = _html(filename)
	doc.disabled = 0
	doc.standard = "No"

	if doc.is_new():
		doc.insert(ignore_permissions=True)
	else:
		doc.save(ignore_permissions=True)
	return doc.name


def run():
	names = [_publish(name, filename) for name, filename in FORMATS.items()]
	frappe.db.commit()
	return {"names": names}
