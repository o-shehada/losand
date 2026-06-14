"""Phase-0 Manufacturing scaffold for Los Andalus.

Creates, idempotently:
  - raw-material Items (Raw Material group)
  - a "Weight" Item Attribute
  - a `custom_is_default_variant` Check field on Item
  - 3 template Items (has_variants) + their weight variants (Nos, with Weight Per Unit)
  - one per-piece BOM per variant (PLACEHOLDER recipes — refine in ERPNext Desk)

Run with:
    bench --site <site> execute losand.setup.manufacture_scaffold.run
"""

import frappe

COMPANY = "Los Andalus"
WEIGHT_UOM = "جم"          # gram
FG_GROUP = "Products"
RM_GROUP = "Raw Material"
ARABIC_UOMS = ["كجم", "حبة", "جم", "لتر"]

# code, name_ar, name_en, stock_uom, valuation_rate
RAW_MATERIALS = [
	("RM-BEEF-MINCE", "لحم بقري مفروم", "Beef Mince 80/20", "كجم", 45),
	("RM-CHICKEN-MINCE", "دجاج مفروم", "Chicken Mince", "كجم", 30),
	("RM-FRESH-EGGS", "بيض طازج", "Fresh Eggs", "حبة", 0.75),
	("RM-SPICES", "بهارات وتوابل", "Spices & Seasoning", "جم", 0.12),
	("RM-VEG-OIL", "زيت نباتي", "Vegetable Oil", "لتر", 8.5),
	("RM-BREAD-CRUMBS", "فتات الخبز", "Bread Crumbs", "كجم", 12),
	("RM-FLOUR", "دقيق", "Flour", "كجم", 3),
]

WEIGHT_VALUES = ["70g", "80g", "120g", "150g", "200g"]

# code, name_ar, weights, default weight, recipe kind
TEMPLATES = [
	{"code": "Chicken Burger", "name": "برجر دجاج", "weights": ["150g", "200g"], "default": "200g", "kind": "chicken"},
	{"code": "Beef Burger", "name": "برجر لحم", "weights": ["120g", "150g"], "default": "120g", "kind": "beef"},
	{"code": "Burger Buns", "name": "خبز البرجر", "weights": ["70g", "80g"], "default": "80g", "kind": "buns"},
]


def _ensure_uoms():
	for u in ARABIC_UOMS:
		if not frappe.db.exists("UOM", u):
			frappe.get_doc({"doctype": "UOM", "uom_name": u}).insert(ignore_permissions=True)


def _ensure_raw_materials():
	for code, name_ar, name_en, uom, rate in RAW_MATERIALS:
		if frappe.db.exists("Item", code):
			continue
		frappe.get_doc(
			{
				"doctype": "Item",
				"item_code": code,
				"item_name": name_ar,
				"description": name_en,
				"item_group": RM_GROUP,
				"stock_uom": uom,
				"is_stock_item": 1,
				"valuation_rate": rate,
			}
		).insert(ignore_permissions=True)


def _ensure_weight_attribute():
	if not frappe.db.exists("Item Attribute", "Weight"):
		frappe.get_doc(
			{
				"doctype": "Item Attribute",
				"attribute_name": "Weight",
				"item_attribute_values": [
					{"attribute_value": w, "abbr": w.upper()} for w in WEIGHT_VALUES
				],
			}
		).insert(ignore_permissions=True)
		return
	doc = frappe.get_doc("Item Attribute", "Weight")
	existing = {r.attribute_value for r in doc.item_attribute_values}
	changed = False
	for w in WEIGHT_VALUES:
		if w not in existing:
			doc.append("item_attribute_values", {"attribute_value": w, "abbr": w.upper()})
			changed = True
	if changed:
		doc.save(ignore_permissions=True)


def _ensure_custom_field():
	if not frappe.db.exists("Custom Field", "Item-custom_is_default_variant"):
		frappe.get_doc(
			{
				"doctype": "Custom Field",
				"dt": "Item",
				"fieldname": "custom_is_default_variant",
				"label": "Default Production Variant",
				"fieldtype": "Check",
				"insert_after": "variant_of",
			}
		).insert(ignore_permissions=True)
		frappe.clear_cache(doctype="Item")


def _ensure_template(t):
	if frappe.db.exists("Item", t["code"]):
		return
	frappe.get_doc(
		{
			"doctype": "Item",
			"item_code": t["code"],
			"item_name": t["name"],
			"item_group": FG_GROUP,
			"stock_uom": "Nos",
			"is_stock_item": 1,
			"has_variants": 1,
			"attributes": [{"attribute": "Weight"}],
		}
	).insert(ignore_permissions=True)


