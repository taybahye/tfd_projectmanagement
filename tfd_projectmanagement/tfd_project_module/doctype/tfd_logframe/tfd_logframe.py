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



@frappe.whitelist()
def add_node(**args):  # إضافة النجمتين هنا ضروري جداً
    # الآن args ستعمل كقاموس يحتوي على (logframe_name, order_index, parent, إلخ)
    
    # 1. جلب بيانات الأب للحصول على الترتيب السابق
    parent_name = args.get("parent")
    parent_main_order = ""
    
    # التأكد أن الأب ليس هو اسم الـ Doctype نفسه (حالة الجذر)
    if parent_name and parent_name != "TFD Logframe":
        parent_main_order = frappe.db.get_value("TFD Logframe", parent_name, "main_order") or ""

    # 2. حساب الترتيب الجديد
    order_index = args.get("order_index") or 0
    if parent_main_order:
        final_main_order = f"{parent_main_order}.{order_index}"
    else:
        final_main_order = str(order_index)

    # 3. إنشاء السجل الجديد
    doc = frappe.get_doc({
        "doctype": "TFD Logframe",
        "logframe_name": args.get("logframe_name"),
        "is_group": frappe.utils.cint(args.get("is_group")), # تحويل للقيمة الرقمية 0 أو 1
        "parent_tfd_logframe": parent_name if parent_name != "TFD Logframe" else None,
        "indicator_name": args.get("indicator_name"), # تأكد من إضافة هذا السطر
        "order_index": order_index,
        "main_order": final_main_order,
        "order_parent": parent_main_order,
        # أضف أي حقول أخرى مطلوبة هنا مثل indicator_name
    })
    
    doc.insert()
    
    # فرابي يتوقع إرجاع اسم السجل الجديد لتحديث الشجرة
    return doc.name