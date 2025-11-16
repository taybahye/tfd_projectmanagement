# Copyright (c) 2024, ziad alsewary and contributors
# For license information, please see license.txt


import frappe
from frappe import _
from frappe.utils import flt

import erpnext

salary_slip = frappe.qb.DocType("Salary Slip")
salary_detail = frappe.qb.DocType("Salary Detail")
salary_component = frappe.qb.DocType("Salary Component")
employee = frappe.qb.DocType("Employee")
employee_bank_account = frappe.qb.DocType("P Employee Bank Account")


def execute(filters=None):
	if not filters:
		filters = {}

	currency = None
	if filters.get("currency"):
		currency = filters.get("currency")
	company_currency = erpnext.get_company_currency(filters.get("company"))

	salary_slips = get_salary_slips(filters, company_currency)
	if not salary_slips:
		return [], []

	earning_types, ded_types = get_earning_and_deduction_types(salary_slips)
	columns = get_columns(earning_types, ded_types, filters)

	ss_earning_map = get_salary_slip_details(salary_slips, currency, company_currency, "earnings")
	ss_ded_map = get_salary_slip_details(salary_slips, currency, company_currency, "deductions")

	doj_map = get_employee_doj_map()

	data = []
	for ss in salary_slips:
		row = {
			"salary_slip_id": ss.name,
			"employee": ss.employee,
			"employee_name": ss.employee_name,
			"currency": currency or company_currency,
			"total_loan_repayment": ss.total_loan_repayment,
		}
  
		if filters.get("add_extra_columns"):
			row = add_extra_columns_into_row(ss, row)
			update_column_width(ss, columns)

		if filters.get("slip_dates"):
			row = add_dates_into_row(ss, row, filters.get("slip_dates"))

		if filters.get("p_bank"):
			row = add_bank_account_into_row(ss, row, filters.get("p_bank"))
			
		

		for e in earning_types:
			row.update({frappe.scrub(e): ss_earning_map.get(ss.name, {}).get(e)})

		for d in ded_types:
			row.update({frappe.scrub(d): ss_ded_map.get(ss.name, {}).get(d)})

		if currency == company_currency:
			row.update(
				{
					"gross_pay": flt(ss.gross_pay) * flt(ss.exchange_rate),
					"total_deduction": flt(ss.total_deduction) * flt(ss.exchange_rate),
					"net_pay": flt(ss.net_pay) * flt(ss.exchange_rate),
				}
			)

		else:
			row.update(
				{"gross_pay": ss.gross_pay, "total_deduction": ss.total_deduction, "net_pay": ss.net_pay}
			)

		data.append(row)
	return columns, data


def get_earning_and_deduction_types(salary_slips):
	salary_component_and_type = {_("Earning"): [], _("Deduction"): []}

	for salary_compoent in get_salary_components(salary_slips):
		component_type = get_salary_component_type(salary_compoent)
		salary_component_and_type[_(component_type)].append(salary_compoent)

	return sorted(salary_component_and_type[_("Earning")]), sorted(
		salary_component_and_type[_("Deduction")]
	)

def add_dates_into_row(slip_data, row, slip_dates):
	if slip_dates == "Disbursement":
		row["custom_start_date_disbursement"] = slip_data.custom_start_date_disbursement
		row["custom_end_date_disbursement"] = slip_data.custom_end_date_disbursement
		
	elif slip_dates == "Attendance":
		row["start_date"] = slip_data.start_date
		row["end_date"] = slip_data.end_date
		
	else:
		row["custom_start_date_disbursement"] = slip_data.custom_start_date_disbursement
		row["custom_end_date_disbursement"] = slip_data.custom_end_date_disbursement
		row["start_date"] = slip_data.start_date
		row["end_date"] = slip_data.end_date

	return row

def add_bank_account_into_row(slip_data, row, bank_name ):
	row["bank"]= ""
	row["employee_bank_account"] = ""
	emp_bank = get_employee_bank_account(slip_data.employee, bank_name)
	row["bank"] = bank_name
 
	if emp_bank.found:
		row["employee_bank_account"] = emp_bank.account_no
		
	return row

def get_employee_bank_account(employee, bank_name):
	# gle = frappe.get_doc("GL Entry", {"voucher_no": si.name, "account": "Sales - _TC"})
    emp_bank_account = frappe._dict({
			"found": False,
			"name": "",
			"account_no": ""
		})
    b_accounts = frappe.db.get_all(
			"P Employee Bank Account",
			fields=["name", "account_no"],
			filters=[
       			["employee", "=", employee], 
          		["bank", "=", bank_name]
            ],
			limit=1
		)
    if len(b_accounts):
        emp_bank_account.found = True
        emp_bank_account.name = b_accounts[0].name
        emp_bank_account.account_no = b_accounts[0].account_no
	
    return emp_bank_account
    

