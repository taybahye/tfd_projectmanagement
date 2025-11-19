# Copyright (c) 2025, Amd Oudah Prosite  and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class IndicatorCollectedData(Document):
    @frappe.whitelist()
    def get_logframe_details(self):
        parent_name = self.indicator_logframe   # نأتي بقيمة الحقل من نفس الدوكتايب
        
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
