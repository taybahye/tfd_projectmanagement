import frappe
from frappe.model.document import Document

class TFDMainProposal(Document):

    # -----------------------------------------------------------------------
    # 1️⃣ Before Save: Sync project_info -> project_plan
    # -----------------------------------------------------------------------
    def before_save(self):
        project_plan = self.get("project_info") or []
        self.set("project_plan", [])

        for d in project_plan:
            self.append("project_plan", {
                "project_name": d.project_name,
                "activity_name": d.activity__name
            })

    # -----------------------------------------------------------------------
    # 2️⃣ Get Staffing Plan Details
    # -----------------------------------------------------------------------
    @frappe.whitelist()
    def get_staffing(staffing_plan):
        proj_list = frappe.db.sql(f"""
            SELECT * 
            FROM `tabStaffing Plan Detail`
            WHERE parent = '{staffing_plan.staffing_plan}'
        """, as_dict=True)
        return proj_list

    # -----------------------------------------------------------------------
    # 3️⃣ Get Logframe Data (Ordered by creation datetime from TFD Main Indicators)
    # -----------------------------------------------------------------------
    @frappe.whitelist()
    def get_log_frame(log_frame_name):
        """
        Returns logframe data for the selected Log Frame name,
        joined with creation datetime from TFD Main Indicators.
        """

        proj_list = frappe.db.sql(f"""
            SELECT
                logf.logframe_name,
                logf.indicator_name,
                logf.type,
                logf.docstatus,
                logf.baseline,
                logf.target,
                logf.acheivement,
                logf.growth_in,
                logf.old_parent,
                logf.parent_tfd_logframe,
                logf.is_group,
                logf.indicator_name1,
                logf.company,
                logf.name,
                proj.parent,
                proj.parentfield,
                proj.parenttype,
                proj.cost,
                proj.project_name,
                proj.activity__name,
                ind.creation AS indicator_creation
            FROM
                `tabTFD Logframe` AS logf
            INNER JOIN
                `tabTFD Logframe Name` AS lf_name
                ON logf.logframe_name = lf_name.name
            LEFT JOIN
                `tabProject Information` AS proj
                ON logf.name = proj.parent
            LEFT JOIN
                `tabTFD Main Indicators` AS ind
                ON logf.name = ind.name
            WHERE
                logf.logframe_name = '{log_frame_name.log_frame_name}'
            ORDER BY
                ind.creation ASC
        """, as_dict=True)

        return proj_list

    # -----------------------------------------------------------------------
    # 4️⃣ Get Indicators and Related Activities (Helper Method)
    # -----------------------------------------------------------------------
    @frappe.whitelist()
    def get_indicators(self, logframe_name):
        """
        Returns a unique list of activities linked to indicators under the given log frame.
        """
        indicator_list = frappe.db.sql("""
            SELECT DISTINCT indicator_name
            FROM `tabTFD Logframe`
            WHERE logframe_name = %s
            ORDER BY logframe_name
        """, (logframe_name,), as_dict=True)

        unique_activity_set = set()

        for indicator in indicator_list:
            activities = frappe.db.sql("""
                SELECT DISTINCT activity
                FROM `tabTFD Logframe Activities`
                WHERE parent IN (
                    SELECT name
                    FROM `tabTFD Logframe`
                    WHERE logframe_name = %s AND indicator_name = %s
                )
            """, (logframe_name, indicator['indicator_name']), as_dict=True)

            for activity in activities:
                unique_activity_set.add((activity['activity'], indicator['indicator_name']))

        final_activity_list = [
            {'activity': activity, 'indicator': indicator} for activity, indicator in unique_activity_set
        ]

        return final_activity_list
