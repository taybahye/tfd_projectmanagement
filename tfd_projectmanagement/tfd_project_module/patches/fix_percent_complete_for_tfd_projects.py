import frappe
from frappe.utils import flt


def execute():
	for project in frappe.get_all("TFD Projects", fields=["name", "percent_complete_method", "percent_complete"]):
		total = frappe.db.count("Project", dict(custom_tfd_project=project.name))
		if project.percent_complete_method == "Task Completion" and total > 0:
			completed = frappe.db.sql(
				"""select count(name) from tabProject where
					custom_tfd_project=%s and status in ('Cancelled', 'Completed')""",
				project.name,
			)[0][0]
			percent_complete = flt(flt(completed) / total * 100, 2)
			if project.percent_complete != percent_complete:
				frappe.db.set_value("TFD Projects", project.name, "percent_complete", percent_complete)
				if percent_complete == 100:
					frappe.db.set_value("TFD Projects", project.name, "status", "Completed")


# 					import frappe
# from frappe.utils import flt


# def execute():
# 	for project in frappe.get_all("Project", fields=["name", "percent_complete_method"]):
# 		total = frappe.db.count("Task", dict(project=project.name))
# 		if project.percent_complete_method == "Task Completion" and total > 0:
# 			completed = frappe.db.sql(
# 				"""select count(name) from tabTask where
# 					project=%s and status in ('Cancelled', 'Completed')""",
# 				project.name,
# 			)[0][0]
# 			percent_complete = flt(flt(completed) / total * 100, 2)
# 			if project.percent_complete != percent_complete:
# 				frappe.db.set_value("Project", project.name, "percent_complete", percent_complete)
# 				if percent_complete == 100:
# 					frappe.db.set_value("Project", project.name, "status", "Completed")

# import frappe
# from frappe.utils import flt

# def execute():
#     """
#     تحسب نسبة إنجاز كل مشروع TFD بناءً على المشاريع المرتبطة به،
#     تطبع old vs new percent_complete لكل مشروع،
#     وتحدث الحقول إذا كانت مختلفة.
#     """

#     projects = frappe.get_all(
#         "TFD Projects",
#         fields=["name", "percent_complete_method", "percent_complete"]
#     )

#     for project in projects:
#         # إجمالي المشاريع المرتبطة بالـ TFD Project
#         total = frappe.db.count("Project", {"custom_tfd_project": project.name})

#         if project.percent_complete_method != "Task Completion" or total == 0:
#             print(f"{project.name}: Skipped (method != Task Completion or no linked Projects)")
#             continue

#         # عدد المشاريع المكتملة أو الملغاة
#         completed = frappe.db.sql(
#             """
#             SELECT COUNT(name)
#             FROM `tabProject`
#             WHERE custom_tfd_project=%s
#               AND status IN ('Cancelled', 'Completed')
#             """,
#             project.name
#         )[0][0]

#         # حساب النسبة الجديدة
#         percent_complete = flt((completed / total) * 100, 2)

#         # طباعة النسبة القديمة والجديدة
#         print(f"{project.name}: old={project.percent_complete}%, new={percent_complete}%")

#         # تحديث فقط إذا تغيرت النسبة
#         if project.percent_complete != percent_complete:
#             frappe.db.set_value("TFD Projects", project.name, "percent_complete", percent_complete)

#             if percent_complete == 100:
#                 frappe.db.set_value("TFD Projects", project.name, "status", "Completed")

#             # Commit بعد كل تحديث لتجنب أي Lock Timeout
#             frappe.db.commit()

#     print("Done updating percent_complete for TFD Projects.")
