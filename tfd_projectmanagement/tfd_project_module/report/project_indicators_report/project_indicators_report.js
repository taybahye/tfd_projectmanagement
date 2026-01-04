// Defines the Project Indicators report filters for the Frappe UI
frappe.query_reports["Project Indicators Report"] = {
    "filters": [
        {
            "fieldname": "project",
            "label": __("Project"),
            "fieldtype": "Link",
            "options": "TFD Projects"
	        }
    ]
};
