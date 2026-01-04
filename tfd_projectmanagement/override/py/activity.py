# Triggered on Project events; updates the linked TFD Projects if not already from it


import frappe
def update_project(doc, method):
    if doc.custom_tfd_project and not getattr(doc.flags, "from_project", False):
        frappe.get_cached_doc("TFD Projects", doc.custom_tfd_project).update_project()
