// Copyright (c) 2025, Amd Oudah Prosite  and contributors
// For license information, please see license.txt

frappe.ui.form.on("Indicator Collected Data", {

    // Event: logframe_name change
    // Fetches indicators for the selected logframe and populates the 'collecting_data' child table
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
                    console.log(r.message);
                    r.message.forEach(row => {
                        if(currentIndicator && currentIndicator != row.name){
                            let emptyRow = frm.add_child("collecting_data");
                            emptyRow.indicator_name_ar = ""; 
                            emptyRow.parent_type = "";
                            emptyRow.type = "";
                        }

                        let d = frm.add_child("collecting_data");
                        d.indicator_name_ar = row.indicator_name_ar;
                        d.parent_type = row.parent_type;
                        d.type = row.type;
                        d.logframe_indicator = row.name;
                        d.order_index = row.main_order;
                        d.indicator_parent = row.indicator_parent;
                        d.baseline = row.baseline;
                        d.target = row.target;
                        currentIndicator = row.name;
                    });

                    frm.refresh_field("collecting_data");
                }
            }
        });
    }
});
