frappe.ui.form.on("Job Applicant", {
    before_insert: function(frm) {
        calculate_experience(frm);
    },
});

function calculate_experience(frm) {
    if (frm.doc.from_date && frm.doc.to_date) {
        let from = frappe.datetime.str_to_obj(frm.doc.from_date);
        let to = frappe.datetime.str_to_obj(frm.doc.to_date);

        if (from && to && to >= from) {
            let years = to.getFullYear() - from.getFullYear();
            let months = to.getMonth() - from.getMonth();
            let days = to.getDate() - from.getDate();

            if (months < 0 || (months === 0 && days < 0)) {
                years -= 1;
            }

            frm.set_value("years_of_experience", years);
        } else {
            frm.set_value("years_of_experience", 0);
        }
    }
}
