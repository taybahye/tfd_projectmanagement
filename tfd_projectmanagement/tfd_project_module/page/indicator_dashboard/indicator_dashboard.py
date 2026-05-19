import frappe


@frappe.whitelist()
def get_indicator_dashboard(logframe_name=None, from_date=None, to_date=None):
    conditions = ["parent.docstatus < 2"]
    values = {}

    if logframe_name:
        conditions.append("parent.logframe_name = %(logframe_name)s")
        values["logframe_name"] = logframe_name

    if from_date:
        conditions.append("parent.from_date >= %(from_date)s")
        values["from_date"] = from_date

    if to_date:
        conditions.append("parent.to_date <= %(to_date)s")
        values["to_date"] = to_date

    rows = frappe.db.sql(f"""
        SELECT
            child.logframe_indicator,
            child.type,
            child.indicator_name_ar,
            SUM(child.collected_value) AS value
        FROM `tabIndicator Collected Data Child` child
        INNER JOIN `tabIndicator Collected Data` parent
            ON parent.name = child.parent
        WHERE {" AND ".join(conditions)}
            AND child.indicator_type = "Ind"
        GROUP BY child.logframe_indicator, child.type, child.indicator_name_ar
        ORDER BY child.logframe_indicator, child.type
    """, values, as_dict=True)

    indicators = {}

    for row in rows:
        if row.logframe_indicator not in indicators:
            indicators[row.logframe_indicator] = {
                "indicator": row.indicator_name_ar,
                "total": 0,
                "items": []
            }

        value = row.value or 0

        indicators[row.logframe_indicator]["items"].append({
            "type": row.type,
            "value": value
        })

        indicators[row.logframe_indicator]["total"] += value

    return list(indicators.values())