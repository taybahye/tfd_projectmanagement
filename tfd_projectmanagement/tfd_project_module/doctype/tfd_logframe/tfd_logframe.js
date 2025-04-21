frappe.ui.form.on('TFD Logframe', {
    indicator_name: function(frm) {
        if (frm.doc.indicator_name) {
            // جلب حقل type من TFD Indicators
            frappe.call({
                method: 'frappe.client.get_value',
                args: {
                    doctype: 'TFD Indicators',
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
    }
});
