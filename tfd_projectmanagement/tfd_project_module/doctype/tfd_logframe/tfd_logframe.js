

frappe.ui.form.on('TFD Logframe', {

    // Recalculate order string when parent or index changes
    order_parent: update_main_order_form,
    order_index: update_main_order_form,

    // Fetches type and visibility settings when indicator is chosen
    indicator_name: function (frm) {
        if (frm.doc.indicator_name) {
            frappe.call({
                method: 'frappe.client.get_value',
                args: {
                    doctype: 'TFD Main Indicators',
                    filters: { name: frm.doc.indicator_name },
                    fieldname: ['type']
                },
                callback: function (r) {
                    if (r.message) {
                        frm.set_value('type', r.message.type);
                        frm.set_df_property('type', 'hidden', 0);

                        // Show Activities table only for Output or Indicator types
                        if (['Output', 'Indicator'].includes(r.message.type)) {
                            frm.set_df_property('activities', 'hidden', 0);
                        } else {
                            frm.set_df_property('activities', 'hidden', 1);
                        }
                    } else {
                        frappe.msgprint(__('Could not find the Indicator: ' + frm.doc.indicator_name));
                        frm.set_df_property('type', 'hidden', 1);
                        frm.set_df_property('activities', 'hidden', 1);
                    }
                }
            });
        } else {
            frm.set_df_property('type', 'hidden', 1);
            frm.set_df_property('activities', 'hidden', 1);
        }
    },

    // Fetches order data from a manually selected old parent
    // old_parent: function (frm) {
    //     if (frm.doc.old_parent) {
    //         frappe.db.get_value('TFD Logframe', frm.doc.old_parent, 'main_order')
    //             .then(r => {
    //                 if (r && r.message && r.message.main_order != null) {
    //                     frm.set_value('order_parent', r.message.main_order);
    //                 } else {
    //                     frm.set_value('order_parent', null);
    //                 }
    //             });
    //     } else {
    //         frm.set_value('order_parent', null);
    //     }
    // },

    refresh(frm) {
        // Run code when form loads
    },

    async validate(frm) {
            // استخدم await للتأكد من انتهاء الجلب قبل الحسابات
            await frm.trigger('get_parent_order');
            
            // الآن تنفيذ الحسابات
            calculate_totals(frm);
        },

    get_parent_order: async function(frm) {
        // نستخدم old_parent أو الحقل المسؤول عن الربط بالشجرة
        let parent_field = frm.doc.old_parent || frm.doc.parent_tfd_logframe;
        
        if (parent_field) {
            let r = await frappe.db.get_value('TFD Logframe', parent_field, 'main_order');
            if (r && r.message) {
                frm.set_value('order_parent', r.message.main_order);
            }
        }
    },
    onload(frm) {
        frm.fields_dict.disaggregation.grid.get_field("parent_type").get_query = function() {
            return {
                filters: {
                    is_group: 1
                }
            };
        };

        frm.fields_dict.disaggregation.grid.get_field("type").get_query = function() {
            return {
                filters: {
                    is_group: 0
                }
            };
        };
    }
});


// 4. Helper Functions & Child Table Logic

// Updates the main_order field in the form
function update_main_order_form(frm) {
    const parent = frm.doc.order_parent;
    const index = frm.doc.order_index;

    if (index) {
        frm.set_value("main_order", parent ? `${parent}.${index}` : `${index}`);
    } else {
        frm.set_value("main_order", "");
    }
}

// Sums Q1, Q2, Q3, and Q4 for a single row
function calculate_row_total(row) {
    row.total = cint(flt(row.q1)) + cint(flt(row.q2)) + cint(flt(row.q3)) + cint(flt(row.q4));
}

// Sums all row totals into a grand total
function calculate_totals(frm) {
    let total_target = 0;
    (frm.doc.disaggregation || []).forEach(row => {
        calculate_row_total(row);
        total_target += cint(flt(row.total));
    });
    frm.refresh_field('disaggregation');
}

// Child Table Triggers
frappe.ui.form.on('TFD Logframe child', {
    // Automatically splits total into 4 quarters when "total" is typed
    total(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        let total = cint(flt(row.total));
        if (total <= 0) return;

        let div = Math.floor(total / 4);
        let rem = total - div * 4;

        row.q1 = div + (rem > 0 ? 1 : 0);
        row.q2 = div + (rem > 1 ? 1 : 0);
        row.q3 = div + (rem > 2 ? 1 : 0);
        row.q4 = div;

        frm.dirty();
        frm.refresh_field('disaggregation');
    },

    // Recalculate total if any quarter is changed manually
    q1: update_row_total_trigger,
    q2: update_row_total_trigger,
    q3: update_row_total_trigger,
    q4: update_row_total_trigger
});

// Helper: Updates row total and marks form as changed
function update_row_total_trigger(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    row.total = cint(flt(row.q1)) + cint(flt(row.q2)) + cint(flt(row.q3)) + cint(flt(row.q4));
    frm.dirty();
    frm.refresh_field('disaggregation');
}