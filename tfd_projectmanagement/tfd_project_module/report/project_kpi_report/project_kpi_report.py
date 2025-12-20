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
        {"label": _("Result"), "fieldname": "result", "fieldtype": "Data", "width": 120},
		{"label": _("Indicator Number"), "fieldname": "order_index", "fieldtype": "Data", "width": 120},
        # {"label": _("From Date"), "fieldname": "from_date", "fieldtype": "Date", "width": 120},
        # {"label": _("To Date"), "fieldname": "to_date", "fieldtype": "Date", "width": 120},
        {"label": _("Indicator"), "fieldname": "indicator_name_ar", "fieldtype": "Data", "width": 250},
        {"label": _("Type"), "fieldname": "type", "fieldtype": "Data", "width": 120},
		{"label": _("Collected Data"), "fieldname": "collected_value", "fieldtype": "Data", "width": 120},

    ]
def get_data(filters):
    query = """
        SELECT
            inch.order_index,
            inch.indicator_name_ar,
            inch.type,
            inch.indicator_parent AS result,
            SUM(inch.collected_value) AS collected_value
        FROM `tabIndicator Collected Data` icd
        JOIN `tabIndicator Collected Data Child` inch
            ON inch.parent = icd.name
        WHERE TRIM(IFNULL(inch.indicator_name_ar, '')) <> ''
    """

    values = {}

    # فلترة حسب Logframe
    if filters.get("logframe_name"):
        query += " AND icd.logframe_name = %(logframe_name)s"
        values["logframe_name"] = filters["logframe_name"]

    if filters.get("from_date") and filters.get("to_date"):
        query += """
            AND icd.from_date >= %(from_date)s
            AND icd.to_date <= %(to_date)s

        """
        values["from_date"] = filters["from_date"]
        values["to_date"] = filters["to_date"]


    query += """
        GROUP BY
            inch.order_index,
            inch.indicator_name_ar,
            inch.type
        ORDER BY inch.order_index
    """

    return frappe.db.sql(query, values, as_dict=True)
