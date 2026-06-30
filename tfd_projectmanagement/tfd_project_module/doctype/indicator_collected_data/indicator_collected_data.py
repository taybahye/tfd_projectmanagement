# Copyright (c) 2025, Amd Oudah Prosite  and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

class IndicatorCollectedData(Document):

    def validate(self):
        self.validate_dates()
        self.validate_overlapping_periods()

    def validate_dates(self):
        if self.from_date and self.to_date and self.from_date > self.to_date:
            frappe.throw(_("From Date cannot be after To Date"))

    def validate_overlapping_periods(self):
        if not self.logframe_name or not self.from_date or not self.to_date:
            return

        overlapping_record = frappe.db.sql(
            """
            SELECT name, from_date, to_date
            FROM `tabIndicator Collected Data`
            WHERE logframe_name = %(logframe_name)s
              AND name != %(name)s
              AND docstatus != 2
              AND from_date <= %(to_date)s
              AND to_date >= %(from_date)s
            LIMIT 1
            """,
            {
                "logframe_name": self.logframe_name,
                "name": self.name or "",
                "from_date": self.from_date,
                "to_date": self.to_date,
            },
            as_dict=True,
        )

        if overlapping_record:
            row = overlapping_record[0]
            frappe.throw(
                _(
                    "There is already an Indicator Collected Data record "
                    "for this Logframe with an overlapping period: {0} "
                    "from {1} to {2}."
                ).format(
                    frappe.bold(row.name),
                    row.from_date,
                    row.to_date,
                )
            )

# Returns all indicators for a given logframe, including child data and parent info
@frappe.whitelist()
def get_logframe_indicators(logframe_name):
    return frappe.db.sql("""
        SELECT 
            log.name,
            log.old_parent,
            logc.parent_type,
            logc.type,
            logc.baseline,
            logc.total AS target,
            log.indicator_name_en,
            log.indicator_name_ar,
            log.main_order,
            parent.indicator_name_ar AS indicator_parent
        FROM `tabTFD Logframe` log
        LEFT JOIN `tabTFD Logframe child` logc 
            ON log.name = logc.parent
        LEFT JOIN `tabTFD Logframe` parent 
            ON parent.name = log.old_parent
        WHERE log.logframe_name = %s
            AND log.type = 'Ind'
        ORDER BY log.main_order, logc.idx
    """, (logframe_name,), as_dict=True)
    