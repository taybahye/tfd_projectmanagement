import frappe

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        {"label": "Project ID", "fieldname": "project_id", "fieldtype": "Link", "options": "TFD Projects", "width": 150},
        {"label": "Proposal ID", "fieldname": "proposal_id", "fieldtype": "Link", "options": "TFD Main Proposal", "width": 150},
        {"label": "Logframe ID", "fieldname": "logframe_id", "fieldtype": "Link", "options": "TFD Logframe", "width": 150},
        {"label": "Achievement", "fieldname": "achievement", "fieldtype": "Float", "width": 120},
    ]

def get_data(filters):
    conditions = ""
    values = {}

    if filters.get("project"):
        conditions += " AND pr.name = %(project)s"
        values["project"] = filters["project"]

    query = f"""
        SELECT 
            pr.name AS project_id,
            p.name AS proposal_id,
            l.name AS logframe_id,
            l.acheivement AS achievement
        FROM 
            `tabTFD Projects` pr 
        JOIN 
            `tabTFD Main Proposal` p  
            ON p.project = pr.name  
        JOIN 
            `tabTFD Logframe` l 
            ON p.log_frame_name = l.logframe_name
            AND l.type = 'Ind'
        WHERE 1=1 {conditions}
        ORDER BY pr.name, l.name
    """

    return frappe.db.sql(query, values, as_dict=True)
