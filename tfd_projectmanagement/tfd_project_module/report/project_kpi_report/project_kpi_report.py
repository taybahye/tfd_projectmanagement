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
		{"label": _("Indicator Number"), "fieldname": "order_index", "fieldtype": "Data", "width": 120},
        {"label": _("From Date"), "fieldname": "from_date", "fieldtype": "Date", "width": 120},
        {"label": _("To Date"), "fieldname": "to_date", "fieldtype": "Date", "width": 120},
        {"label": _("Indicator"), "fieldname": "indicator_name_ar", "fieldtype": "Data", "width": 250},
        {"label": _("Type"), "fieldname": "type", "fieldtype": "Data", "width": 120},
		{"label": _("Collected Data"), "fieldname": "collected_value", "fieldtype": "Data", "width": 120},

    ]
def get_data(filters):
    query = """
        SELECT
            icd.from_date,
            icd.to_date,
            inch.indicator_name_ar,
            inch.type,
			inch.order_index,
            SUM(inch.collected_value) AS collected_value,
            icd.logframe_name
        FROM `tabIndicator Collected Data` icd
        JOIN `tabIndicator Collected Data Child` inch
            ON inch.parent = icd.name
        WHERE TRIM(IFNULL(inch.indicator_name_ar, '')) <> ''
    """

    values = {}

    # فلترة حسب Logframe
    if filters.get("logframe_name"):
        query += " AND icd.logframe_name = %(logframe_name)s"
        values["logframe_name"] = filters.get("logframe_name")

    # فلترة حسب from_date
    if filters.get("from_date"):
        query += " AND icd.from_date >= %(from_date)s"
        values["from_date"] = filters.get("from_date")

    # فلترة حسب to_date
    if filters.get("to_date"):
        query += " AND icd.to_date <= %(to_date)s"
        values["to_date"] = filters.get("to_date")

    # التجميع حسب الأعمدة الأساسية
    query += """
        GROUP BY icd.from_date, icd.to_date, inch.indicator_name_ar, inch.type, icd.logframe_name
        ORDER BY icd.from_date, icd.to_date, inch.idx
    """

    return frappe.db.sql(query, values, as_dict=True)

		# query = """
		# 	SELECT
		# 		k.logframe_name,
		# 		k.indicator_logframe,
		# 		lt.type AS indicator_type,
		# 		lt.total AS target,
		# 		DATE_FORMAT(a.date_collected, '%%Y-%%m') AS period,
		# 		SUM(COALESCE(a.collected_value, 0)) AS actual_value
		# 	FROM `tabIndicator Collected Data` k
		# 	LEFT JOIN `tabDisaggregation Logframe Child` a
		# 		ON k.name = a.parent AND a.parentfield = 'collecting_data'
		# 	LEFT JOIN `tabTFD Logframe` l
		# 		ON l.name = k.indicator_logframe
		# 	LEFT JOIN `tabTFD Logframe child` lt
		# 		ON lt.parent = l.name AND lt.type = a.type
		# 	WHERE 1=1
		# """
		