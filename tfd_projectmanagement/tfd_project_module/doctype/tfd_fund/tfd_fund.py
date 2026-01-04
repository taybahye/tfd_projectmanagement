import frappe
from frappe.model.document import Document

class TFDFund(Document):

    # Calculates population based on a government and a given percentage
    @frappe.whitelist()
    def calculate_population(self, env_name, percentage):
        if float(percentage) > 100:
            frappe.throw("النسبة المدخلة لا يمكن أن تكون أكبر من 100")

        environment = frappe.get_doc("TFD Governments", env_name)
        total_population = environment.population

        result_population = (float(percentage) / 100) * total_population

        # إرجاع نتيجة الحساب
        return result_population