def _ensure_variant(t, weight):
	from erpnext.controllers.item_variant import create_variant, get_variant

	weight_g = int(weight.rstrip("g"))
	is_default = 1 if weight == t["default"] else 0

	code = get_variant(t["code"], {"Weight": weight})
	if code:
		frappe.db.set_value("Item", code, "custom_is_default_variant", is_default)
		return code

	v = create_variant(t["code"], {"Weight": weight})
	v.item_group = FG_GROUP
	v.stock_uom = "Nos"
	v.is_stock_item = 1
	v.weight_per_unit = weight_g
	v.weight_uom = WEIGHT_UOM
	v.custom_is_default_variant = is_default
	v.insert(ignore_permissions=True)
	return v.name


def _recipe(kind, weight_g):
	"""PLACEHOLDER per-piece recipe (qty in each material's stock UOM)."""
	if kind == "beef":
		return [
			("RM-BEEF-MINCE", round(weight_g * 0.9 / 1000, 3), "كجم"),
			("RM-SPICES", 4, "جم"),
			("RM-VEG-OIL", 0.01, "لتر"),
			("RM-BREAD-CRUMBS", 0.02, "كجم"),
			("RM-FRESH-EGGS", 0.1, "حبة"),
		]
	if kind == "chicken":
		return [
			("RM-CHICKEN-MINCE", round(weight_g * 0.9 / 1000, 3), "كجم"),
			("RM-SPICES", 4, "جم"),
			("RM-VEG-OIL", 0.01, "لتر"),
			("RM-BREAD-CRUMBS", 0.02, "كجم"),
			("RM-FRESH-EGGS", 0.1, "حبة"),
		]
	# buns
	return [
		("RM-FLOUR", round(weight_g * 0.7 / 1000, 3), "كجم"),
		("RM-FRESH-EGGS", 0.05, "حبة"),
		("RM-VEG-OIL", 0.005, "لتر"),
	]


def _ensure_bom(variant_code, kind, weight_g):
	if frappe.db.exists("BOM", {"item": variant_code, "is_active": 1, "docstatus": 1}):
		return
	bom = frappe.new_doc("BOM")
	bom.item = variant_code
	bom.company = COMPANY
	bom.quantity = 1
	bom.is_active = 1
	bom.is_default = 1
	bom.rate_of_materials_based_on = "Valuation Rate"
	for code, qty, uom in _recipe(kind, weight_g):
		bom.append("items", {"item_code": code, "qty": qty, "uom": uom})
	bom.insert(ignore_permissions=True)
	bom.submit()


def _ensure_manufacturing_settings():
	# Consume what was actually transferred to WIP (so operator's actual quantities drive cost),
	# not the BOM-planned amounts.
	frappe.db.set_single_value(
		"Manufacturing Settings",
		"backflush_raw_materials_based_on",
		"Material Transferred for Manufacture",
	)


def _ensure_link_back_fields():
	# Reverse link so the Production Batch "Connections" tab can group its WO + Stock Entries.
	for dt in ("Work Order", "Stock Entry"):
		fid = f"{dt}-custom_production_batch"
		if not frappe.db.exists("Custom Field", fid):
			frappe.get_doc(
				{
					"doctype": "Custom Field",
					"dt": dt,
					"fieldname": "custom_production_batch",
					"label": "Production Batch",
					"fieldtype": "Link",
					"options": "Los Andalus Production Batch",
					"insert_after": "company",
					"read_only": 1,
					"no_copy": 1,
				}
			).insert(ignore_permissions=True)


def _ensure_roles():
	for role in ("Manufacture Operator", "Manufacture Supervisor"):
		if not frappe.db.exists("Role", role):
			frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 1}).insert(
				ignore_permissions=True
			)


def _ensure_app_settings():
	s = frappe.get_single("Los Andalus Manufacture Settings")
	defaults = {
		"company": COMPANY,
		"factory_name": "مصنع الغذاء الحديث",
		"raw_material_group": RM_GROUP,
		"source_warehouse": "Stores - LA",
		"wip_warehouse": "Work In Progress - LA",
		"fg_warehouse": "Finished Goods - LA",
	}
	changed = False
	for field, value in defaults.items():
		if not s.get(field):
			s.set(field, value)
			changed = True
	if changed:
		s.save(ignore_permissions=True)


def run():
	_ensure_manufacturing_settings()
	_ensure_roles()
	_ensure_link_back_fields()
	_ensure_app_settings()
	_ensure_uoms()
	_ensure_raw_materials()
	_ensure_weight_attribute()
	_ensure_custom_field()

	variants = []
	for t in TEMPLATES:
		_ensure_template(t)
		for w in t["weights"]:
			code = _ensure_variant(t, w)
			_ensure_bom(code, t["kind"], int(w.rstrip("g")))
			variants.append(code)

	frappe.db.commit()
	summary = {
		"raw_materials": frappe.db.count("Item", {"item_group": RM_GROUP}),
		"templates": frappe.db.count("Item", {"has_variants": 1}),
		"variants": variants,
		"boms": frappe.db.count("BOM", {"docstatus": 1}),
	}
	print("SCAFFOLD_DONE", frappe.as_json(summary))
	return summary