def add_extra_columns_into_row(slip_data, row):
	row["branch"] = slip_data.branch
	row["department"] = slip_data.department
	row["section"] = slip_data.section
	row["designation"] = slip_data.designation
	row["leave_without_pay"] = slip_data.leave_without_pay
	row["absent_days"] = slip_data.absent_days
		
	return row
   
def update_column_width(ss, columns):
	if ss.branch is not None:
		columns[3].update({"width": 120})
	if ss.department is not None:
		columns[4].update({"width": 120})
	if ss.designation is not None:
		columns[5].update({"width": 120})
	# if ss.leave_without_pay is not None:
	# 	columns[9].update({"width": 120})

def get_columns(earning_types, ded_types, filters):
	columns = [
		{
			"label": _("Slip ID"),
			"fieldname": "salary_slip_id",
			"fieldtype": "Link",
			"options": "Salary Slip",
			"width": 150,
		},
		{
			"label": _("Employee"),
			"fieldname": "employee",
			"fieldtype": "Link",
			"options": "Employee",
			"width": 120,
		},
		{
			"label": _("Employee Name"),
			"fieldname": "employee_name",
			"fieldtype": "Data",
			"width": 140,
		}
	]
	if filters.get("add_extra_columns"):
		add_extra_columns(columns)
  
	if filters.get("slip_dates"):
		add_dates_colunms(columns, filters)
	
	if filters.get("p_bank"):
		add_bank_colunms(columns)

	for earning in earning_types:
		columns.append(
			{
				"label": earning,
				"fieldname": frappe.scrub(earning),
				"fieldtype": "Float",
				"precision": 2,
				"width": 120,
			}
		)

	columns.append(
		{
			"label": _("Gross Pay USD"),
			"fieldname": "gross_pay",
			"fieldtype": "Float",
			
   			"precision": 2,
			"width": 120,
		}
	)

	for deduction in ded_types:
		columns.append(
			{
				"label": deduction,
				"fieldname": frappe.scrub(deduction),
				"fieldtype": "Float",
				
    			"precision": 2,
				"width": 120,
			}
		)

	columns.extend(
		[
			# {
			# 	"label": _("Loan Repayment"),
			# 	"fieldname": "total_loan_repayment",
			# 	"fieldtype": "Float",
				
			# 	"width": 120,
			# },
			{
				"label": _("Total Deduction USD"),
				"fieldname": "total_deduction",
				"fieldtype": "Float",
				
				"width": 120,
			},
			{
				"label": _("Net Pay USD"),
				"fieldname": "net_pay",
				"fieldtype": "Float",
				
				"width": 120,
			},
			{
				"label": _("Currency"),
				"fieldtype": "Data",
				"fieldname": "currency",
				"hidden": 1,
			},
		]
	)
	return columns

def add_dates_colunms(columns, filters):
	if filters.get("slip_dates") == "Disbursement":
		columns += [
			{
				"label": _("Start Date (Dis)"),
				"fieldname": "custom_start_date_disbursement",
				"fieldtype": "Data",
				"width": 100,
			},
			{
				"label": _("End Date (Dis)"),
				"fieldname": "custom_end_date_disbursement",
				"fieldtype": "Data",
				"width": 100,
			},
		]
	elif filters.get("slip_dates") == "Attendance":
		columns += [
			{
				"label": _("Start Date (Att)"),
				"fieldname": "start_date",
				"fieldtype": "Data",
				"width": 100,
			},
			{
				"label": _("End Date (Att)"),
				"fieldname": "end_date",
				"fieldtype": "Data",
				"width": 100,
			},
		]
	else:
		columns += [
			{
				"label": _("Start Date (Dis)"),
				"fieldname": "custom_start_date_disbursement",
				"fieldtype": "Data",
				"width": 100,
			},
			{
				"label": _("End Date (Dis)"),
				"fieldname": "custom_end_date_disbursement",
				"fieldtype": "Data",
				"width": 100,
			},
			{
				"label": _("Start Date (Att)"),
				"fieldname": "start_date",
				"fieldtype": "Data",
				"width": 100,
			},
			{
				"label": _("End Date (Att)"),
				"fieldname": "end_date",
				"fieldtype": "Data",
				"width": 100,
			},
		]
   
def add_bank_colunms(columns):
	columns += [
		# {
		# 	"label": _("Employee Bank Account"),
		# 	"fieldname": "employee_bank_account",
		# 	"fieldtype": "Link",
   		# 	"options": "P Employee Bank Account",
		# 	"width": 100,
		# },		
  		{
			"label": _("Bank"),
			"fieldname": "bank",
			"fieldtype": "Data",
			"width": 100,
		},
  		{
			"label": _("Account Number"),
			"fieldname": "employee_bank_account",
			"fieldtype": "Data",
			"width": 100,
		},
	]
    
