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
            child.parent_type,
            child.type,
            child.indicator_name_ar,
            SUM(child.collected_value) AS value
        FROM `tabIndicator Collected Data Child` child
        INNER JOIN `tabIndicator Collected Data` parent
            ON parent.name = child.parent
        WHERE {" AND ".join(conditions)}
            AND child.indicator_type = "Ind"
        GROUP BY
            child.logframe_indicator,
            child.parent_type,
            child.type,
            child.indicator_name_ar
        ORDER BY
            child.logframe_indicator,
            child.parent_type,
            child.type
    """, values, as_dict=True)

    indicators = {}

    for row in rows:
        indicator_key = row.logframe_indicator
        parent_type = row.parent_type or "Without Group"
        value = row.value or 0

        target = get_logframe_target(
            indicator_key=indicator_key,
            type_value=row.type,
            parent_type=row.parent_type
        )

        if indicator_key not in indicators:
            indicators[indicator_key] = {
                "indicator": row.indicator_name_ar,
                "total": 0,
                "target": 0,
                "parents": {}
            }

        if parent_type not in indicators[indicator_key]["parents"]:
            indicators[indicator_key]["parents"][parent_type] = {
                "total": 0,
                "target": 0,
                "items": []
            }

        indicators[indicator_key]["parents"][parent_type]["items"].append({
            "type": row.type or "Unknown",
            "value": value,
            "target": target
        })

        indicators[indicator_key]["parents"][parent_type]["total"] += value
        indicators[indicator_key]["parents"][parent_type]["target"] += target

        indicators[indicator_key]["total"] += value
        indicators[indicator_key]["target"] += target

    result = []

    for indicator in indicators.values():
        indicator["achievement"] = (
            (indicator["total"] / indicator["target"]) * 100
            if indicator["target"] else 0
        )

        indicator["parents"] = [
            {
                "parent_type": parent_type,
                "total": data["total"],
                "target": data["target"],
                "achievement": (
                    (data["total"] / data["target"]) * 100
                    if data["target"] else 0
                ),
                "items": [
                    {
                        **item,
                        "achievement": (
                            (item["value"] / item["target"]) * 100
                            if item["target"] else 0
                        )
                    }
                    for item in data["items"]
                ]
            }
            for parent_type, data in indicator["parents"].items()
        ]

        result.append(indicator)

    return result


def get_logframe_target(indicator_key, type_value=None, parent_type=None):
    if not indicator_key:
        return 0

    doc = frappe.get_doc("TFD Logframe", indicator_key)

    target = 0

    for row in doc.get("disaggregation") or []:
        same_type = (row.type or "") == (type_value or "")
        same_parent = (row.parent_type or "") == (parent_type or "")

        if same_type and same_parent:
            target += row.total or 0

    return target