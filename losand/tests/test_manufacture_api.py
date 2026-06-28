import frappe
import pytest

from losand.api.manufacture import (
	_allowed_workbench_names,
	_stock_rows,
	cfg,
	get_category_raw_materials,
	get_current_session,
	submit_batch,
)


def test_get_current_session_returns_flags():
	session = get_current_session()
	assert "user" in session
	assert "authenticated" in session
	assert "can_produce" in session
	assert "can_enter" in session


def test_cfg_resolves_config():
	c = cfg()
	for key in ("company", "source", "wip", "fg", "raw_group", "factory_name"):
		assert c.get(key)


def test_get_category_raw_materials_shape():
	category = frappe.get_all("Product Category", limit=1, pluck="name")
	if not category:
		pytest.skip("No product category configured")
	rms = get_category_raw_materials(category[0])
	assert isinstance(rms, list)
	if rms:
		first = rms[0]
		for key in ("item_code", "name_ar", "unit", "rate", "available_qty"):
			assert key in first


def test_stock_rows_supports_non_batch_items(monkeypatch):
	monkeypatch.setattr(frappe.db, "get_value", lambda *args, **kwargs: 0)
	assert _stock_rows("Eggs", "Raw Materials", 4) == [(None, 4.0)]


def test_allowed_workbenches_are_read_from_staff_assignments(monkeypatch):
	def fake_get_all(doctype, **kwargs):
		assert doctype == "Workbench Staff"
		assert kwargs["filters"]["user"] == "operator@example.com"
		return ["Workbench A"]

	monkeypatch.setattr(frappe, "get_all", fake_get_all)
	assert _allowed_workbench_names("operator@example.com") == ["Workbench A"]
	assert _allowed_workbench_names("Guest") == []


def test_submit_batch_requires_login():
	frappe.set_user("Guest")
	with pytest.raises(frappe.PermissionError):
		submit_batch({"variant": "X", "producedQty": 1})
	frappe.set_user("Administrator")
