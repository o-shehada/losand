import frappe
import pytest

from losand.api.manufacture import get_current_session, save_food_logger_batch


def test_get_current_session_returns_user():
	session = get_current_session()
	assert "user" in session
	assert "authenticated" in session


def test_save_food_logger_batch_requires_login():
	frappe.set_user("Guest")
	with pytest.raises(frappe.PermissionError):
		save_food_logger_batch({"producedQty": 10}, {"totalCost": 50, "unitCost": 5})


def test_save_food_logger_batch_returns_confirmation():
	frappe.set_user("Administrator")
	result = save_food_logger_batch(
		{"batchRef": "#B-TEST", "product": "Beef Burger", "producedQty": 10},
		{"totalCost": 50, "unitCost": 5},
	)
	assert result["batchRef"] == "#B-TEST"
	assert result["product"] == "Beef Burger"
	assert result["producedQty"] == 10
	assert result["totalCost"] == 50
	assert result["unitCost"] == 5
	assert result["savedBy"] == "Administrator"
