// Copyright (c) 2024, Amd Oudah Prosite  and contributors
// For license information, please see license.txt

frappe.ui.form.on("TFD Logframe Name", {
    refresh: function(frm) {
        // Button Duplicate Tree
        frm.add_custom_button("Duplicate Tree", function() {
            frappe.prompt([
                {"fieldname": "new_name", "fieldtype": "Data", "label": "New Logframe Name", "reqd": 1}
            ],
            function(values){
                frappe.call({
                    method: "tfd_projectmanagement.tfd_project_module.doctype.tfd_logframe_name.tfd_logframe_name.duplicate_logframe_tree",
                    args: {
                        old_logframe_name: frm.doc.name,
                        new_logframe_name: values.new_name
                    },
                    callback: function(r) {
                        if(r.message.status === "success") {
                            frappe.msgprint("Logframe tree duplicated as: " + r.message.new_logframe_name);
                            frappe.set_route("Form", "TFD Logframe Name", r.message.new_logframe_name);
                        }
                    }
                });
            },
            "Enter New Name",
            "Duplicate"
            );
        });

        frm.add_custom_button("Open Logframe", function() {
            frappe.set_route("List", "TFD Logframe", {
                logframe_name: frm.doc.name
        });
});
    }
});