// Copyright (c) 2025, Safa and contributors
// For license information, please see license.txt

frappe.ui.form.on("Project", {
    refresh(frm) {
        frm.set_query("custom_parent", function() {
            return {
                filters: {
                    custom_is_group: 1
                }
            };
        });
    },
    validate(frm) {
        if (!frm.doc.custom_disaggregation || frm.doc.custom_disaggregation.length === 0) {
            return;
        }

        let totals = {};
        let total_sum = 0;

        frm.doc.custom_disaggregation.forEach(row => {
            if (row.type) {
                totals[row.type] = (totals[row.type] || 0) + (row.number_target || 0);
                total_sum += (row.number_target || 0);
            }
        });

        frm.set_value('custom_total', total_sum);


    },
});
