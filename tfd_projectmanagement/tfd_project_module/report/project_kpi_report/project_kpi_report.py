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
        {"label": _("Result"), "fieldname": "result", "fieldtype": "Data", "width": 220},
        {"label": _("Indicator Number"), "fieldname": "order_index", "fieldtype": "Data", "width": 120},
        {"label": _("Indicator"), "fieldname": "indicator_name_ar", "fieldtype": "Data", "width": 300},
        {"label": _("Type"), "fieldname": "type", "fieldtype": "Data", "width": 120},
        {"label": _("Baseline"), "fieldname": "baseline", "fieldtype": "Float", "width": 140},
        {"label": _("Target"), "fieldname": "target", "fieldtype": "Float", "width": 140},
        {
            "label": _("Cumulative Achievement"),
            "fieldname": "collected_value",
            "fieldtype": "Float",
            "width": 140
        },
        {
            "label": _("Achievement %"),
            "fieldname": "achievement_percent",
            "fieldtype": "Percent",
            "width": 140
        },
        {"label": _("Comment"), "fieldname": "comment", "fieldtype": "Data", "width": 300},

    ]

def get_data(filters):
    query = """
        SELECT
            MIN(icd.from_date) AS from_date,
            MAX(icd.to_date) AS to_date,
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

    # التجميع حسب المؤشر فقط
    query += """
        GROUP BY inch.indicator_name_ar, inch.type, inch.order_index, icd.logframe_name
        ORDER BY inch.order_index
    """

    return frappe.db.sql(query, values, as_dict=True)
