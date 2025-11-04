frappe.ui.form.on('TFD Logframe', {
    indicator_name: function(frm) {
        if (frm.doc.indicator_name) {
            // جلب حقل type من TFD Indicators
            frappe.call({
                method: 'frappe.client.get_value',
                args: {
                    doctype: 'TFD Main Indicators',
                    filters: { name: frm.doc.indicator_name },
                    fieldname: ['type']
                },
                callback: function(r) {
                    if (r.message) {
                        // ضبط قيمة الحقل "type" في logframe
                        frm.set_value('type', r.message.type);

                        // إظهار الحقول بناءً على قيمة type
                        frm.set_df_property('type', 'hidden', 0); // إظهار حقل type

                        if (r.message.type === 'Output' || r.message.type === 'Indicator') {
                            frm.set_df_property('activities', 'hidden', 0); // إظهار حقل activities
                        } else {
                            frm.set_df_property('activities', 'hidden', 1); // إخفاء حقل activities
                        }
                    } else {
                        frappe.msgprint(__('Could not find the Indicator: ' + frm.doc.indicator_name));
                        frm.set_df_property('type', 'hidden', 1);
                        frm.set_df_property('activities', 'hidden', 1);
                    }
                }
            });
        } else {
            // إذا لم يتم اختيار indicator، إخفاء الحقول
            frm.set_df_property('type', 'hidden', 1);
            frm.set_df_property('activities', 'hidden', 1);
        }
    },

    refresh: function(frm) {
        // عند فتح النموذج لأول مرة، إخفاء حقل activities افتراضياً
        frm.set_df_property('activities', 'hidden', 0);
         calculate_totals(frm);
        
        // detect changes in the child table
        frm.fields_dict.indicators.grid.wrapper.on('change', function() {
            calculate_totals(frm);
        });
    },
    validate(frm) {
        // recalculate before saving
        calculate_totals(frm);
    }
});
function calculate_totals(frm) {
    let total_target = 0;
    let total_achievement = 0;

    (frm.doc.disaggregation || []).forEach(row => {
        total_target += flt(row.target);
        total_achievement += flt(row.achievement);
    });

    frm.set_value('target', total_target);
    frm.set_value('acheivement', total_achievement);
}