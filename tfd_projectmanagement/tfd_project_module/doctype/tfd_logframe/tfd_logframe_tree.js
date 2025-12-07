// tfd_logframe_tree.js

frappe.provide("frappe.treeview_settings");

frappe.treeview_settings['TFD Logframe'] = {
    breadcrumb: "TFD",
    title: __("TFD Logframe"),
    
    // 1. Fetch children
    get_tree_nodes: "tfd_projectmanagement.tfd_project_module.doctype.tfd_logframe.tfd_logframe.get_logframe_children",

    // 2. Sorting
    sort_function: function (a, b) {
        const type_order = ["Goal", "Outcome", "Output", "Impact", "Ind"];
        const type_diff = type_order.indexOf(a.data.type) - type_order.indexOf(b.data.type);
        if (type_diff !== 0) return type_diff;
        return (a.data.order_index || 0) - (b.data.order_index || 0);
    },

    // 3. Label formatting
    label: function (node) {
        const prefix = node.data.type ? `[${node.data.type}] ` : "";
        // Use extended_type if available, otherwise use index
        const ref = node.data.extended_type ? `${node.data.extended_type}- ` : (node.data.order_index ? `${node.data.order_index}. ` : "");
        const name = node.data.indicator_name || node.value || "";
        return `${prefix}${ref}${name}`;
    },

    // 4. CUSTOM DIALOG LOGIC
    onload: function (treeview) {
        console.log("✅ TFD Logframe Tree Loaded"); // Look for this in Console (F12)

        // Override the "New" button function
        treeview.make_new_node = function (parent_node, parent_label, is_root) {
            console.log("⚡ Custom New Node Dialog Triggered");

            // Identify Parent
            let default_parent = "";
            if (!is_root && parent_node) {
                default_parent = parent_node;
            }

            let d = new frappe.ui.Dialog({
                title: __("New TFD Logframe (Custom)"), // Title changed to verify it's ours
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
                    // ⭐ THIS IS THE FIELD YOU WANTED ⭐
                    {
                        fieldtype: 'Data',
                        fieldname: 'extended_type',
                        label: __('Extended Type / Ref Code'),
                        description: "e.g. 1.1 or Goal-A (Manual Reference)"
                    },
                    { 
                        fieldtype: 'Link', fieldname: 'indicator_name', label: 'Indicator Name', 
                        options: 'TFD Main Indicators', reqd: 1 
                    },
                    { 
                        fieldtype: 'Int', fieldname: 'order_index', label: 'Order Index', reqd: 1, default: 1 
                    },
                    {
                        // Hidden field to ensure parent is linked
                        fieldtype: 'Link',
                        fieldname: 'parent_tfd_logframe',
                        label: 'Parent',
                        options: 'TFD Logframe',
                        hidden: 1, 
                        default: default_parent
                    }
                ],
                primary_action_label: __('Create'),
                primary_action: function (values) {
                    d.disable_primary_action();
                    
                    // Call the standard add_node API
                    frappe.call({
                        method: "frappe.desk.treeview.add_node",
                        args: {
                            doctype: "TFD Logframe",
                            parent: values.parent_tfd_logframe || treeview.root_value,
                            name: values.logframe_name, 
                            is_group: values.is_group,
                            data: values // Sends extended_type to backend
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
            d.show();
        };
    }
};