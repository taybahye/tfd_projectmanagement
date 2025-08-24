# Copyright (c) 2025, Amd Oudah Prosite  and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from hrms.hr.doctype.leave_application.leave_application import get_leave_balance_on


class ahmed(Document):
	pass





@frappe.whitelist()
def get_result_checkin():
    try:
        frappe.log("بدء تنفيذ استعلام الحضور لجميع موظفي شركة طيبة...")

        employees = frappe.get_all("Employee", filters={"company": "Taybah Foundation For Development"}, fields=["name", "employee_name"])

        all_created_leaves = []
        delay_summary = []

        for emp in employees:
            employee = emp.name
            employee_name = emp.employee_name

            frappe.log(f"معالجة الموظف: {employee_name}")

            result = frappe.db.sql("""
                SELECT DISTINCT
                    att.attendance_date,
                    att.in_time,
                    att.out_time,
                    ci.shift_start,
                    ci.shift_end,
                    st.late_entry_grace_period,
                    st.early_exit_grace_period,
                    CASE
                        WHEN att.out_time < SUBTIME(ci.shift_end, SEC_TO_TIME(st.early_exit_grace_period * 60)) THEN
                            TIMESTAMPDIFF(
                                SECOND,
                                att.out_time,
                                SUBTIME(ci.shift_end, SEC_TO_TIME(st.early_exit_grace_period * 60))
                            )
                        ELSE 0
                    END AS early_exit_delay_seconds,
                    CASE
                        WHEN att.in_time > ADDTIME(ci.shift_start, SEC_TO_TIME(st.late_entry_grace_period * 60)) THEN
                            TIMESTAMPDIFF(
                                SECOND,
                                ADDTIME(ci.shift_start, SEC_TO_TIME(st.late_entry_grace_period * 60)),
                                att.in_time
                            )
                        ELSE 0
                    END AS late_entry_delay_seconds
                FROM
                    tabAttendance att
                LEFT JOIN
                    `tabEmployee Checkin` ci ON att.name = ci.attendance
                LEFT JOIN
                    `tabShift Type` st ON att.shift = st.name
                WHERE
                    att.in_time IS NOT NULL
                    AND att.out_time IS NOT NULL
                    AND ci.shift_start IS NOT NULL
                    AND ci.shift_end IS NOT NULL
                    AND att.docstatus < 2
                    AND att.employee = %s
                ORDER BY
                    att.attendance_date;
            """, employee, as_dict=True)

            if not result:
                frappe.log(f"لا توجد سجلات حضور للموظف: {employee_name}")
                continue

            total_delay_seconds = sum([row['early_exit_delay_seconds'] + row['late_entry_delay_seconds'] for row in result])
            total_minutes = total_delay_seconds // 60
            days_to_create = total_minutes / 480  # 480 دقيقة = يوم عمل
            days_to_create = float(days_to_create)

            existing_auto_leaves = frappe.db.count("Leave Application", {
                "employee": employee,
                "leave_type": "الاجازة السنوية",
                "description": "تم إنشاء الإجازة تلقائيًا بسبب التأخير",
                "docstatus": 1
            })

            days_to_create -= existing_auto_leaves

            today = frappe.utils.today()
            balance = get_leave_balance_on(employee, "الاجازة السنوية", today)
            frappe.log(f"رصيد الإجازة السنوية للموظف {employee_name} ({employee}): {balance} يوم")
            frappe.log(f"عدد الأيام المطلوب إنشاؤها: {days_to_create}")

            # ✅ تحقق من أن التأخيرات تساوي يومًا أو أكثر فقط
            if days_to_create < 1:
                frappe.log(f"📌 عدد أيام التأخير أقل من يوم. لا حاجة لإنشاء غياب أو إجازة للموظف {employee_name}.")
                delay_summary.append(f"🕒 {employee_name} ({employee}): {total_minutes} دقيقة تأخير ≈ {days_to_create:.2f} يوم")
                continue

            available_dates = [row['attendance_date'] for row in result]
            created_days = 0

            for date in available_dates:
                if created_days >= days_to_create:
                    break

                leave_date = date

                # إلغاء الحضور المعتمد
                existing_attendance_names = frappe.get_all("Attendance", {
                    "attendance_date": leave_date,
                    "employee": employee,
                    "docstatus": 1
                }, pluck="name")

                if existing_attendance_names:
                    for att_name in existing_attendance_names:
                        att_doc = frappe.get_doc("Attendance", att_name)
                        att_doc.cancel()
                        frappe.db.commit()
                        frappe.log(f"🔄 تم إلغاء سجل الحضور {att_name} للموظف {employee_name} في التاريخ: {leave_date}")

                # إنشاء إجازة أو غياب
                if balance > 0:
                    leave_app = frappe.new_doc("Leave Application")
                    leave_app.employee = employee
                    leave_app.leave_type = "الاجازة السنوية"
                    leave_app.from_date = leave_date
                    leave_app.to_date = leave_date
                    leave_app.description = "تم إنشاء الإجازة تلقائيًا بسبب التأخير"
                    leave_app.status = "Approved"
                    leave_app.save()
                    leave_app.submit()
                    all_created_leaves.append(leave_app.name)
                    balance -= 1
                    created_days += 1
                    total_minutes -= 480
                    frappe.log(f"📄 تم إنشاء إجازة تلقائية للموظف {employee_name} في التاريخ: {leave_date}")
                else:
                    att = frappe.new_doc("Attendance")
                    att.employee = employee
                    att.attendance_date = leave_date
                    att.status = "Absent"
                    att.company = "Taybah Foundation For Development"
                    att.insert()
                    frappe.db.commit()
                    created_days += 1
                    total_minutes -= 480
                    frappe.log(f"📄 تم إنشاء سجل غياب للموظف {employee_name} في التاريخ: {leave_date}")

            delay_summary.append(f"🕒 {employee_name} ({employee}): {total_minutes} دقيقة تأخير ≈ {days_to_create:.2f} يوم")

        return {
            "created_leaves": all_created_leaves,
            "delay_summary": delay_summary,
            "message": f"✅ تم إنشاء {len(all_created_leaves)} إجازة تلقائية وسجلات غياب بناءً على التأخيرات."
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_result_checkin Error")
        frappe.msgprint(f"حدث خطأ أثناء التنفيذ: {str(e)}")
        return {
            "error": True,
            "message": f"حدث خطأ أثناء التنفيذ: {str(e)}"
        }







