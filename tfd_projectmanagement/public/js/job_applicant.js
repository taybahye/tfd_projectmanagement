frappe.ui.form.on("Job Applicant", {
    before_save: function(frm) {
        if (frm.doc.custom_work_experiences && frm.doc.custom_work_experiences.length > 0) {
            frm.doc.custom_work_experiences.forEach(row => {
                calculate_experience(row.doctype, row.name);
            });
        }
    }
});

function calculate_experience(cdt, cdn) {
    let row = frappe.get_doc(cdt, cdn);
    if (!row.from_date) return;
    let from = frappe.datetime.str_to_obj(row.from_date);

    // إذا Check مفعل نعتبر الموظف يعمل الآن
    let to;
    if (row.i_currently_work_here == 1) {
        to = new Date(); // تاريخ اليوم
    } else if (row.to_date) {
        to = frappe.datetime.str_to_obj(row.to_date);
    } else {
        // لا يوجد to_date ولم يعمل Check
        frappe.model.set_value(cdt, cdn, "experience_months", 0);
        frappe.model.set_value(cdt, cdn, "experience_years", 0);
        frappe.model.set_value(cdt, cdn, "experience_remaining_months", 0);
        return;
    }

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
