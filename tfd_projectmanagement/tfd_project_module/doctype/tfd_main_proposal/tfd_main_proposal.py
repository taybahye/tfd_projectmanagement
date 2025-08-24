from frappe.model.document import Document
import frappe

class TFDMainProposal(Document):
    def before_save(self):
            # جلب البيانات من Project Information
            project_info = frappe.db.sql("""
                SELECT project_name , activity__name
                FROM `tabProject Information`
                WHERE parent = %s
            """, (self.name,), as_dict=True)

            self.set("project_plan", [])

            # انسخ البيانات للجدول الفرعي
            for pi in project_info:
                row = self.append("project_plan", {})
                row.project_name = pi.project_name
                row.activity_name = pi.activity__name



    @frappe.whitelist()
    def get_staffing(staffing_plan):
        proj_list=frappe.db.sql(f""" select * from  tabStaffing Plan Detail where parent='{staffing_plan.staffing_plan}' """,as_dict=True)
        return proj_list
    
    @frappe.whitelist()
    def get_log_frame(log_frame_name):
        #   frappe.log(f"Indicator List: {ppst[0]}") 
        #   frappe.msgprint(f"Indicator List: {log_frame_name.log_frame_name}") 
        
        proj_list=frappe.db.sql(f""" SELECT
        `tabTFD Logframe`.logframe_name, 
        `tabTFD Logframe`.indicator_name, 
        `tabTFD Logframe`.type, 
        `tabTFD Logframe`.docstatus, 
        `tabTFD Logframe`.baseline, 
        `tabTFD Logframe`.target, 
        `tabTFD Logframe`.acheivement, 
        `tabTFD Logframe`.growth_in, 
        `tabTFD Logframe`.old_parent, 
        `tabTFD Logframe`.parent_tfd_logframe, 
        `tabTFD Logframe`.is_group, 
        `tabTFD Logframe`.indicator_name1, 
        `tabTFD Logframe`.company, 
        `tabTFD Logframe`.`name`, 
        `tabProject Information`.parent, 
        `tabProject Information`.parentfield, 
        `tabProject Information`.parenttype, 
        `tabProject Information`.cost, 
        `tabProject Information`.project_name,
        `tabProject Information`.activity__name
    FROM
        `tabTFD Logframe`
        INNER JOIN
        `tabTFD Logframe Name`
        ON 
            `tabTFD Logframe`.logframe_name = `tabTFD Logframe Name`.`name`
        LEFT JOIN
        `tabProject Information`
        ON 
            `tabTFD Logframe`.`name` = `tabProject Information`.parent
            where `tabTFD Logframe`.logframe_name='{log_frame_name.log_frame_name}' ORDER BY `tabTFD Logframe`.parent_tfd_logframe DESC  """,as_dict=True)
        
        #   frappe.msgprint(f"Indicator List: {log_frame_name.log_frame_name}") 
        #   frappe.msgprint({proj_list})
        return proj_list




  # @frappe.whitelist()
  # def get_indicators(self ,logframe_name):
  #   # frappe.msgprint(f"Calling get_indicators with logframe_name: {self.framework}")  # تحقق من استلام logframe_name

  #   indicator_list = frappe.db.sql(f"""
  #     SELECT indicator_name 
  #     FROM tabTFD Logframe
  #     WHERE logframe_name = '{logframe_name}'
  #   """, as_dict=True)

  #   # frappe.msgprint(f"Indicator List: {indicator_list}")  # تحقق من نتائج الاستعلام
  #   return indicator_list
    @frappe.whitelist()
    def get_indicators(self, logframe_name):
            indicator_list = frappe.db.sql("""
                SELECT DISTINCT indicator_name
                FROM `tabTFD Logframe`
                WHERE logframe_name = %s
                ORDER BY logframe_name
            """, (logframe_name,), as_dict=True)

            # frappe.msgprint(f"Indicator List with Indicator Names: {indicator_list}")

            unique_activity_set = set()

            for indicator in indicator_list:
                activities = frappe.db.sql("""
                    SELECT DISTINCT activity
                    FROM `tabTFD Logframe Activities`
                    WHERE parent IN (
                        SELECT name
                        FROM `tabTFD Logframe`
                        WHERE logframe_name = %s AND indicator_name = %s
                    )
                """, (logframe_name, indicator['indicator_name']), as_dict=True)

                for activity in activities:
                    unique_activity_set.add((activity['activity'], indicator['indicator_name']))

            final_activity_list = [
                {'activity': activity, 'indicator': indicator} for activity, indicator in unique_activity_set
            ]

            # frappe.msgprint(f"Unique Activity List with Indicator Names: {final_activity_list}")
            return final_activity_list
