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
# API for Tree View (Updated & Fixed)
# =================+ww=========================
@frappe.whitelist()
def get_logframe_children(doctype, parent=None, is_root=False, **kwargs):
    
    # تحديد الفلتر
    filters = {}
    if parent:
        filters["parent_tfd_logframe"] = parent
    else:
        filters["parent_tfd_logframe"] = ["is", "not set"]

    # جلب البيانات
    # قمت بإضافة "is_group as expandable" ليظهر سهم التوسيع بجانب المجلدات
    children = frappe.get_all(
        "TFD Logframe",
        filters=filters,
        fields=["name as value", "indicator_name as title", "type", "order_index", "main_order", "is_group", "is_group as expandable"],
        order_by="order_index asc"
    )

    return children

# @frappe.whitelist()
# def get_logframe_children(doctype, parent=None, **kwargs):

#     children = frappe.get_all(
#         "TFD Logframe",
#         filters={"parent_logframe": parent} if parent else {},
#         fields=["name as value", "type", "is_group"]
#     )

#     # ⭐ ترتيب صارم
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
