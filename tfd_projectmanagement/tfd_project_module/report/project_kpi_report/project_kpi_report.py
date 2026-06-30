import frappe
from frappe import _


# Entry point for the report: returns columns and data based on filters
def execute(filters=None):
    if not filters:
        filters = {}

    columns = get_columns()
    data = get_data(filters)
    return columns, data



# Defines the columns for the Project KPI report
def get_columns():
    return [
        {"label": _("Indicator Number"), "fieldname": "order_index", "fieldtype": "Data", "width": 120},
        {"label": _("Indicator"), "fieldname": "indicator_name_ar", "fieldtype": "Data", "width": 300},
        {
            "label": _("Logframe Indicator"),
            "fieldname": "logframe_indicator",
            "fieldtype": "Data",
            "width": 300
        },
        {
            "label": _("Parent Type"),
            "fieldname": "parent_type",
            "fieldtype": "Data",
            "width": 180
        },
        {"label": _("Type"), "fieldname": "type", "fieldtype": "Data", "width": 120},
        {"label": _("Baseline"), "fieldname": "baseline", "fieldtype": "Number", "width": 140},
        {
            "label": _("Target"),
            "fieldname": "target",
            "fieldtype": "Data",
            "width": 140
        },
        {
            "label": _("Cumulative Achievement"),
            "fieldname": "collected_value",
            "fieldtype": "Number",
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



def get_project_info(logframe_name):
    if not logframe_name:
        return {}

    logframe_info = frappe.db.get_value(
        "TFD Logframe Name",
        logframe_name,
        [
            "name",
            "tfd_project",
        ],
        as_dict=True,
    ) or {}

    if not logframe_info.get("tfd_project"):
        return logframe_info

    project_info = frappe.db.get_value(
        "TFD Projects",
        logframe_info.get("tfd_project"),
        [
            "project_name",
            "project_number",
            "expected_start_date",
            "expected_end_date",
        ],
        as_dict=True,
    ) or {}

    return {
        **logframe_info,
        **project_info,
        "project_start_date": project_info.get("expected_start_date"),
        "project_end_date": project_info.get("expected_end_date"),
    }

# Retrieves and aggregates data for the Project KPI report based on filters
def get_data(filters):
    query = """
        SELECT
            MIN(icd.from_date) AS from_date,
            MAX(icd.to_date) AS to_date,
            inch.indicator_name_ar,
            inch.logframe_indicator,
            inch.baseline,
            inch.target,
            inch.parent_type,
            inch.indicator_parent,
            inch.type,
            inch.indicator_type,
            inch.order_index,
            SUM(inch.collected_value) AS collected_value,
            CASE
                WHEN CAST(inch.target AS DECIMAL(18,6)) > 0 THEN
                    ROUND((SUM(inch.collected_value) / CAST(inch.target AS DECIMAL(18,6))) * 100, 2)
                ELSE 0
            END AS achievement_percent,
            icd.logframe_name,
            inch.comment,
            parent.name AS section_name,
            parent.type AS section_type,
            parent.indicator_name_ar AS section_title,
            parent.main_order AS section_order
        FROM `tabIndicator Collected Data` icd
        JOIN `tabIndicator Collected Data Child` inch
            ON inch.parent = icd.name
        LEFT JOIN `tabTFD Logframe` ind
            ON ind.name = inch.logframe_indicator

        LEFT JOIN `tabTFD Logframe` parent
            ON parent.name = ind.old_parent
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
        GROUP BY
                inch.indicator_name_ar,
                inch.logframe_indicator,
                inch.baseline,
                inch.target,
                inch.parent_type,
                inch.indicator_type,
                inch.type,
                inch.indicator_parent,
                inch.order_index,
                icd.logframe_name,
                inch.comment,
                parent.name,
                parent.type,
                parent.indicator_name_ar,
                parent.main_order
           ORDER BY
                parent.main_order,
                inch.order_index
        """

    data = frappe.db.sql(query, values, as_dict=True)

    project_info = get_project_info(filters.get("logframe_name"))
    project_info.update({
        "report_from_date": filters.get("from_date"),
        "report_to_date": filters.get("to_date"),
    })

    for row in data:
        row.update(project_info)

    return data
