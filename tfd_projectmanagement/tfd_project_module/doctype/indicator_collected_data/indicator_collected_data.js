// Copyright (c) 2025, Amd Oudah Prosite  and contributors
// For license information, please see license.txt

frappe.ui.form.on("Indicator Collected Data", {
	// onload(frm) {
	// 	frm.set_query("indicator_logframe", function(doc) {
	// 		return {
	// 			filters: {
	// 				logframe_name: doc.logframe_name,
    //                 collect_data : true,
	// 			}
	// 		};
	// 	});
      
	// },
    // indicator_logframe(frm) {

    //     frappe.call({
    //         method: "get_logframe_details",
    //         doc: frm.doc,
            
    //         callback(r) {
    //             if (r.message) {
    //                 frm.clear_table("collecting_data");

    //                 r.message.forEach(row => {
    //                     let child = frm.add_child("collecting_data");
    //                     child.type = row.type;
    //                 });

    //                 frm.refresh_field("collecting_data");
    //             }
    //         }
    //     });
    // } ,
logframe_name: function(frm) {
    if (!frm.doc.logframe_name) return;

    frappe.call({
        method: "tfd_projectmanagement.tfd_project_module.doctype.indicator_collected_data.indicator_collected_data.get_logframe_indicators",
        args: {
            logframe_name: frm.doc.logframe_name
        },
        callback: function(r) {
            if (r.message) {
                frm.clear_table("collecting_data");

                let currentIndicator = null;

                r.message.forEach(row => {
                    // إذا تغير المؤشر، نضيف صف فارغ قبل المؤشر الجديد
                    if(currentIndicator && currentIndicator != row.name){
                        let emptyRow = frm.add_child("collecting_data");
                        emptyRow.indicator_name_ar = ""; // صف فارغ
                        emptyRow.type = "";
                    }

                    let d = frm.add_child("collecting_data");
                    d.indicator_name_ar = row.indicator_name_ar;
                    d.type = row.type;

                    currentIndicator = row.name;
                });

                frm.refresh_field("collecting_data");
            }
        }
    });
}


});
