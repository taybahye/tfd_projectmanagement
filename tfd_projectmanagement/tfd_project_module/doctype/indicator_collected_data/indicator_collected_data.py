# Copyright (c) 2025, Amd Oudah Prosite  and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class IndicatorCollectedData(Document):
	pass


# Returns all indicators for a given logframe, including child data and parent info
@frappe.whitelist()
def get_logframe_indicators(logframe_name):
	return frappe.db.sql("""
		SELECT log.name,
		 log.old_parent ,
		 logc.type , 
		 logc.baseline,
		 logc.total AS target,
		 log.indicator_name_en ,
		 log.indicator_name_ar , 
		 log.main_order,
			CONCAT(parent.type , ':' ,parent.indicator_name_en, ':\n', IFNULL(parent.indicator_name_ar, '')) AS indicator_parent
		FROM `tabTFD Logframe` log
        LEFT JOIN `tabTFD Logframe child` logc 
            ON log.name = logc.parent
        LEFT JOIN `tabTFD Logframe` parent 
            ON parent.name = log.old_parent
        WHERE log.logframe_name = %s
	""", (logframe_name,), as_dict=True)
