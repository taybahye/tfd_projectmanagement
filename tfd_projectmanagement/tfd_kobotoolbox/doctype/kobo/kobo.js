// Copyright (c) 2025, Amd Oudah Prosite  and contributors
// For license information, please see license.txt

frappe.ui.form.on("kobo", {

	// Adds a custom button to fetch Kobo forms when the form is refreshed
	refresh(frm) {
        frm.add_custom_button(__('Get kobo Froms'), function () {
			frappe.show_progress(__('Fetching Data'), 0, 100, __('Fetching...'));
		
            // /home/amdoudah/frappe-bench/apps/tfd_projectmanagement/tfd_projectmanagement/tfd_kobotoolbox/doctype/kobo/kobo.js
			frappe.call({
				method: "get_kobo_forms",
				doc: frm.doc,
				callback: function (response) {
					// frappe.show_progress(__('Fetching Data'), 100, 100, __('Completed!'));
					// frm.refresh_field("data_from_api");
					frm.refresh_field(response);
					frappe.msgprint(__('Data fetch completed!'));
				},
				always: function () {
					frappe.hide_progress(); // إخفاء progress بعد انتهاء العملية
				}
			});
		});
		
	},

	// get_instrument :


	// Triggers fetching and importing all Kobo forms and submissions
	get_instrument(frm){
        // console.log("test")
		alert('Starting Request...')
		frappe.call({
			method: "get_kobo_all_data",
			doc: frm.doc,
			callback: function (response) {
				// frappe.show_progress(__('Fetching Data'), 100, 100, __('Completed!'));
				// frm.refresh_field("data_from_api");
				// frm.refresh_field(response);
				// frappe.msgprint(__('Data fetch completed!'));
			},
			always: function () {
				frappe.hide_progress(); // إخفاء progress بعد انتهاء العملية
			}
		});

        
    },
});
