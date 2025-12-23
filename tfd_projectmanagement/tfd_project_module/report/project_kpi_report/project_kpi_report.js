// Copyright (c) 2025, Amd Oudah Prosite  and contributors
// For license information, please see license.txt

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
	//  tree: true,
    // name_field: "name",
    // parent_field: "parent",
    // initial_depth: 0
};
