// Register the report in Frappe/ERPNext
// Define the filters that users can select
frappe.query_reports["Validate Attendance Report"] = {
    "filters": [
		 {
            "fieldname": "branch",
            "label": __("Branch"),
            "fieldtype": "Link",
            "options": "Branch",
            "reqd": 1 // Branch selection is required
        },
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "reqd": 1,
            "default": frappe.datetime.month_start()  // Default: start of current month
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "reqd": 1,
            "default": frappe.datetime.month_end() // Default: end of current month
        }
    ]
};
