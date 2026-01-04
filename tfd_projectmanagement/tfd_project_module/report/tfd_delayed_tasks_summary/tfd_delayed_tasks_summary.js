// Define filters available in the report
frappe.query_reports["TFD Delayed Tasks Summary"] = {
	filters: [
		// Filter by TFD Project
		{
			fieldname: "custom_tfd_project",
			label: __("TFD Project"),
			fieldtype: "Link",
			options:"TFD Projects",
		},
		// Filter by Project
		{
			fieldname: "project",
			label: __("Project"),
			fieldtype: "Link",
			options:"Project",
		},
        // Start date filter
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
		},
		// End date filter
		{
			fieldname: "to_date",
			label: __("To Date"),
			fieldtype: "Date",
		},
		// Filter by priority
		{
			fieldname: "priority",
			label: __("Priority"),
			fieldtype: "Select",
			options: ["", "Low", "Medium", "High", "Urgent"],
		},
		// Filter by status
		{
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Select",
			options: ["", "Open", "Working", "Pending Review", "Overdue", "Completed"],
		},
	],

	// Highlight delay column values (red if delayed, green if on track)
	formatter: function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (column.id == "delay") {
			if (data["delay"] > 0) {
				value = `<p style="color: red; font-weight: bold">${value}</p>`;
			} else {
				value = `<p style="color: green; font-weight: bold">${value}</p>`;
			}
		}
		return value;
	},

	// On report load, set dynamic filter queries
	onload: function (report) {
		let project_filter = frappe.query_report.get_filter('project');

		if (project_filter) {
			project_filter.df.get_query = function() {
				let tfd_project = frappe.query_report.get_filter_value("custom_tfd_project");

				if (tfd_project) {
					return {
						filters: {
							custom_tfd_project: tfd_project
						}
					};
				}

				return {};
			};
		}
	}


};
