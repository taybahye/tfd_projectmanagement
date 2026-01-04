import frappe
from frappe.utils.nestedset import NestedSet

class TFDLogframe(NestedSet):

    def validate(self):
        # Calculate achievement percentage based on target and achievement fields
        if self.target and self.target != 0:
            self.achievement_percentage = round((self.acheivement / self.target) * 100, 2)
        else:
            self.achievement_percentage = 0

    def before_insert(self):
        #  1) If the type is 'Goal', it must not have a parent (it acts as a ROOT node only)
        if self.type == "Goal":
            self.parent_tfd_logframe = None

        #  2) Determine the correct sequence/order index if not provided
        if not self.order_index:
            self.order_index = self.get_next_order_index()

        #  3) Generate the final record name (dynamically based on parent and type)
        self.set_safe_autoname()

    def get_next_order_index(self):
        """Returns the next sequence number within the same parent node"""
        filters = {}

        # If it has a parent -> get the maximum order_index within that parent
        if self.parent_tfd_logframe:
            filters["parent_tfd_logframe"] = self.parent_tfd_logframe
        else:
            # For ROOT nodes: Applies to 'Goal' type only
            filters["parent_tfd_logframe"] = ["is", "not set"]

        last_index = frappe.db.get_value(
            "TFD Logframe",
            filters=filters,
            fieldname="MAX(order_index)"
        ) or 0

        return int(last_index) + 1

    def set_safe_autoname(self):
        """
        Final Name Format:
        {parent_name or ROOT}-{type}-{order_index}
        """
        # Logic for naming prefix (uses ROOT for top-level nodes)
        parent_name = self.parent_tfd_logframe if self.parent_tfd_logframe else "ROOT"

        name_parts = [
            parent_name,
            self.type or "Unknown",
            str(self.order_index or 0)
        ]

        full_name = "-".join(name_parts)

        # Character length protection (Max 140 chars)
        if len(full_name) > 140:
            full_name = full_name[:137] + "..."

        self.name = full_name


# ==========================================
# API for Tree View (Updated & Fixed)
# ==========================================
@frappe.whitelist()
def get_logframe_children(doctype, parent=None, is_root=False, **kwargs):
    
    # Define filters based on whether a parent node is selected
    filters = {}
    if parent:
        filters["parent_tfd_logframe"] = parent
    else:
        filters["parent_tfd_logframe"] = ["is", "not set"]

    # Fetch records
    # 'is_group as expandable' is added to show the expansion arrow next to folders
    children = frappe.get_all(
        "TFD Logframe",
        filters=filters,
        fields=["name as value", "indicator_name as title", "type", "order_index", "main_order", "is_group", "is_group as expandable"],
        order_by="order_index asc"
    )

    return children
