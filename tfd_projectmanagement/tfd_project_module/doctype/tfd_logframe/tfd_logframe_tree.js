frappe.treeview_settings["TFD Logframe"] = {
    breadcrumb: "TFD",
    title: __("TFD Logframe"),

    // الربط مع دوال السيرفر
    // get_tree_nodes: "tfd_projectmanagement.tfd_project_module.doctype.tfd_logframe.tfd_logframe.get_logframe_children",
    
    // هذه الدالة هي التي ستقوم بعملية الحفظ والحساب في السيرفر
    add_tree_node: "tfd_projectmanagement.tfd_project_module.doctype.tfd_logframe.tfd_logframe.add_node",


    // تجاهل الحقول التي يتم تمريرها تلقائياً ولا نريد تكرارها
    ignore_fields: ["parent_tfd_logframe"],

    onload: function (treeview) {
        console.log("Treeview loaded using Frappe standard settings");
  
    }
};