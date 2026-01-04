// Register the report in Frappe/ERPNext
// Define the filters that the user can select on the report page
frappe.query_reports["Validate  Report"] = {
    "filters": [
		 {
            "fieldname": "branch",
            "label": __("Branch"),
            "fieldtype": "Link",
            "options": "Branch",
            "reqd": 1 // Make branch selection required
        },
        {
            "fieldname": "from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "reqd": 1,
            "default": frappe.datetime.month_start()   // Default to start of current month
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "reqd": 1,
            "default": frappe.datetime.month_end()    // Default to end of current month
        }
    ]
};
