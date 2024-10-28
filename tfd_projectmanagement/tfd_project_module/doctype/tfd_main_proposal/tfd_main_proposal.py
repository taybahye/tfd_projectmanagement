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
  def get_indicators(self ,logframe_name):
    # Fetch indicators for the specified logframe name
    indicator_list = frappe.db.sql(f"""
      SELECT indicator_name , name
      FROM `tabTFD Logframe`
      WHERE logframe_name = '{logframe_name}'
    """, as_dict=True)
    
    frappe.msgprint(f"Documents with logframe_name {logframe_name}: {indicator_list}")
    
    # Fetch activities for each indicator
    for indicator in indicator_list:
        activities = frappe.db.sql("""
            SELECT activity
            FROM `tabTFD Logframe Activities`
            WHERE parent = %s
        """, (indicator['name'],), as_dict=True)
        
        # Add activities to each indicator
        indicator['activities'] = [activity['activity'] for activity in activities]

    # Output the final result
    frappe.msgprint(f"Indicator List with Activities: {indicator_list}")
    return indicator_list 