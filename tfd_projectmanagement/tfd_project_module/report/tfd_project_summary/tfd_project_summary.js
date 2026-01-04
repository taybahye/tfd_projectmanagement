// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.query_reports["TFD Project Summary"] = {
	// Define filters available for this report
	filters: [
		// Company filter (required)
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			reqd: 1,
		},
		// Filter by active status
		{
			fieldname: "is_active",
			label: __("Is Active"),
			fieldtype: "Select",
			options: "\nYes\nNo",
			default: "Yes",
		},
		// Filter by TFD Project
		{
			fieldname: "custom_tfd_project",
			label: __("TFD Project"),
			fieldtype: "Link",
			options: "TFD Projects",
		},
		// Filter by Project Status
		{
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Select",
			options: "\nOpen\nCompleted\nCancelled",
			default: "Open",
		},
		// Filter by Project Name / Activity
		{
			fieldname: "name",
			label: __("Activity"),
			fieldtype: "Link",
			options: "Project"
		},
		// Filter by Project Type
		{
			fieldname: "project_type",
			label: __("Project Type"),
			fieldtype: "Link",
			options: "Project Type",
		},
		// Filter by Priority
		{
			fieldname: "priority",
			label: __("Priority"),
			fieldtype: "Select",
			options: "\nLow\nMedium\nHigh",
		},
	],
};
