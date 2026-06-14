import frappe
import pytest

from losand.api.manufacture import cfg, get_current_session, get_raw_materials, submit_batch


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


def test_get_raw_materials_shape():
	rms = get_raw_materials()
	assert isinstance(rms, list)
	if rms:
		first = rms[0]
		for key in ("item_code", "name_ar", "unit", "rate", "available_qty"):
			assert key in first


def test_submit_batch_requires_login():
	frappe.set_user("Guest")
	with pytest.raises(frappe.PermissionError):
		submit_batch({"variant": "X", "producedQty": 1})
	frappe.set_user("Administrator")
