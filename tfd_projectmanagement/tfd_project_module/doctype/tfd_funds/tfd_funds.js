frappe.ui.form.on("TFD Funds", {
    refresh: function(frm) {
        frm.set_query('bank', function() {
            return {
                filters: {
                    account_type: 'Bank' 
                }
            };
        });

       
    },

   
});



frappe.ui.form.on("TFD Governments Child", {
    percentage: function(frm, cdt , cdn) {
        let row = locals[cdt][cdn];

        if (row.goverment && row.percentage) {
            frappe.call({
                method: "calculate_population",
                doc:frm.doc,
                args: {
                    env_name: row.goverment,
                    percentage: row.percentage,
                },
                callback: function(r) {
                    if (r.message) {
                        // تحديث الحقل بالعدد السكاني المحسوب
                        frappe.model.set_value(cdt, cdn, 'population', r.message);
                    }
                }
            });
        }
    },
});