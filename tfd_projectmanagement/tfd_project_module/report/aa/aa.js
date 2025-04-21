// Copyright (c) 2024, ziad alsewary and contributors
// For license information, please see license.txt

frappe.query_reports["PWP Salary Register"] = {
	"filters": [
		{
			"fieldname":"from_date",
			"label": __("From"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(),-1),
			"reqd": 1,
			"width": "100px"
		},
		{
			"fieldname":"to_date",
			"label": __("To"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 1,
			"width": "100px"
		},
		{
			"fieldname": "currency",
			"fieldtype": "Link",
			"options": "Currency",
			"label": __("Currency"),
			"default": erpnext.get_currency(frappe.defaults.get_default("Company")),
			"width": "50px"
		},
		{
			"fieldname":"employee",
			"label": __("Employee"),
			"fieldtype": "Link",
			"options": "Employee",
			"width": "100px"
		},
		{
			"fieldname":"employment_type",
			"label": __("Employment Type"),
			"fieldtype": "Link",
			"options": "Employment Type",
			"width": "100px"
		},
		{
			"fieldname":"company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_user_default("Company"),
			"width": "100px",
			"reqd": 1
		},
		{
			"fieldname":"docstatus",
			"label":__("Document Status"),
			"fieldtype":"Select",
			"options":["Draft", "Submitted", "Cancelled"],
			"default": "Draft",
			"width": "100px"
		},
		{
			"fieldname":"salary_structure",
			"label": __("Salary Structure"),
			"fieldtype": "Link",
			"options": "Salary Structure",
			"width": "100px",
		},
		{
			"fieldname":"slip_dates",
			"label": __("Slip Dates"),
			"fieldtype":"Select",
			"options":["", "Disbursement", "Attendance", "All"],
			"default": "",
		},
		{
			"fieldname":"p_bank",
			"label": __("P Bank"),
			"fieldtype": "Link",
			"options": "P Bank",
			"width": "100px",
		},
		{
			"fieldname":"title",
			"label": __("Title"),
			"fieldtype": "Data",
			"width": "100px",
			on_change: function() {}
		},
		{
			"fieldname":"show_dates",
			"label": __("Show Dates in Print"),
			"fieldtype": "Check",
			"width": "100px",
			on_change: function() {}
		},
		{
			"fieldname":"do_not_show_the_exception",
			"label": __("Do not show the exception"),
			"fieldtype": "Check",
			"width": "100px",
		},
		{
			"fieldname":"add_extra_columns",
			"label": __("Add Extra Columns"),
			"fieldtype": "Check",
			"width": "100px",
		},
	]
};
