import frappe


# Main function executed by the report
# It returns the report columns and the data
# filtered by date range and branch
def execute(filters=None):
    # Ensure filters is a dictionary even if None is passed
    if not filters:
        filters = {}


    # Extract filter values
    from_date = filters.get("from_date")
    to_date = filters.get("to_date")
    branch = filters.get("branch")


    # Define the report columns
    columns = [
        {"label": "Employee ID", "fieldname": "employee_id", "fieldtype": "Link", "options": "Employee", "width": 120},
        {"label": "Employee Name", "fieldname": "employee_name", "fieldtype": "Data", "width": 200},
        {"label": "Branch", "fieldname": "branch", "fieldtype": "Link", "options": "Branch", "width": 150},
                {"label": "Days", "fieldname": "planned_days", "fieldtype": "Int", "width": 120},
        {"label": "Attendance Days", "fieldname": "attendance_days", "fieldtype": "Int", "width": 150},
    ]


    # SQL query to fetch employee attendance
    # Uses LEFT JOIN to include employees with zero attendance
    # Optionally filters by branch if provided
    data = frappe.db.sql("""
        SELECT 
            e.name AS employee_id,
            e.employee_name,
            e.branch,
            COALESCE(COUNT(a.name), 0) AS attendance_days
        FROM 
            `tabEmployee` e
        LEFT JOIN 
            `tabAttendance` a 
            ON a.employee = e.name 
            AND a.attendance_date BETWEEN %(from_date)s AND %(to_date)s
        WHERE 
            e.status = 'Active'
            {branch_condition}
        GROUP BY 
            e.name, e.employee_name, e.branch
        ORDER BY 
            e.employee_name
    """.format(
        branch_condition="AND e.branch = %(branch)s" if branch else ""
    ), {
        "from_date": from_date,
        "to_date": to_date,
        "branch": branch
    }, as_dict=True)

    # Add a default value of 0 for 'planned_days' column for each row
    for row in data:
        row["planned_days"] = 0


    # Return columns and data to display in the report
    return columns, data
