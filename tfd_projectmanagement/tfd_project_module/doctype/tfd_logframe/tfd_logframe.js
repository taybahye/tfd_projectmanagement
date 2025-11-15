// =======================================
// Tree View Customization: TFD Logframe
// =======================================

frappe.treeview_settings['TFD Logframe'] = {
    breadcrumb: "TFD",
    title: __("TFD Logframe"),

    // Fetch children from server
    get_tree_nodes: "tfd_projectmanagement.doctype.tfd_logframe.tfd_logframe.get_logframe_children",

    // Sorting of tree nodes
    sort_function: function (a, b) {
        const type_order = ["Goal", "Outcome", "Output", "Impact", "Ind"];
        const type_diff = type_order.indexOf(a.data.type) - type_order.indexOf(b.data.type);
        if (type_diff !== 0) return type_diff;
        return (a.data.order_index || 0) - (b.data.order_index || 0);
    },

    // Label appearance in tree
    label: function (node) {
        const prefix = node.data.type ? `[${node.data.type}] ` : "";
        const order = node.data.order_index ? `${node.data.order_index}. ` : "";
        const name = node.data.indicator_name || node.value || "";
        return `${prefix}${order}${name}`;
    }
};


// =======================================
// Form Logic: Parent DocType (TFD Logframe)
// =======================================

frappe.ui.form.on('TFD Logframe', {
    
    // Auto-update main_order when index or parent changes
    order_parent: update_main_order,
    order_index: update_main_order,

    // Get type from TFD Main Indicators
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

    // Auto-set order_parent based on old_parent
    old_parent: function (frm) {
        if (frm.doc.old_parent) {
            frappe.db.get_value('TFD Logframe', frm.doc.old_parent, 'main_order')
                .then(r => {
                    if (r && r.message && r.message.order_index !== undefined) {
                        frm.set_value('order_parent', r.message.order_index);
                    } else {
                        frappe.msgprint(__('Could not find order_index for the selected Old Parent'));
                        frm.set_value('order_parent', null);
                    }
                });
        } else {
            frm.set_value('order_parent', null);
        }
    },

    refresh(frm) {
        frm.set_df_property('activities', 'hidden', 0);
    },

    validate(frm) {
        calculate_totals(frm);
    }
});


// =======================================
// Helper Functions for Totals
// =======================================

function calculate_row_total(row) {
    row.total = cint(flt(row.q1)) + cint(flt(row.q2)) + cint(flt(row.q3)) + cint(flt(row.q4));
}

function calculate_totals(frm) {
    let total_target = 0;

    (frm.doc.disaggregation || []).forEach(row => {
        calculate_row_total(row);
        total_target += cint(flt(row.total));
    });

    frm.refresh_field('disaggregation');
}


// =======================================
// Child Table Logic: TFD Logframe child
// =======================================

frappe.ui.form.on('TFD Logframe child', {
    total(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        let total = cint(flt(row.total));
        if (total <= 0) return;

        let divided = Math.floor(total / 4);
        let remainder = total - divided * 4;

        row.q1 = divided + (remainder > 0 ? 1 : 0);
        row.q2 = divided + (remainder > 1 ? 1 : 0);
        row.q3 = divided + (remainder > 2 ? 1 : 0);
        row.q4 = divided;

        frm.dirty();
        frm.refresh_field('disaggregation');
    },

    q1: update_row_total,
    q2: update_row_total,
    q3: update_row_total,
    q4: update_row_total
});

function update_row_total(frm, cdt, cdn) {
    let row = locals[cdt][cdn];
    row.total = cint(flt(row.q1)) + cint(flt(row.q2)) + cint(flt(row.q3)) + cint(flt(row.q4));
    frm.dirty();
    frm.refresh_field('disaggregation');
}


// =======================================
// NEW: Auto-update main_order (Fixed for Goals)
// =======================================

function update_main_order(frm) {
    const parent = frm.doc.order_parent;
    const index = frm.doc.order_index;

    if (index) {
        if (parent) {
            // Child node → parent.index
            frm.set_value("main_order", `${parent}.${index}`);
        } else {
            // Goal or top-level node → only index
            frm.set_value("main_order", `${index}`);
        }
    } else {
        frm.set_value("main_order", "");
    }
}
