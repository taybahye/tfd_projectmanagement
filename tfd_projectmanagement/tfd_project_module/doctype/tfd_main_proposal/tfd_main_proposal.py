import frappe
from frappe.model.document import Document

class TFDMainProposal(Document):

    # هذه الدالة تعمل عند الحفظ فقط (في السيرفر) فلا تسبب تعليق المتصفح
    def before_save(self):
        # 1. جلب البيانات من الجدول الأول
        info_data = self.get("project_info") or []
        
        # 2. تنظيف الجدول الثاني
        self.set("project_plan", [])

        # 3. نقل البيانات
        for row in info_data:
            self.append("project_plan", {
                "project_name": row.project_name,
                "activity_name": row.activity__name
            })

    @frappe.whitelist()
    def get_staffing(self, staffing_plan):
        return frappe.db.sql("SELECT * FROM `tabStaffing Plan Detail` WHERE parent = %s", (staffing_plan,), as_dict=True)

    @frappe.whitelist()
    def get_log_frame(self, log_frame_name):
        return frappe.db.sql("""
            SELECT
                logf.logframe_name, logf.indicator_name, logf.type, logf.docstatus,
                logf.baseline, logf.target, logf.acheivement, logf.growth_in,
                logf.old_parent, logf.parent_tfd_logframe, logf.is_group,
                logf.indicator_name1, logf.company, logf.name,
                proj.parent, proj.parentfield, proj.parenttype, proj.cost,
                proj.project_name, proj.activity__name,
                ind.creation AS indicator_creation
            FROM `tabTFD Logframe` AS logf
            LEFT JOIN `tabProject Information` AS proj ON logf.name = proj.parent
            LEFT JOIN `tabTFD Main Indicators` AS ind ON logf.name = ind.name
            WHERE logf.logframe_name = %s
            ORDER BY ind.creation ASC
        """, (log_frame_name,), as_dict=True)

    @frappe.whitelist()
    def get_indicators(self, logframe_name):
        # Helper logic kept as per previous requests
        indicator_list = frappe.db.sql("SELECT DISTINCT indicator_name FROM `tabTFD Logframe` WHERE logframe_name = %s ORDER BY indicator_name", (logframe_name,), as_dict=True)
        unique_activity_set = set()
        for indicator in indicator_list:
            activities = frappe.db.sql("SELECT DISTINCT activity FROM `tabTFD Logframe Activities` WHERE parent IN (SELECT name FROM `tabTFD Logframe` WHERE logframe_name = %s AND indicator_name = %s)", (logframe_name, indicator['indicator_name']), as_dict=True)
            for activity in activities:
                unique_activity_set.add((activity['activity'], indicator['indicator_name']))
        return [{'activity': activity, 'indicator': indicator} for activity, indicator in unique_activity_set]

    @frappe.whitelist()
    def get_logframe_link(self, logframe_name):
        goal = frappe.db.get_value("TFD Logframe", {"logframe_name": logframe_name, "type": "Goal"}, ["indicator_name1", "order_index", "type"], as_dict=True)
        if not goal:
            goal = frappe.db.get_value("TFD Logframe", {"logframe_name": logframe_name, "parent_tfd_logframe": ["=", ""]}, ["indicator_name1", "order_index", "type"], as_dict=True)
        
        return {
            "indicator_name1": (goal.get("indicator_name1") if goal else "") or "",
            "order_index": (goal.get("order_index") if goal else 0) or 0,
            "type": (goal.get("type") if goal else "") or ""
        }