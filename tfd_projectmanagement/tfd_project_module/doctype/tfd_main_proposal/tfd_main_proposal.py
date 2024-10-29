from frappe.model.document import Document
import frappe

class TFDMainProposal(Document):
  @frappe.whitelist()
  def get_staffing(staffing_plan):
      proj_list=frappe.db.sql(f""" select * from  tabStaffing Plan Detail where parent='{staffing_plan.staffing_plan}' """,as_dict=True)
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

        frappe.msgprint(f"Indicator List with Indicator Names: {indicator_list}")

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

        frappe.msgprint(f"Unique Activity List with Indicator Names: {final_activity_list}")
        return final_activity_list
