frappe.listview_settings["Shift Type"] = {
    onload: function(listview) {
        listview.page.add_action_item(__("Bulk Mark Attendance"), () => {
            let selected = listview.get_checked_items();
            if (!selected.length) {
                frappe.msgprint(__("Please select at least one Shift Type"));
                return;
            }

            selected.forEach((d) => {
                frappe.db.get_doc("Shift Type", d.name).then(doc => {
                    if (!doc.enable_auto_attendance) {
                        frappe.show_alert({
                            message: __("Enable Auto Attendance for " + d.name),
                            indicator: 'red'
                        });
                        return;
                    }

                    if (!doc.process_attendance_after) {
                        frappe.show_alert({
                            message: __("Set Process Attendance After for " + d.name),
                            indicator: 'red'
                        });
                        return;
                    }

                    if (!doc.last_sync_of_checkin) {
                        frappe.show_alert({
                            message: __("Set Last Sync of Checkin for " + d.name),
                            indicator: 'red'
                        });
                        return;
                    }

                    frappe.call({
                        method: "tfd_projectmanagement.tfd_project_module.utils.process_auto_attendance_for_selected_shift",
                        args: { shift_name: d.name },
                        callback: function(r) {
                            frappe.show_alert({
                                message: __("Attendance processing started for " + d.name),
                                indicator: 'green'
                            });
                        }
                    });

                });
            });
        });
    }
};
