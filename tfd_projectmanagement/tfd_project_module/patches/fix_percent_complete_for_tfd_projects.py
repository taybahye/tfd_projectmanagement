import frappe
from frappe.utils import flt

# Patch: Update percent completion of all TFD Projects based on linked Projects.
# For projects using "Activity Completion" method, calculates percent_complete.
# If all linked Projects are completed or cancelled, sets percent_complete to 100% and marks the TFD Project as "Completed".

def execute():
	for project in frappe.get_all("TFD Projects", fields=["name", "percent_complete_method", "percent_complete"]):
		total = frappe.db.count("Project", dict(custom_tfd_project=project.name))
		if project.percent_complete_method == "Activity Completion" and total > 0:
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