def add_extra_columns(columns):
	columns += [
		{
			"label": _("Branch"),
			"fieldname": "branch",
			"fieldtype": "Link",
			"options": "Branch",
			"width": -1,
		},
		{
			"label": _("Department"),
			"fieldname": "department",
			"fieldtype": "Link",
			"options": "Department",
			"width": -1,
		},
		{
			"label": _("Designation"),
			"fieldname": "designation",
			"fieldtype": "Link",
			"options": "Designation",
			"width": 120,
		},
		{
			"label": _("LWP"),
			"fieldname": "leave_without_pay",
			"fieldtype": "Float",
			"width": 50,
			"precision":2
		},
		{
			"label": _("Absent"),
			"fieldname": "absent_days",
			"fieldtype": "Float",
			"width": 50,
			"precision":2
		},
	]
    
def get_salary_components(salary_slips):
	return (
		frappe.qb.from_(salary_detail)
		.where(
      		(salary_detail.amount != 0) 
        	& (salary_detail.parent.isin([d.name for d in salary_slips]))
         )
		.select(salary_detail.salary_component)
		.distinct()
	).run(pluck=True)

def get_salary_component_type(salary_component):
	return frappe.db.get_value("Salary Component", salary_component, "type", cache=True)

def get_salary_slips(filters, company_currency):
	doc_status = {"Draft": 0, "Submitted": 1, "Cancelled": 2}
	
	query = (
		frappe.qb.from_(salary_slip)
		.select(
      		salary_slip.star
         )
	)
	# query = (
	# 	frappe.qb.from_(salary_slip)
	# 	.left_join(employee_bank_account)
	# 	.on(salary_slip.employee == employee_bank_account.employee)
	# 	.select(
    #   		salary_slip.star
    #      )
	# )
	# if filters.get("p_bank"):
	# 	query = query.select(
	# 				employee_bank_account.bank,
    #  				employee_bank_account.account_no.as_("employee_bank_account")
    #       		)

	if filters.get("docstatus"):
		query = query.where(salary_slip.docstatus == doc_status[filters.get("docstatus")])

	if filters.get("from_date"):
		query = query.where(salary_slip.custom_start_date_disbursement >= filters.get("from_date"))

	if filters.get("to_date"):
		query = query.where(salary_slip.custom_end_date_disbursement <= filters.get("to_date"))

	if filters.get("company"):
		query = query.where(salary_slip.company == filters.get("company"))

	if filters.get("employment_type"):
		query = query.where(salary_slip.custom_employment_type == filters.get("employment_type"))

	if filters.get("employee"):
		query = query.where(salary_slip.employee == filters.get("employee"))

	if filters.get("currency") and filters.get("currency") != company_currency:
		query = query.where(salary_slip.currency == filters.get("currency"))

	if filters.get("salary_structure"):
		query = query.where(salary_slip.salary_structure == filters.get("salary_structure"))
  
	if filters.get("do_not_show_the_exception"):
		query = query.where(salary_slip.custom_exception != 1)
	
	
  
	# if filters.get("project"):
	# 	query = query.where(filters.get("project").isin(salary_slip.custom_projects))
	
	# frappe.msgprint(str(query))
	salary_slips = query.run(as_dict=1)

	return salary_slips or []

def get_employee_doj_map():
	employee = frappe.qb.DocType("Employee")

	result = (frappe.qb.from_(employee).select(employee.name, employee.date_of_joining)).run()

	return frappe._dict(result)

def get_salary_slip_details(salary_slips, currency, company_currency, component_type):
	salary_slips = [ss.name for ss in salary_slips]

	result = (
		frappe.qb.from_(salary_slip)
		.join(salary_detail)
		.on(salary_slip.name == salary_detail.parent)
		.where((salary_detail.parent.isin(salary_slips)) & (salary_detail.parentfield == component_type))
		.select(
			salary_detail.parent,
			salary_detail.salary_component,
			salary_detail.amount,
			salary_slip.exchange_rate,
		)
	).run(as_dict=1)

	ss_map = {}

	for d in result:
		ss_map.setdefault(d.parent, frappe._dict()).setdefault(d.salary_component, 0.0)
		if currency == company_currency:
			ss_map[d.parent][d.salary_component] += flt(d.amount) * flt(
				d.exchange_rate if d.exchange_rate else 1
			)
		else:
			ss_map[d.parent][d.salary_component] += flt(d.amount)

	return ss_map

