// ===============================
// Parent DocType: TFD Logframe
// ===============================

frappe.ui.form.on('TFD Logframe', {
    indicator_name: function(frm) {
        if (frm.doc.indicator_name) {
            frappe.call({
                method: 'frappe.client.get_value',
                args: {
                    doctype: 'TFD Main Indicators',
                    filters: { name: frm.doc.indicator_name },
                    fieldname: ['type']
                },
                callback: function(r) {
                    if (r.message) {
                        frm.set_value('type', r.message.type);
                        frm.set_df_property('type', 'hidden', 0);

                        if (['Output', 'Indicator'].includes(r.message.type)) {
                            frm.set_df_property('activities', 'hidden', 0);
                        } else {
                            frm.set_df_property('activities', 'hidden', 1);
                        }
                    } else {
                        frappe.msgprint(__('Could not find the Indicator: ' + frm.doc.indicator_name));
                        frm.set_df_property('type', 'hidden', 1);
                        frm.set_df_property('activities', 'hidden', 1);
                    }
                }
            });
        } else {
            frm.set_df_property('type', 'hidden', 1);
            frm.set_df_property('activities', 'hidden', 1);
        }
    },

    refresh(frm) {
        frm.set_df_property('activities', 'hidden', 0);
    },

    validate(frm) {
        calculate_totals(frm);
    }
});


// ===============================
// Helper Functions
// ===============================

function calculate_row_total(row) {
    row.total = cint(flt(row.q1)) + cint(flt(row.q2)) + cint(flt(row.q3)) + cint(flt(row.q4));
}

function calculate_totals(frm) {
    let total_target = 0;

    (frm.doc.disaggregation || []).forEach(row => {
        calculate_row_total(row);
        total_target += cint(flt(row.total));
    });

    frm.refresh_field('disaggregation');
}


// ===============================
// Child Table: TFD Logframe child
// ===============================

frappe.ui.form.on('TFD Logframe child', {

    // لما يتغير total → يقسم العدد على 4 بدون كسور
    total(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        let total = cint(flt(row.total));

        if (total <= 0) return;

        // تقسيم متساوي لأربعة أرباع (بدون كسور)
        let divided = Math.floor(total / 4); // يقسم بدون كسور
        let remainder = total - divided * 4; // لتوزيع الباقي إن وجد

        // توزيع الباقي حتى يكون المجموع صحيح 100%
        row.q1 = divided + (remainder > 0 ? 1 : 0);
        row.q2 = divided + (remainder > 1 ? 1 : 0);
        row.q3 = divided + (remainder > 2 ? 1 : 0);
        row.q4 = divided;

        frm.dirty();
        frm.refresh_field('disaggregation');
    },

    // لما تتغير أي قيمة من Q1–Q4 → يعيد حساب total
    q1: update_row_total,
    q2: update_row_total,
    q3: update_row_total,
    q4: update_row_total
});


function update_row_total(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    row.total = cint(flt(row.q1)) + cint(flt(row.q2)) + cint(flt(row.q3)) + cint(flt(row.q4));
    frm.dirty();
    frm.refresh_field('disaggregation');
}
