// Copyright (c) 2025, Amd Oudah Prosite  and contributors
// For license information, please see license.txt

frappe.ui.form.on("Indicator Collected Data", {
	onload(frm) {
		frm.set_query("indicator_logframe", function(doc) {
			return {
				filters: {
					logframe_name: doc.logframe_name,
                    collect_data : 1,
				}
			};
		});
      
	},
    indicator_logframe(frm) {

        frappe.call({
            method: "get_logframe_details",
            doc: frm.doc,
            
            callback(r) {
                if (r.message) {
                    frm.clear_table("collecting_data");

                    r.message.forEach(row => {
                        let child = frm.add_child("collecting_data");
                        child.type = row.type;
                    });

                    frm.refresh_field("collecting_data");
                }
            }
        });
    }       

});
