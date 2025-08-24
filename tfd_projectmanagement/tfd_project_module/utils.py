import frappe

@frappe.whitelist()
def process_auto_attendance_for_selected_shift(shift_name):
    frappe.enqueue(
        method="tfd_projectmanagement.tfd_project_module.utils.bulk_process_auto_attendance",
        shift_name=shift_name,
        queue='long',
        timeout=None
    )
    return "Processing started in background."

@frappe.whitelist()
def bulk_process_auto_attendance(shift_name):
    if not frappe.db.exists("Shift Type", shift_name):
        frappe.throw(f"Shift Type {shift_name} not found")
    
    shift_doc = frappe.get_doc("Shift Type", shift_name)
    shift_doc.process_auto_attendance()
    frappe.db.commit()
