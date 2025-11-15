# Copyright (c) 2025, Amd Oudah Prosite  and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

import frappe
from email_reply_parser import EmailReplyParser
from frappe import _, qb
from frappe.desk.reportview import get_match_cond
from frappe.model.document import Document
from frappe.query_builder import Interval
from frappe.query_builder.functions import Count, CurDate, Date, Sum, UnixTimestamp
from frappe.utils import add_days, flt, get_datetime, get_link_to_form, get_time, get_url, nowtime, today
from frappe.utils.user import is_website_user

from erpnext import get_default_company
from erpnext.controllers.queries import get_filters_cond
from erpnext.controllers.website_list_for_contact import get_customers_suppliers
from erpnext.setup.doctype.holiday_list.holiday_list import is_holiday


class TFDProjects(Document):
	
	def validate(self):
		# if not self.is_new():
		#     self.copy_from_template()  # nosemgrep
		# self.send_welcome_email()
		# self.update_costing()
		self.update_percent_complete()
		# self.validate_from_to_dates("expected_start_date", "expected_end_date")
		# self.validate_from_to_dates("actual_start_date", "actual_end_date")
	def update_project(self):
		"""Called externally by Activity"""
		self.update_percent_complete()
		self.save(ignore_permissions=True)  # تحفظ التغييرات في قاعدة البيانات


	def update_percent_complete(self):
		if self.status == "Completed":
			if (
				len(frappe.get_all("Project", dict(custom_tfd_project=self.name))) == 0
			):  # A project without tasks should be able to complete
				self.percent_complete_method = "Manual"
				self.percent_complete = 100

		if self.percent_complete_method == "Manual":
			if self.status == "Completed":
				self.percent_complete = 100
			return

		total = frappe.db.count("Project", dict(custom_tfd_project=self.name))

		if not total:
			self.percent_complete = 0
		else:
			if (self.percent_complete_method == "Task Completion" and total > 0) or (
				not self.percent_complete_method and total > 0
			):
				completed = frappe.db.sql(
					"""select count(name) from tabProject where
					custom_tfd_project=%s and status in ('Cancelled', 'Completed')""",
					self.name,
				)[0][0]
				self.percent_complete = flt(flt(completed) / total * 100, 2)

			if self.percent_complete_method == "Task Progress" and total > 0:
				progress = frappe.db.sql(
					"""select sum(custom_progress) from tabProject where
					custom_tfd_project=%s""",
					self.name,
				)[0][0]
				self.percent_complete = flt(flt(progress) / total, 2)

			if self.percent_complete_method == "Task Weight" and total > 0:
				weight_sum = frappe.db.sql(
					"""select sum(custom_weight) from tabProject where
					custom_tfd_project=%s""",
					self.name,
				)[0][0]
				weighted_progress = frappe.db.sql(
					"""select custom_progress, custom_weight from tabProject where
					custom_tfd_project=%s""",
					self.name,
					as_dict=1,
				)
				pct_complete = 0
				for row in weighted_progress:
					pct_complete += row["custom_progress"] * frappe.utils.safe_div(row["custom_weight"], weight_sum)
				self.percent_complete = flt(flt(pct_complete), 2)

		# don't update status if it is cancelled
		if self.status == "Cancelled":
			return

		self.status = "Completed" if self.percent_complete == 100 else "Open"

	
