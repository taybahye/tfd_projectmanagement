# Copyright (c) 2025, Amd Oudah Prosite  and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class IndicatorCollectedData(Document):
	@frappe.whitelist()
	def get_logframe_details(self):
		parent_name = self.indicator_logframe 

		data = frappe.db.sql("""
			SELECT 
				log.name as child_name,
				log.type,
				logp.logframe_name
			FROM `tabTFD Logframe child` log
			JOIN `tabTFD Logframe` logp 
				ON log.parent = logp.name
			WHERE logp.name = %s
		""", (parent_name,), as_dict=True)

		return data



	def validate(self):
		self.generate_summary()

	def generate_summary(self):
		self.aggregated_data = []

		summary = {}

		for row in self.collecting_data:
			type_name = row.type

			if type_name not in summary:
				summary[type_name] = {
					"total": 0,
					"last_date": row.date_collected
				}

			# جمع القيم
			summary[type_name]["total"] += row.collected_value or 0

			# تحديث آخر تاريخ
			if row.date_collected and row.date_collected > summary[type_name]["last_date"]:
				summary[type_name]["last_date"] = row.date_collected

		# تعبئة الجدول الجديد aggregated_data
		for type_name, info in summary.items():
			child = self.append("aggregated_data", {})
			child.type = type_name
			child.collected_value = info["total"]
			child.date_collected = info["last_date"]   # ← آخر تاريخ



@frappe.whitelist()
def get_logframe_indicators(logframe_name):
	return frappe.db.sql("""
		SELECT log.name, logc.type , log.indicator_name_en , log.indicator_name_ar
		FROM `tabTFD Logframe` log
		JOIN `tabTFD Logframe child` logc ON log.name = logc.parent
		WHERE log.logframe_name = %s
	""", (logframe_name,), as_dict=True)
