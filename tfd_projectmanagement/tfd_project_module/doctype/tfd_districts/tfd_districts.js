// Copyright (c) 2024, Amd Oudah Prosite  and contributors
// For license information, please see license.txt

// frappe.ui.form.on("TFD Districts", {
// 	refresh(frm) {

// 	},
// });
frappe.ui.form.on('TFD Districts', {
    city: function(frm) {
        if (frm.doc.city) {
            frm.set_query('directorate', function() {
                return {
                    filters: {
                        'government': frm.doc.city  // ربط المديريات بالمدينة المختارة
                    }
                };
            });
        } else {
            frm.set_query('directorate', function() {
                return {};
            });
        }
    }
});


