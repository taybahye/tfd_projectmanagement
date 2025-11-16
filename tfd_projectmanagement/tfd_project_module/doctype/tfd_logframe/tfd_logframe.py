import frappe
from frappe.utils.nestedset import NestedSet

class TFDLogframe(NestedSet):

    def validate(self):
        if self.target and self.target != 0:
            self.achievement_percentage = round((self.acheivement / self.target) * 100, 2)
        else:
            self.achievement_percentage = 0

    def before_insert(self):

        # ⭐ 1) إذا النوع Goal → لازم يكون بدون parent (ROOT منطقي فقط)
        if self.type == "Goal":
            self.parent_tfd_logframe = None

        # ⭐ 2) تحديد رقم الترتيب الصحيح
        if not self.order_index:
            self.order_index = self.get_next_order_index()

        # ⭐ 3) توليد الاسم النهائي (يعتمد على parent "ظاهريًا")
        self.set_safe_autoname()

    def get_next_order_index(self):
        """يعطي رقم ترتيب داخل نفس الـ parent"""

        filters = {}

        # إذا له parent → نجيب آخر order_index داخل نفس parent
        if self.parent_tfd_logframe:
            filters["parent_tfd_logframe"] = self.parent_tfd_logframe
        else:
            # ROOT nodes: Goal فقط
            filters["parent_tfd_logframe"] = ["is", "not set"]

        last_index = frappe.db.get_value(
            "TFD Logframe",
            filters=filters,
            fieldname="MAX(order_index)"
        ) or 0

        return int(last_index) + 1

    def set_safe_autoname(self):
        """
        الاسم النهائي:
        {parent أو ROOT}-{type}-{order_index}
        """

        # الاسم فقط—not actual parent field
        parent_name = self.parent_tfd_logframe if self.parent_tfd_logframe else "ROOT"

        name_parts = [
            parent_name,
            self.type or "Unknown",
            str(self.order_index or 0)
        ]

        full_name = "-".join(name_parts)

        # حماية الطول
        if len(full_name) > 140:
            full_name = full_name[:137] + "..."

        self.name = full_name


# ==========================================
# API for Tree View
# ==========================================
@frappe.whitelist()
def get_logframe_children(parent=None):
    filters = {"parent_tfd_logframe": parent} if parent else {"parent_tfd_logframe": ["is", "not set"]}

    children = frappe.get_all(
        "TFD Logframe",
        filters=filters,
        fields=["name as value", "indicator_name", "type", "order_index", "is_group"],
        order_by="order_index asc"
    )
    return children
