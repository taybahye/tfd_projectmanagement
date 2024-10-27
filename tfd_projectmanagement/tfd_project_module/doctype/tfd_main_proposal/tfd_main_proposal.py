from frappe.model.document import Document
import frappe

class TFDMainProposal(Document):
	@frappe.whitelist()
	def get_staffing(staffing_plan):
			proj_list=frappe.db.sql(f""" select * from  `tabStaffing Plan Detail` where parent='{staffing_plan.staffing_plan}' """,as_dict=True)
			return proj_list
