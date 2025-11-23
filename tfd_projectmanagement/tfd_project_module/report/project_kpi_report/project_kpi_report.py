# Copyright (c) 2025, Amd Oudah Prosite and contributors
# For license information, please see license.txt

import frappe
from frappe import _

def execute(filters=None):
    if not filters:
        filters = {}

    columns = get_columns()
    data = get_data(filters)

    return columns, data


def get_columns():
    return [
        {"label": _("Logframe"), "fieldname": "logframe_name", "fieldtype": "Data", "width": 200},
        {"label": _("Indicator"), "fieldname": "indicator_logframe", "fieldtype": "Data", "width": 200},
        {"label": _("Type"), "fieldname": "indicator_type", "fieldtype": "Data", "width": 120},
        {"label": _("Target Value"), "fieldname": "target", "fieldtype": "Float", "width": 120},
        {"label": _("Actual Value"), "fieldname": "actual_value", "fieldtype": "Float", "width": 120},
    ]


def get_data(filters):
		query = """
			SELECT
				k.logframe_name,
				k.indicator_logframe,
				lt.type AS indicator_type,
				lt.total AS target,
				DATE_FORMAT(a.date_collected, '%%Y-%%m') AS period,
				SUM(COALESCE(a.collected_value, 0)) AS actual_value
			FROM `tabIndicator Collected Data` k
			LEFT JOIN `tabDisaggregation Logframe Child` a
				ON k.name = a.parent AND a.parentfield = 'collecting_data'
			LEFT JOIN `tabTFD Logframe` l
				ON l.name = k.indicator_logframe
			LEFT JOIN `tabTFD Logframe child` lt
				ON lt.parent = l.name AND lt.type = a.type
			WHERE 1=1
		"""

		values = {}

		if filters.get("logframe"):
			query += " AND k.logframe_name = %(logframe)s"
			values["logframe"] = filters.get("logframe")

		if filters.get("from_date"):
			query += " AND a.date_collected >= %(from_date)s"
			values["from_date"] = filters.get("from_date")

		if filters.get("to_date"):
			query += " AND a.date_collected <= %(to_date)s"
			values["to_date"] = filters.get("to_date")

		query += """
			GROUP BY k.logframe_name, k.indicator_logframe, lt.type, lt.total, period
			ORDER BY k.logframe_name, k.indicator_logframe, period
		"""

		return frappe.db.sql(query, values, as_dict=True)
