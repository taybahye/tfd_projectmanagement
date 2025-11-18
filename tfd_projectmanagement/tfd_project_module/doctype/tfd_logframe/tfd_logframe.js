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


// ===================================================
// CUSTOM TREE QUICK ENTRY (REPLACES FRAPPE DEFAULT)
// ===================================================

frappe.treeview_settings['TFD Logframe'].onload = function (treeview) {
    treeview.make_new_node = function () {

        let d = new frappe.ui.Dialog({
            title: __("New Logframe Entry"),
            fields: [
                // Required fields FIRST
                { fieldtype: 'Link', fieldname: 'company', label: 'Company', options: 'Company', reqd: 1 },
                { fieldtype: 'Link', fieldname: 'indicator_name', label: 'Indicator Name', options: 'TFD Main Indicators', reqd: 1 },
                { fieldtype: 'Int', fieldname: 'order_index', label: 'Order Index', reqd: 1 },

                // Optional fields (tree quick entry normally never shows)
                { fieldtype: 'Link', fieldname: 'old_parent', label: 'Old Parent', options: 'TFD Logframe' },
                { fieldtype: 'Data', fieldname: 'order_parent', label: 'Order Parent' },
                { fieldtype: 'Data', fieldname: 'main_order', label: 'Main Order' },
                { fieldtype: 'Check', fieldname: 'is_group', label: 'Is Group' }
            ],

            primary_action(values) {

                // Auto fill parent from tree value
                values.parent = treeview.root_value;

                // Main order calculation (same logic as form)
                if (values.order_parent) {
                    values.main_order = `${values.order_parent}.${values.order_index}`;
                } else {
                    values.main_order = `${values.order_index}`;
                }

                frappe.call({
                    method: "frappe.desk.treeview.add_node",
                    args: {
                        doctype: "TFD Logframe",
                        parent: values.parent,
                        name: values.indicator_name,
                        data: values
                    },
                    callback: function () {
                        treeview.reload();
                        d.hide();
                    }
                });
            }
        });

        d.show();
    };
};



// =======================================
// FORM LOGIC
// =======================================

frappe.ui.form.on('TFD Logframe', {

    order_parent: update_main_order,
    order_index: update_main_order,
    

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

    old_parent: function (frm) {
        if (frm.doc.old_parent) {
            frappe.db.get_value('TFD Logframe', frm.doc.old_parent, 'main_order')
                .then(r => {
                    if (r && r.message && r.message.main_order != null) {
                        frm.set_value('order_parent', r.message.main_order);
                    } else {
                        frappe.msgprint(__('Could not find main_order for Parent'));
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
// Helper: Disaggregation Totals
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
// Child Table Logic
// =======================================

frappe.ui.form.on('TFD Logframe child', {
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
// Main Order Auto Update
// =======================================

function update_main_order(frm) {
    const parent = frm.doc.order_parent;
    const index = frm.doc.order_index;

    if (index) {
        if (parent) {
            frm.set_value("main_order", `${parent}.${index}`);
        } else {
            frm.set_value("main_order", `${index}`);
        }
    } else {
        frm.set_value("main_order", "");
    }
}
// ===================================================
// Tree View Custom Add Child Dialog for TFD Logframe
// ===================================================

frappe.treeview_settings['TFD Logframe'].onload = function(treeview) {

    treeview.make_new_node = function() {

        let dialog = new frappe.ui.Dialog({
            title: __("New TFD Logframe"),
            fields: [

                // ====== (1) Group Node ======
                {
                    fieldtype: 'Check',
                    fieldname: 'is_group',
                    label: __('Group Node')
                },

                // ====== (2) Company ======
                {
                    fieldtype: 'Link',
                    fieldname: 'company',
                    label: 'Company',
                    options: 'Company',
                    reqd: 1
                },

                // ====== (3) Logframe Name ======
                {
                    fieldtype: 'Link',
                    fieldname: 'logframe_name',
                    label: 'Logframe Name',
                    options: 'TFD Logframe Name',
                    reqd: 1
                },

                // ====== (4) Indicator Name ======
                {
                    fieldtype: 'Link',
                    fieldname: 'indicator_name',
                    label: 'Indicator Name',
                    options: 'TFD Main Indicators',
                    reqd: 1
                },

                // ====== (5) Order Index ======
                {
                    fieldtype: 'Int',
                    fieldname: 'order_index',
                    label: 'Order Index',
                    reqd: 1
                },

                // ====== (6) Parent TFD Logframe ======
                {
                    fieldtype: 'Link',
                    fieldname: 'parent_tfd_logframe',
                    label: 'Parent Logframe',
                    options: 'TFD Logframe'
                },

                // ====== (7) Old Parent ======
                {
                    fieldtype: 'Link',
                    fieldname: 'old_parent',
                    label: 'Old Parent',
                    options: 'TFD Logframe'
                },

                // ====== (8) Auto-Calculated Main Order ======
                {
                    fieldtype: 'Data',
                    fieldname: 'main_order',
                    label: 'Main Order',
                    read_only: 1
                }
            ],

            primary_action(values) {

                // Auto-generate main_order BEFORE saving
                if (values.order_index) {
                    if (values.parent_tfd_logframe) {
                        values.main_order = `${values.parent_tfd_logframe}.${values.order_index}`;
                    } else {
                        values.main_order = `${values.order_index}`;
                    }
                }

                // Create tree node
                frappe.call({
                    method: "frappe.desk.treeview.add_node",
                    args: {
                        doctype: "TFD Logframe",
                        parent: treeview.root_value,
                        name: values.logframe_name,   // تستخدم اسم اللوجفريم كاسم للداخل
                        data: values,
                    },
                    callback: function() {
                        treeview.reload();
                        dialog.hide();
                    }
                });
            }
        });

        // ===== Auto Refresh of main_order in dialog =====
        dialog.fields_dict.order_index.df.onchange = () => update_main_order(dialog);
        dialog.fields_dict.parent_tfd_logframe.df.onchange = () => update_main_order(dialog);

        function update_main_order(d) {
            let idx = d.get_value("order_index");
            let parent = d.get_value("parent_tfd_logframe");

            if (idx) {
                if (parent) {
                    d.set_value("main_order", `${parent}.${idx}`);
                } else {
                    d.set_value("main_order", `${idx}`);
                }
            }
        }

        dialog.show();
    };
};
