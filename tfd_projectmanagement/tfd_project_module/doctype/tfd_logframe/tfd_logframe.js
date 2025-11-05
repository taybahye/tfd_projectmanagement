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

    refresh: function(frm) {
        // Show activities by default
        frm.set_df_property('activities', 'hidden', 0);

        // Watch for any change in disaggregation table
        frm.fields_dict.disaggregation.grid.wrapper.on('change', function() {
            calculate_totals(frm);
        });
    },

    validate(frm) {
        // Recalculate before saving
        calculate_totals(frm);
    }
});


// === Helper Functions ===

// Sum q1–q4 in each row and update total
function calculate_row_total(row) {
    row.total = (flt(row.q1) || 0) + (flt(row.q2) || 0) + (flt(row.q3) || 0) + (flt(row.q4) || 0);
}

// Sum all child totals and set parent fields if needed
function calculate_totals(frm) {
    let total_target = 0;
    let total_achievement = 0;

    (frm.doc.disaggregation || []).forEach(row => {
        calculate_row_total(row);
        total_target += flt(row.total);
    });

    // Example: if you have total fields in parent
    // frm.set_value('total_disaggregation', total_target);

    // frm.refresh_field('disaggregation');
}
