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
    conditions = ""
    values = {}

    if filters.get("logframe_name"):
        conditions += " AND icd.logframe_name = %(logframe_name)s"
        values["logframe_name"] = filters["logframe_name"]

    if filters.get("from_date") and filters.get("to_date"):
        conditions += """
            AND icd.from_date >= %(from_date)s
            AND icd.to_date <= %(to_date)s
        """
        values["from_date"] = filters["from_date"]
        values["to_date"] = filters["to_date"]

    # 1️⃣ جلب جميع الـ Results
    results = frappe.db.sql(f"""
        SELECT DISTINCT
            inch.indicator_parent
        FROM `tabIndicator Collected Data` icd
        JOIN `tabIndicator Collected Data Child` inch
            ON inch.parent = icd.name
        WHERE TRIM(IFNULL(inch.indicator_parent, '')) <> ''
        {conditions}
        ORDER BY inch.indicator_parent
    """, values, as_dict=True)

    data = []

    for res in results:
        # 2️⃣ صف العنوان الخاص بالـ Result
        data.append({
            "result": res.indicator_parent,
            "order_index": "",
            "indicator_name_ar": "",
            "type": "",
            "baseline": "",
            "target": "",
            "collected_value": "",
            "achievement_percent": "",
            "comment"  : ""
        })

        # 3️⃣ جلب المؤشرات التابعة لكل Result
        indicators = frappe.db.sql(f"""
            SELECT
                inch.order_index,
                inch.indicator_name_ar,
                inch.type,
                inch.baseline,
                inch.target,
                inch.comment,
                SUM(inch.collected_value) AS collected_value
            FROM `tabIndicator Collected Data` icd
            JOIN `tabIndicator Collected Data Child` inch
                ON inch.parent = icd.name
            WHERE
                inch.indicator_parent = %(result)s
                AND TRIM(IFNULL(inch.indicator_name_ar, '')) <> ''
                {conditions}
            GROUP BY inch.name
            ORDER BY inch.order_index
        """, {**values, "result": res.indicator_parent}, as_dict=True)

        for ind in indicators:
            # حساب نسبة الإنجاز
            achievement_percent = 0
            if ind.target and ind.target > 0:
                achievement_percent = (ind.collected_value / ind.target) * 100

            data.append({
                "result": "",
                "order_index": ind.order_index,
                "indicator_name_ar": ind.indicator_name_ar,
                "type": ind.type,
                "baseline": ind.baseline,
                "target": ind.target,
                "collected_value": ind.collected_value,
                "achievement_percent": round(achievement_percent, 2),
                "comment" : ind.comment
            })

    return data
