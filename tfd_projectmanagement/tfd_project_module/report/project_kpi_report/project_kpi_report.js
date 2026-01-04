// Defines the Project KPI report filters for the Frappe UI
frappe.query_reports["Project KPI Report"] = {
	filters: [
		{
			"fieldname": "logframe",
			"label": __("Logframe"),
			"fieldtype": "Link",
			"options": "TFD Logframe Name",
		},
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
		},
	],

};
