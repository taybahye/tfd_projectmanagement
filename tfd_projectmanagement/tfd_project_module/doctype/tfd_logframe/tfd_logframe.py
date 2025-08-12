# Copyright (c) 2024, Amd Oudah Prosite  and contributors
# For license information, please see license.txt

import frappe
from frappe.utils.nestedset import NestedSet


class TFDLogframe(NestedSet):
	def validate(self):
			if self.target and self.target != 0:
				self.achievement_percentage = round((self.acheivement / self.target) * 100, 2)
			else:
				self.achievement_percentage = 0
