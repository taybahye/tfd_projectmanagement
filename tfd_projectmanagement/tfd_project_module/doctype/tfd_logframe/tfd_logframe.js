// =======================================
// Tree View Customization: TFD Logframe
// =======================================

frappe.treeview_settings['TFD Logframe'] = {
    breadcrumb: "TFD",
    title: __("TFD Logframe"),

    // 1. Fetch children from server
    get_tree_nodes: "tfd_projectmanagement.tfd_project_module.doctype.tfd_logframe.tfd_logframe.get_logframe_children",

    // 2. Sorting of tree nodes
    sort_function: function (a, b) {
        const type_order = ["Goal", "Outcome", "Output", "Impact", "Ind"];
        const type_diff = type_order.indexOf(a.data.type) - type_order.indexOf(b.data.type);
        if (type_diff !== 0) return type_diff;
        return (a.data.order_index || 0) - (b.data.order_index || 0);
    },

    // 3. Label appearance in tree
    label: function (node) {
        const prefix = node.data.type ? `[${node.data.type}] ` : "";
        const order = node.data.main_order ? `${node.data.main_order}- ` : ""; // Showing Main Order in Label
        const name = node.data.indicator_name || node.value || "";
        return `${prefix}${order}${name}`;
    },

    // 4. ONLOAD: Custom Quick Entry Dialog
    onload: function (treeview) {
        
        treeview.make_new_node = function (parent_node, parent_label, is_root) {
            
            // Determine Parent
            let default_parent = "";
            if (!is_root && parent_node) {
                default_parent = parent_node;
            }

            let d = new frappe.ui.Dialog({
                title: __("New TFD Logframe"),
                fields: [
                    {
                        fieldtype: 'Check',
                        fieldname: 'is_group',
                        label: __('Group Node')
                    },
                    { 
                        fieldtype: 'Link', fieldname: 'company', label: 'Company', 
                        options: 'Company', default: frappe.defaults.get_user_default("Company"), reqd: 1 
                    },
                    { 
                        fieldtype: 'Link', fieldname: 'logframe_name', label: 'Logframe Name', 
                        options: 'TFD Logframe Name', reqd: 1 
                    },
                    // --- NEW FIELD ADDED HERE ---
                    {
                        fieldtype: 'Data',
                        fieldname: 'extended_type',
                        label: __('Extended Type / Ref Code'),
                        description: "e.g., 1.1, Goal-A (Optional naming helper)"
                    },
                    // ----------------------------
                    { 
                        fieldtype: 'Link', fieldname: 'indicator_name', label: 'Indicator Name', 
                        options: 'TFD Main Indicators', reqd: 1 
                    },
                    { 
                        fieldtype: 'Section Break', label: 'Ordering' 
                    },
                    { 
                        fieldtype: 'Int', fieldname: 'order_index', label: 'Order Index', reqd: 1, default: 1 
                    },
                    { 
                        fieldtype: 'Data', 
                        fieldname: 'main_order', 
                        label: 'Main Order (Preview)', 
                        read_only: 1 
                    },
                    {
                        // Hidden field to store parent, ensures we pass it correctly
                        fieldtype: 'Link',
                        fieldname: 'parent_tfd_logframe',
                        label: 'Parent',
                        options: 'TFD Logframe',
                        hidden: 1, 
                        default: default_parent
                    }
                ],
                primary_action_label: __('Create'),

                primary_action: async function (values) {
                    d.disable_primary_action();

                    // Calculate final order before sending
                    let final_main_order = values.main_order; 
                    
                    frappe.call({
                        method: "frappe.desk.treeview.add_node",
                        args: {
                            doctype: "TFD Logframe",
                            parent: values.parent_tfd_logframe || treeview.root_value,
                            name: values.logframe_name, 
                            is_group: values.is_group,
                            data: {
                                ...values,
                                main_order: final_main_order // Ensure this is sent
                            }
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

            // Logic to auto-calculate Main Order when Index changes
            const update_main_order_preview = async () => {
                let idx = d.get_value('order_index');
                let parent = d.get_value('parent_tfd_logframe');
                
                if (idx) {
                    if (parent) {
                        // Fetch parent's main order
                        let r = await frappe.db.get_value('TFD Logframe', parent, 'main_order');
                        let parent_order = (r && r.message) ? r.message.main_order : "";
                        
                        if (parent_order) {
                            d.set_value('main_order', `${parent_order}.${idx}`);
                        } else {
                            d.set_value('main_order', `${parent}.${idx}`);
                        }
                    } else {
                        // Root Node
                        d.set_value('main_order', `${idx}`);
                    }
                }
            };

            // Trigger calculation on change
            d.fields_dict.order_index.df.onchange = () => update_main_order_preview();
            
            d.show();
            // Run once on open
            update_main_order_preview();
        };
    }
};

// =======================================
// Form Logic (Standard Form View)
// =======================================

frappe.ui.form.on('TFD Logframe', {
    order_parent: update_main_order_form,
    order_index: update_main_order_form,

    indicator_name: function (frm) {
        if (frm.doc.indicator_name) {
            frappe.db.get_value('TFD Main Indicators', frm.doc.indicator_name, 'type')
            .then(r => {
                if (r && r.message) {
                    frm.set_value('type', r.message.type);
                    
                    // Toggle Activities/Hide based on Type
                    let show_activities = ['Output', 'Indicator'].includes(r.message.type);
                    frm.set_df_property('activities', 'hidden', show_activities ? 0 : 1);
                }
            });
        }
    },

    refresh(frm) {
        // Any refresh logic
    }
});

// Helper for Form View Main Order Calculation
function update_main_order_form(frm) {
    const parent = frm.doc.order_parent;
    const index = frm.doc.order_index;
    if (index) {
        frm.set_value("main_order", parent ? `${parent}.${index}` : `${index}`);
    }
}