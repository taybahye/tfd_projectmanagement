import frappe
from frappe.utils.nestedset import NestedSet

class TFDLogframe(NestedSet):

    # Checks data before saving to calculate the achievement percentage
    def validate(self):
        if self.target and self.target != 0:
            self.achievement_percentage = round((self.acheivement / self.target) * 100, 2)
        else:
            self.achievement_percentage = 0

    # Runs logic before creating a new record
    def before_insert(self):
        # 1) If type is Goal -> it must have no parent (logic only for ROOT)
        if self.type == "Goal":
            self.parent_tfd_logframe = None

        # 2) Set the correct order number
        if not self.order_index:
            self.order_index = self.get_next_order_index()

        # 3) Generate the final name (depends on parent "visually")
        self.set_safe_autoname()

    # Finds the next available order number under the same parent
    def get_next_order_index(self):
        """Gives a sequence number inside the same parent"""
        filters = {}

        # If it has a parent -> get the last order_index inside that parent
        if self.parent_tfd_logframe:
            filters["parent_tfd_logframe"] = self.parent_tfd_logframe
        else:
            # ROOT nodes: Goal only
            filters["parent_tfd_logframe"] = ["is", "not set"]

        last_index = frappe.db.get_value(
            "TFD Logframe",
            filters=filters,
            fieldname="MAX(order_index)"
        ) or 0

        return int(last_index) + 1

    # Formats the record ID/Name in a specific way
    def set_safe_autoname(self):
        """
        Final Name format:
        {parent or ROOT}-{type}-{order_index}
        """
        # Name only—not actual parent field
        parent_name = self.parent_tfd_logframe if self.parent_tfd_logframe else "ROOT"

        name_parts = [
            parent_name,
            self.type or "Unknown",
            str(self.order_index or 0)
        ]

        full_name = "-".join(name_parts)

        # Protect length (max 140 chars)
        if len(full_name) > 140:
            full_name = full_name[:137] + "..."

        self.name = full_name


# API for Tree View (Updated & Fixed)
@frappe.whitelist()
def get_logframe_children(doctype, parent=None, is_root=False, **kwargs):
    
    # Define the filter
    filters = {}
    if parent:
        filters["parent_tfd_logframe"] = parent
    else:
        filters["parent_tfd_logframe"] = ["is", "not set"]

    # Fetch data
    # Added "is_group as expandable" so the expansion arrow appears next to folders
    children = frappe.get_all(
        "TFD Logframe",
        filters=filters,
        fields=["name as value", "indicator_name as title", "type", "order_index", "main_order", "is_group", "is_group as expandable"],
        order_by="order_index asc"
    )

    return children

# Note: The code below was commented out in your original file.
# It contains logic for strict sorting by type priority.
# @frappe.whitelist()
# def get_logframe_children(doctype, parent=None, **kwargs):

#     children = frappe.get_all(
#         "TFD Logframe",
#         filters={"parent_logframe": parent} if parent else {},
#         fields=["name as value", "type", "is_group"]
#     )

#     # Strict sorting priority
#     priority = {
#         "Ind": 1,
#         "Outcome": 2,
#         "Output": 3,
#         "Activity": 4,
#         "Goal": 5
#     }

#     def sort_key(row):
#         p = priority.get(row.type, 99)

#         import re
#         m = re.search(r"\d+", row.value or "")
#         num = int(m.group()) if m else 0

#         return (p, num)

#     children.sort(key=sort_key)

#     return children