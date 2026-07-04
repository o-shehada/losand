from __future__ import annotations

import frappe
from frappe.model.document import Document


class LosAndalusGiftCard(Document):
	def before_insert(self):
		# A fresh card's balance defaults to its initial value.
		if self.balance in (None, 0) and self.initial_value:
			self.balance = self.initial_value
