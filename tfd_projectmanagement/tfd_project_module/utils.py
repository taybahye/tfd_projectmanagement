import frappe



# Whitelisted function to start auto attendance processing
# for a specific shift. 
# This runs the processing in the background using a queue.
@frappe.whitelist()
def process_auto_attendance_for_selected_shift(shift_name):
    # Enqueue the background job for processing
    frappe.enqueue(
        method="tfd_projectmanagement.tfd_project_module.utils.bulk_process_auto_attendance",
        shift_name=shift_name,
        queue='long',
        timeout=None
    )

    # Return a message immediately
    return "Processing started in background."


# Whitelisted function that actually performs
# the bulk auto attendance for the given shift.
# This is executed in the background queue.
@frappe.whitelist()
def bulk_process_auto_attendance(shift_name):
    # Check if the shift type exists
    if not frappe.db.exists("Shift Type", shift_name):
        frappe.throw(f"Shift Type {shift_name} not found")
    
    # Fetch the Shift Type document
    shift_doc = frappe.get_doc("Shift Type", shift_name)

    # Call the method to process auto attendance for this shift
    shift_doc.process_auto_attendance()

    # Commit changes to the database
    frappe.db.commit()
