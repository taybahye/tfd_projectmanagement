# import frappe
# from frappe.model.document import Document

# class Funds(Document):
#     pass


# @frappe.whitelist()
# def get_bank_accounts(doctype=None, txt=None, filters=None, limit_start=0, limit_page_length=20, ignore_user_permissions=False):
#     # Log the raw filters
#     frappe.log("Raw filters: {}".format(filters))

#     if not filters:
#         filters = {}
#     else:
#         filters = frappe.parse_json(filters)

#     gets = frappe.get_all('Account', filters=filters, fields=['name', 'account_name'])
#     return [{'value': g['name'], 'label': g['account_name']} for g in gets]
