const SENSITIVE_ISSUE_ROLE = "M&E-EMP";
const SENSITIVE_ISSUE_TYPE = "حساسة";

frappe.ui.form.on("Issue", {
    refresh(frm) {
        toggle_resolution_section(frm);
    },

    issue_type(frm) {
        toggle_resolution_section(frm);
    },
});

function toggle_resolution_section(frm) {
    const is_sensitive = frm.doc.issue_type === SENSITIVE_ISSUE_TYPE;
    const can_view_resolution = frappe.user_roles.includes(SENSITIVE_ISSUE_ROLE);

    frm.set_df_property(
        "section_break_19",
        "hidden",
        is_sensitive && !can_view_resolution ? 1 : 0,
    );
}
