// Copyright (c) 2024, Amd Oudah Prosite  and contributors
// For license information, please see license.txt

// frappe.ui.form.on("TFD Villages", {
// 	refresh(frm) {

// 	},
// });
frappe.ui.form.on('TFD Villages', {
    city: function(frm) {
        if (frm.doc.city) {
            frm.set_query('directorate', function() {
                return {
                    filters: {
                        'government': frm.doc.city 
                    }
                };
            });
        } else {
            frm.set_query('directorate', function() {
                return {};
            });
        }
    },
    directorate: function(frm) {
        if (frm.doc.directorate) {
            frm.set_query('disticts', function() {
                return {
                    filters: {
                        'directorate': frm.doc.directorate  
                    }
                };
            });
        } else {
            frm.set_query('disticts', function() {
                return {};
            });
        }
    }
});