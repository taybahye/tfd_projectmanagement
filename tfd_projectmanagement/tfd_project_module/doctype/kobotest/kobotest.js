// Copyright (c) 2024, Amd Oudah Prosite  and contributors
// For license information, please see license.txt


 frappe.ui.form.on("Kobotest", {
 	refresh(frm) {
     
        


	},
    get(frm){
		alert('ww')
        frappe.call({
			method: "get_form_data",
			doc: frm.doc,
			callback: function(r) {
                // frm.refresh_field("pages");
                // frm.refresh_field("answers");	
			}
		});
    },
 });

