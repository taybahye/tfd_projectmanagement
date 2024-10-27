from frappe.model.document import Document
import frappe

class TFDMainProposal(Document):
	@frappe.whitelist()
	def get_staffing(staffing_plan):
			proj_list=frappe.db.sql(f""" select * from  `tabStaffing Plan Detail` where parent='{staffing_plan.staffing_plan}' """,as_dict=True)
			return proj_list



	# @frappe.whitelist()
	# def get_indicators(self ,logframe_name):
	# 	# frappe.msgprint(f"Calling get_indicators with logframe_name: {self.framework}")  # تحقق من استلام logframe_name

	# 	indicator_list = frappe.db.sql(f"""
	# 		SELECT indicator_name 
	# 		FROM `tabTFD Logframe`
	# 		WHERE logframe_name = '{logframe_name}'
	# 	""", as_dict=True)

	# 	# frappe.msgprint(f"Indicator List: {indicator_list}")  # تحقق من نتائج الاستعلام
	# 	return indicator_list
	@frappe.whitelist()
	def get_indicators(self, logframe_name):
		# استعلام للحصول على indicator_name من الجدول الأساسي
		indicator_list = frappe.db.sql(f"""
			SELECT indicator_name 
			FROM `tabTFD Logframe`
			WHERE logframe_name = '{logframe_name}'
		""", as_dict=True)
		
		# استعلام للحصول على الأنشطة المرتبطة من الجدول الفرعي (افترض أن اسمه `tabTFD Logframe Activities`)
		activities = frappe.db.sql(f"""
			SELECT activity
			FROM `tabTFD Logframe Activities`
			WHERE parent = '{logframe_name}'
		""", as_dict=True)
		
		# إضافة قائمة الأنشطة إلى قائمة المؤشرات
		for indicator in indicator_list:
			indicator['activities'] = activities  # إضافة الأنشطة كقائمة مرتبطة بكل مؤشر
		
		frappe.msgprint(f"Indicator List with Activities: {indicator_list}")  # تحقق من نتائج الاستعلام
		return indicator_list

