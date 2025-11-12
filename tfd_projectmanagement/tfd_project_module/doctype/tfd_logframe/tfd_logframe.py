import frappe
from frappe.utils.nestedset import NestedSet

class TFDLogframe(NestedSet):
	def validate(self):
		if self.target and self.target != 0:
			self.achievement_percentage = round((self.acheivement / self.target) * 100, 2)
		else:
			self.achievement_percentage = 0

	def before_insert(self):
		# ✅ تحديد رقم الترتيب التلقائي
		if not self.order_index:
			self.order_index = self.get_next_order_index()

		# ✅ ضبط الاسم (autoname) يدويًا بطريقة آمنة
		self.set_safe_autoname()

	def get_next_order_index(self):
		filters = {}
		if self.parent_tfd_logframe:
			filters["parent_tfd_logframe"] = self.parent_tfd_logframe
		else:
			filters["parent_tfd_logframe"] = ["is", "not set"]

		last_index = frappe.db.get_value(
			"TFD Logframe",
			filters=filters,
			fieldname="MAX(order_index)"
		) or 0

		return int(last_index) + 1

	def set_safe_autoname(self):
		"""
		توليد اسم قصير وآمن (<= 140 حرف)
		"""
		name_parts = [
			self.type or "Unknown",
			str(self.order_index or 0),
			(self.indicator_name or "").replace(" ", "-")
		]
		full_name = "-".join(name_parts)
		if len(full_name) > 140:
			full_name = full_name[:137] + "..."  # تقصير للحماية
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
