import frappe


# Change this value if the role used by your installation has a different name.
SENSITIVE_ISSUE_ROLE = "M&E-EMP"
SENSITIVE_ISSUE_TYPE = "حساسة"

# Fields displayed in the standard Issue resolution section.
RESOLUTION_FIELDS = (
    "resolution_details",
    "resolution_date",
    "resolution_time",
    "user_resolution_time",
)


def validate_sensitive_issue(doc, method=None):
    """Prevent unauthorized users from adding or changing a sensitive resolution."""
    if doc.issue_type != SENSITIVE_ISSUE_TYPE:
        return

    if SENSITIVE_ISSUE_ROLE in frappe.get_roles():
        return

    if doc.is_new():
        resolution_changed = any(doc.get(fieldname) for fieldname in RESOLUTION_FIELDS)
    else:
        existing_values = frappe.db.get_value(
            "Issue", doc.name, list(RESOLUTION_FIELDS), as_dict=True
        ) or {}
        resolution_changed = any(
            (doc.get(fieldname) or "") != (existing_values.get(fieldname) or "")
            for fieldname in RESOLUTION_FIELDS
        )

    # Unrelated edits are allowed, but resolution data cannot be added or
    # changed by a user who lacks the sensitive-issue role.
    if resolution_changed:
        frappe.throw(
            "لا تملك الصلاحية لإدخال أو تعديل الحل في الشكوى الحساسة",
            frappe.PermissionError,
        )
