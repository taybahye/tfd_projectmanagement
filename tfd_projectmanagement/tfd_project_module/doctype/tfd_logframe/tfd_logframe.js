// 1. Tree View Customization

frappe.treeview_settings['TFD Logframe'] = {
    breadcrumb: "TFD",
    title: __("TFD Logframe"),

    // Fetches child nodes from the server
    get_tree_nodes: "tfd_projectmanagement.tfd_project_module.doctype.tfd_logframe.tfd_logframe.get_logframe_children",

    // Sorts nodes by type priority, then by numeric ID
    sort_function: function (a, b) {
        
        // 1. Define priority for each type
        const typePriority = { 
            "ind": 1, "outcome": 2, "output": 3, "activity": 4, "goal": 5 
        };
        
        let typeA = (a.data.type || "").toLowerCase();
        let typeB = (b.data.type || "").toLowerCase();
        
        let weightA = typePriority[typeA] || 99;
        let weightB = typePriority[typeB] || 99;
        
        // Sort by weight first
        if (weightA !== weightB) return weightA - weightB;

        // 2. Smart numeric sort (treats "10" as greater than "2")
        let valA = String(a.data.value || "").trim();
        let valB = String(b.data.value || "").trim();

        return valA.localeCompare(valB, undefined, { numeric: true, sensitivity: 'base' });
    },

    // Sets the display text for each node in the tree
    label: function (node) {
        const prefix = node.data.type ? `[${node.data.type}] ` : "";
        const order = node.data.main_order ? `${node.data.main_order}- ` : (node.data.order_index ? `${node.data.order_index}. ` : "");
        const name = node.data.indicator_name || node.value || "";
        return `${prefix}${order}${name}`;
    },

    // 2. Custom Quick Entry Dialog
    onload: function (treeview) {

        // Function to create the pop-up window for adding new nodes
        treeview.make_new_node = function (parent_node, parent_label, is_root) {
            
            // Set default parent based on where the user clicked
            let default_parent = (!is_root && parent_node) ? parent_node : "";

            let d = new frappe.ui.Dialog({
                title: __("New TFD Logframe"),
                fields: [
                    { fieldtype: 'Check', fieldname: 'is_group', label: __('Group Node') },
                    { 
                        fieldtype: 'Link', fieldname: 'company', label: 'Company', 
                        options: 'Company', default: frappe.defaults.get_user_default("Company"), reqd: 1 
                    },
                    { 
                        fieldtype: 'Link', fieldname: 'logframe_name', label: 'Logframe Name', 
                        options: 'TFD Logframe Name', reqd: 1 
                    },
                    { 
                        fieldtype: 'Link', fieldname: 'indicator_name', label: 'Indicator Name', 
                        options: 'TFD Main Indicators', reqd: 1 
                    },
                    { 
                        fieldtype: 'Int', fieldname: 'order_index', label: 'Order Index', reqd: 1 
                    },
                    
                    // --- Hidden fields for calculations ---
                    { fieldtype: 'Data', fieldname: 'order_parent', label: 'Hidden Parent Order', hidden: 1 }, 
                    { fieldtype: 'Link', fieldname: 'parent_tfd_logframe', label: 'Real Parent', options: 'TFD Logframe', hidden: 1, default: default_parent },
                    // --------------------------------

                    { fieldtype: 'Section Break', label: 'Order Details' },
                    { 
                        fieldtype: 'Link', 
                        fieldname: 'dialog_parent', 
                        label: 'Parent Logframe', 
                        options: 'TFD Logframe',
                        default: default_parent,
                        read_only: 0 
                    },
                    { 
                        fieldtype: 'HTML', 
                        fieldname: 'order_preview_html', 
                        label: 'Preview'
                    }
                ],
                primary_action_label: __('Create'),

                // Action when "Create" button is clicked
                primary_action: async function (values) {
                    d.disable_primary_action();

                    values.parent_tfd_logframe = values.dialog_parent; 
                    
                    // Calculate the final hierarchy order (e.g., 1.1.2)
                    let final_order_data = await get_calculated_order_data(values.dialog_parent, values.order_index);
                    values.main_order = final_order_data.full_order;
                    values.order_parent = final_order_data.parent_order_str;

                    // Server call to save the new node
                    frappe.call({
                        method: "frappe.desk.treeview.add_node",
                        args: {
                            doctype: "TFD Logframe",
                            parent: values.parent_tfd_logframe || treeview.root_value,
                            name: values.logframe_name, 
                            is_group: values.is_group,
                            data: values 
                        },
                        callback: function (r) {
                            d.enable_primary_action();
                            if (!r.exc) {
                                treeview.reload();
                                d.hide();
                            }
                        }
                    });
                }
            });

            // Helper: Calculates the nested order string (e.g., Parent.Index)
            const get_calculated_order_data = async (parent_name, index) => {
                if (!parent_name) return { full_order: `${index}`, parent_order_str: "" };
                
                let r = await frappe.db.get_value('TFD Logframe', parent_name, 'main_order');
                let p_order = (r && r.message) ? r.message.main_order : "";
                
                if(p_order) {
                    return { full_order: `${p_order}.${index}`, parent_order_str: p_order };
                } else {
                    return { full_order: `${parent_name}.${index}`, parent_order_str: "" };
                }
            };

            // Helper: Updates the visual preview in the dialog
            const update_preview = async () => {
                let idx = d.get_value('order_index');
                let par = d.get_value('dialog_parent');
                
                let html_content = "";
                
                if(idx) {
                    let calc_data = await get_calculated_order_data(par, idx);
                    
                    d.set_value('order_parent', calc_data.parent_order_str);
                    d.set_value('parent_tfd_logframe', par);

                    html_content = `
                        <div style="padding: 10px; background-color: #e2e3e5; border: 1px solid #d6d8db; color: #383d41; border-radius: 4px;">
                             Parent Order: <strong>${calc_data.parent_order_str || "Root"}</strong> <br>
                             Your Index: <strong>${idx}</strong>
                        </div>
                        <div style="margin-top: 5px; padding: 10px; background-color: #d1e7dd; border: 1px solid #badbcc; color: #0f5132; border-radius: 4px;">
                            <strong>Final Main Order:</strong> ${calc_data.full_order}
                        </div>
                    `;
                } else {
                     html_content = `<div style="color: #777;">Please enter an index...</div>`;
                }
                
                d.fields_dict.order_preview_html.$wrapper.html(html_content);
            };

            // Update preview when inputs change
            d.fields_dict.order_index.df.onchange = () => update_preview();
            d.fields_dict.dialog_parent.df.onchange = () => update_preview();

            d.show();
            setTimeout(() => update_preview(), 300);
        };
    }
};


// 3. Form View Logic

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
    old_parent: function (frm) {
        if (frm.doc.old_parent) {
            frappe.db.get_value('TFD Logframe', frm.doc.old_parent, 'main_order')
                .then(r => {
                    if (r && r.message && r.message.main_order != null) {
                        frm.set_value('order_parent', r.message.main_order);
                    } else {
                        frm.set_value('order_parent', null);
                    }
                });
        } else {
            frm.set_value('order_parent', null);
        }
    },

    refresh(frm) {
        // Run code when form loads
    },

    validate(frm) {
        // Run totals calculation before saving
        calculate_totals(frm);
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