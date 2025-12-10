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



import frappe
import re  # ضروري للتعامل مع النصوص

@frappe.whitelist()
def get_logframe_children(doctype, parent=None, is_root=False, **kwargs):
    
    # 1. الفلتر الأساسي
    filters = {}
    if parent:
        filters["parent_tfd_logframe"] = parent
    else:
        filters["parent_tfd_logframe"] = ["is", "not set"]

    # 2. جلب البيانات من قاعدة البيانات (بدون ترتيب SQL)
    children = frappe.get_all(
        "TFD Logframe",
        filters=filters,
        fields=["name as value", "indicator_name as title", "type", "order_index", "is_group", "is_group as expandable"]
    )

    # 3. دالة حساب "وزن" كل صف للترتيب
    def get_sort_key(row):
        # --- أولاً: تحديد وزن النوع ---
        priority_map = {
            "ind": 1,       # يظهر أولاً
            "goal": 2,
            "outcome": 3,
            "output": 4,
            "activity": 5
        }
        
        # محاولة معرفة النوع من الحقل أو من الاسم
        t_type = (row.get("type") or "").lower()
        val_str = (row.get("value") or "").lower()
        
        if not t_type:
            if "ind" in val_str: t_type = "ind"
            elif "outcome" in val_str: t_type = "outcome"
            elif "output" in val_str: t_type = "output"
            elif "activity" in val_str: t_type = "activity"
            elif "goal" in val_str: t_type = "goal"
        
        # الوزن الافتراضي 99 للعناصر غير المعروفة
        type_weight = priority_map.get(t_type, 99)

        # --- ثانياً: استخراج الأرقام للترتيب (Natural Sort) ---
        # نبحث عن رقم في نهاية النص مثل "-1.10" أو "-1.2"
        # Regex: يبحث عن شرطة متبوعة بأرقام ونقاط في نهاية السطر
        numbers = []
        match = re.search(r'-(\d+(\.\d+)*)$', row.get("value") or "")
        
        if match:
            num_str = match.group(1) # يأخذ النص "1.10"
            # يحوله إلى قائمة أرقام [1, 10]
            numbers = [int(n) for n in num_str.split('.') if n.isdigit()]
        else:
            # إذا لم يجد رقماً في الاسم، يستخدم order_index كاحتياطي
            numbers = [row.get("order_index") or 0]

        # نرجع (وزن النوع، قائمة الأرقام) ليقوم بايثون بالمقارنة
        return (type_weight, numbers)

    # 4. تطبيق الترتيب على القائمة قبل إرسالها
    children.sort(key=get_sort_key)

    return children
