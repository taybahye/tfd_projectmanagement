frappe.ui.form.on("Job Applicant", {
    before_save: function(frm) {
        if (frm.doc.custom_work_experiences && frm.doc.custom_work_experiences.length > 0) {
            frm.doc.custom_work_experiences.forEach(row => {
                calculate_experience(row.doctype, row.name);
            });
        }
    }
});

// دالة لحساب الخبرة لكل صف في الجدول الفرعي
function calculate_experience(cdt, cdn) {
    let row = frappe.get_doc(cdt, cdn);
    if (!row.from_date || !row.to_date) return;

    let from = frappe.datetime.str_to_obj(row.from_date);
    let to   = frappe.datetime.str_to_obj(row.to_date);
    if (to < from) {
        frappe.model.set_value(cdt, cdn, "experience_months", 0);
        frappe.model.set_value(cdt, cdn, "experience_years", 0);
        frappe.model.set_value(cdt, cdn, "experience_remaining_months", 0);
        return;
    }

    // حساب الأشهر الكاملة
    let months = (to.getFullYear() - from.getFullYear()) * 12;
    months += to.getMonth() - from.getMonth();
    if (to.getDate() < from.getDate()) months -= 1;

    let years = Math.floor(months / 12);
    let remainingMonths = months % 12;

    frappe.model.set_value(cdt, cdn, "experience_months", months);
    frappe.model.set_value(cdt, cdn, "experience_years", years);
    frappe.model.set_value(cdt, cdn, "experience_remaining_months", remainingMonths);
}
