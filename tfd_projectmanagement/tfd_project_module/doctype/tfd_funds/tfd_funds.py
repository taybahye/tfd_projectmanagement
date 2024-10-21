import frappe
from frappe.model.document import Document

class TFDFunds(Document):

    @frappe.whitelist()
    def calculate_population(self , env_name, percentage):
        environment = frappe.get_doc("TFD Governments", env_name)
        total_population = environment.population

        result_population = (float(percentage) / 100) * total_population

        # frappe.msgprint(str(result_population))
        return result_population


