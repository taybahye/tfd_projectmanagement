# Copyright (c) 2024, Amd Oudah Prosite  and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class TFDLogframeName(Document):
	pass



@frappe.whitelist()
def duplicate_logframe_tree(old_logframe_name, new_logframe_name):
    """
    Duplicate Logframe tree with debug prints to track duplicate names
    """
    frappe.log(f"Starting duplication: {old_logframe_name} -> {new_logframe_name}")

    new_lfname = frappe.get_doc({
        "doctype": "TFD Logframe Name",
        "log_frame_name": new_logframe_name
    }).insert(ignore_permissions=True)

    parent_map = {}
    root_nodes = frappe.get_all(
        "TFD Logframe",
        filters={"logframe_name": old_logframe_name, "old_parent": None},
        order_by="idx asc"
    )

    nodes_to_copy = root_nodes.copy()

    while nodes_to_copy:
        current = nodes_to_copy.pop(0)
        node = frappe.get_doc("TFD Logframe", current.name)

        frappe.log(f"\nCopying node: {node.name}")
        frappe.log(f"  old_parent: {node.old_parent}, parent_tfd_logframe: {node.parent_tfd_logframe}")

        new_node = frappe.get_doc(node.as_dict())
        new_node.name = None
        new_node.logframe_name = new_lfname.name
        new_node.old_parent = parent_map.get(node.old_parent)
        new_node.parent_tfd_logframe = parent_map.get(node.parent_tfd_logframe)

        # إعادة حساب الاسم بناء على Expression
        # new_node.run_method("autoname")
        frappe.log(f"  Generated new name: {new_node.name}")

        try:
            new_node.insert(ignore_permissions=True)
            frappe.log(f"  Node inserted successfully: {new_node.name}")
        except frappe.DuplicateEntryError as e:
            frappe.log(f"  DUPLICATE ERROR for node {new_node.name} -> {e}")
            raise e

        parent_map[node.name] = new_node.name

        # إضافة الأطفال للقائمة
        children = frappe.get_all(
            "TFD Logframe",
            filters={"old_parent": node.name},
            order_by="idx asc"
        )
        frappe.log(f"  Adding {len(children)} children to queue")
        nodes_to_copy.extend(children)

    frappe.log("Duplication finished successfully!")
    return {"status": "success", "new_logframe_name": new_lfname.name}