# # apps/tfd_projectmanagement/tfd_projectmanagement/overrides/salary_slip_override.py
# import frappe
# from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip
# from frappe.utils import get_datetime
# from datetime import datetime, time, timedelta

# # إعدادات
# LATE_GRACE_MINUTES   = 10.0
# WORKING_HOURS_PER_DAY = 8.0
# # إن كنت تريد الاعتماد على "راتب أساسي" (عربي) فقط، استعمل المجموعة التالية:
# BASE_COMPONENTS = {"راتب أساسي"}
# FALLBACK_SHIFT_START = time(8, 0)
# DEDUCTION_COMPONENT_NAME = "خصم التاخيرات"   # أنشئ Salary Component بهذا الاسم/نوع Deduction

# class CustomSalarySlip(SalarySlip):
#     def validate(self):
#         # حافظ على تحقق HRMS الأصلي
#         super().validate()
#         # طبق خصم التأخير
#         self.apply_late_deduction()

#     # ========== أدوات مساعدة ==========
#     @staticmethod
#     def _minutes_diff(later_dt: datetime, earlier_dt: datetime) -> float:
#         try:
#             return (later_dt - earlier_dt).total_seconds() / 60.0
#         except Exception:
#             return 0.0

#     @staticmethod
#     def _coerce_shift_start(val) -> time:
#         if isinstance(val, time):
#             return val
#         if isinstance(val, timedelta):
#             base = datetime.min + val
#             return time(base.hour, base.minute, base.second)
#         return FALLBACK_SHIFT_START

#     def _get_shift_meta(self, employee, the_date):
#         """يرجع (start_time: time, late_grace: float) من الشفت لليوم."""
#         rec = frappe.db.sql(
#             """
#             SELECT st.start_time, st.late_entry_grace_period
#             FROM `tabShift Assignment` sa
#             JOIN `tabShift Type` st ON st.name = sa.shift_type
#             WHERE sa.employee=%s
#               AND sa.start_date <= %s
#               AND (sa.end_date IS NULL OR sa.end_date >= %s)
#             ORDER BY sa.start_date DESC
#             LIMIT 1
#             """,
#             (employee, the_date, the_date),
#             as_dict=True,
#         )
#         start_time = FALLBACK_SHIFT_START
#         late_grace = LATE_GRACE_MINUTES
#         if rec:
#             st = rec[0].get("start_time")
#             start_time = self._coerce_shift_start(st)
#             lg = rec[0].get("late_entry_grace_period")
#             late_grace = float(lg) if lg is not None else LATE_GRACE_MINUTES
#         return start_time, late_grace

#     def _total_late_from_attendance(self, employee, start_date, end_date) -> float:
#         total = 0.0
#         atts = frappe.get_all(
#             "Attendance",
#             filters={
#                 "employee": employee,
#                 "attendance_date": ["between", [start_date, end_date]],
#                 "docstatus": 1,
#             },
#             fields=["attendance_date", "status", "in_time"],
#             order_by="attendance_date asc",
#         )
#         for a in atts:
#             if a.get("status") not in ("Present", "Work From Home", "On Duty"):
#                 continue
#             in_time_val = a.get("in_time")
#             if not in_time_val:
#                 continue
#             in_dt = get_datetime(in_time_val)
#             st_time, grace = self._get_shift_meta(employee, a["attendance_date"])
#             shift_start_dt = datetime.combine(a["attendance_date"], st_time)
#             late = self._minutes_diff(in_dt, shift_start_dt) - grace
#             if late > 0:
#                 total += late
#         return total

#     def _total_late_from_checkin(self, employee, start_date, end_date) -> float:
#         # في حال لا يوجد in_time في Attendance نعتمد على أول Checkin يومي
#         checkins = frappe.get_all(
#             "Employee Checkin",
#             filters={
#                 "employee": employee,
#                 "time": ["between", [f"{start_date} 00:00:00", f"{end_date} 23:59:59"]],
#                 "docstatus": 1,
#             },
#             fields=["time"],
#             order_by="time asc",
#         )
#         first_in_by_day = {}
#         for c in checkins:
#             dt = get_datetime(c.get("time"))
#             d = dt.date()
#             # نحتفظ بأول دخول
#             if d not in first_in_by_day:
#                 first_in_by_day[d] = dt

#         total = 0.0
#         for d, in_dt in first_in_by_day.items():
#             st_time, grace = self._get_shift_meta(employee, d)
#             shift_start_dt = datetime.combine(d, st_time)
#             late = self._minutes_diff(in_dt, shift_start_dt) - grace
#             if late > 0:
#                 total += late
#         return total

#     @staticmethod
#     def _sum_base_components(earnings_childtable) -> float:
#         total = 0.0
#         for row in (earnings_childtable or []):
#             comp = (row.salary_component or "").strip()
#             if comp in BASE_COMPONENTS:
#                 total += float(row.amount or 0)
#         return total

#     def _upsert_deduction_row(self, amount: float, component_name: str = DEDUCTION_COMPONENT_NAME):
#         for row in (self.deductions or []):
#             if (row.salary_component or "").strip() == component_name:
#                 row.amount = float(amount or 0)
#                 return
#         self.append("deductions", {"salary_component": component_name, "amount": float(amount or 0)})

#     # ========== المنطق الرئيسي ==========
#     def apply_late_deduction(self):
#         """يُحسب خصم التأخيرات ويضيفه كسطر Deduction."""
#         # 1) إجمالي دقائق التأخير
#         total_late = self._total_late_from_attendance(self.employee, self.start_date, self.end_date)
#         if total_late <= 0:
#             total_late = self._total_late_from_checkin(self.employee, self.start_date, self.end_date)

#         # خزّنها في حقول مخصصة (إن وجدت)
#         if hasattr(self, "custom_total_late_minutes"):
#             self.custom_total_late_minutes = float(total_late or 0)

#         # 2) قيمة الأساس "راتب أساسي" من الـ Earnings
#         base_amount = self._sum_base_components(self.earnings)

#         # أيام الدفع والدقائق ضمن الفترة
#         payment_days = float(self.payment_days or self.total_working_days or 26.0)
#         minutes_in_period = WORKING_HOURS_PER_DAY * 60.0 * payment_days

#         late_deduction = 0.0
#         if base_amount > 0 and minutes_in_period > 0 and total_late > 0:
#             late_deduction = base_amount * (total_late / minutes_in_period)

#         if hasattr(self, "custom_late_deduction_amount"):
#             self.custom_late_deduction_amount = float(late_deduction or 0)

#         # 3) أضف/حدّث بند الخصم
#         self._upsert_deduction_row(late_deduction, DEDUCTION_COMPONENT_NAME)

# apps/tfd_projectmanagement/tfd_projectmanagement/overrides/salary_slip_override.py

# apps/tfd_projectmanagement/tfd_projectmanagement/overrides/salary_slip_override.py

import frappe
from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip
from frappe.utils import get_datetime
from datetime import datetime, date, time, timedelta

# ================= إعدادات =================
LATE_GRACE_MINUTES    = 15.0               # سماح افتراضي إن لم نجد قيمة في الشفت
WORKING_HOURS_PER_DAY = 8.0                # ساعات الدوام المعتمدة يوميًا
BASE_COMPONENTS       = {"راتب أساسي"}     # المكوّن/ات التي يُحتسب الخصم منها
FALLBACK_SHIFT_START  = time(8, 0)         # وقت بداية الشفت الافتراضي إن لم نجد شفت
DEDUCTION_COMPONENT_NAME = "خصم التاخيرات" # Salary Component (Deduction) لخصم التأخير
# ===========================================


class CustomSalarySlip(SalarySlip):
    def validate(self):
        # تحققات HRMS الأصلية
        super().validate()
        # تطبيق خصم التأخير + تعبئة الحقول/الجدول الفرعي
        self.apply_late_deduction()

    # ========== أدوات مساعدة ==========
    @staticmethod
    def _minutes_diff(later_dt: datetime, earlier_dt: datetime) -> float:
        """فرق الدقائق بين تاريخين."""
        try:
            return (later_dt - earlier_dt).total_seconds() / 60.0
        except Exception:
            return 0.0

    @staticmethod
    def _coerce_shift_start(val) -> time:
        """تحويل start_time (قد يأتي timedelta في بعض الإصدارات) إلى time."""
        if isinstance(val, time):
            return val
        if isinstance(val, timedelta):
            base = datetime.min + val
            return time(base.hour, base.minute, base.second)
        return FALLBACK_SHIFT_START

    def _get_shift_meta(self, employee, the_date: date):
        """
        إرجاع (start_time: time, late_grace: float) من الشفت الفعّال في ذلك اليوم.
        - نقرأ Enable Late Entry Marking و Late Entry Grace Period من Shift Type.
        - إذا Enable Late Entry Marking غير مفعَّل => السماح = 0.
        """
        rec = frappe.db.sql(
            """
            SELECT
                st.start_time,
                st.enable_late_entry_marking,
                st.late_entry_grace_period
            FROM `tabShift Assignment` sa
            JOIN `tabShift Type` st ON st.name = sa.shift_type
            WHERE sa.employee = %s
              AND sa.start_date <= %s
              AND (sa.end_date IS NULL OR sa.end_date >= %s)
            ORDER BY sa.start_date DESC
            LIMIT 1
            """,
            (employee, the_date, the_date),
            as_dict=True,
        )

        start_time = FALLBACK_SHIFT_START
        late_grace = LATE_GRACE_MINUTES

        if rec:
            row = rec[0]
            start_time = self._coerce_shift_start(row.get("start_time"))
            enable_late = bool(row.get("enable_late_entry_marking"))
            grace_val = row.get("late_entry_grace_period")
            if not enable_late:
                late_grace = 0.0
            else:
                late_grace = float(grace_val) if grace_val is not None else LATE_GRACE_MINUTES

        return start_time, late_grace

    # -------- تجميع دقائق التأخير لكل يوم --------
    def _late_minutes_by_day(self, employee, start_date, end_date):
        """
        يرجّع dict: {date: late_minutes_after_grace}
        الأسبقية:
          1) Attendance.in_time لو موجود
          2) وإلا أول Employee Checkin في اليوم
        """
        late_by_day = {}

        # 1) من Attendance
        atts = frappe.get_all(
            "Attendance",
            filters={
                "employee": employee,
                "attendance_date": ["between", [start_date, end_date]],
                "docstatus": 1,
            },
            fields=["attendance_date", "status", "in_time"],
            order_by="attendance_date asc",
        )
        for a in (atts or []):
            d = a.get("attendance_date")
            if a.get("status") not in ("Present", "Work From Home", "On Duty"):
                continue
            in_time_val = a.get("in_time")
            if not in_time_val:
                continue
            in_dt = get_datetime(in_time_val)
            st_time, grace = self._get_shift_meta(employee, d)
            shift_start_dt = datetime.combine(d, st_time)
            late_after_grace = self._minutes_diff(in_dt, shift_start_dt) - grace
            if late_after_grace > 0:
                late_by_day[d] = late_after_grace

        # 2) من Employee Checkin (لأيام لا توجد لها in_time في Attendance)
        checkins = frappe.get_all(
            "Employee Checkin",
            filters={
                "employee": employee,
                "time": ["between", [f"{start_date} 00:00:00", f"{end_date} 23:59:59"]],
                "docstatus": 1,
            },
            fields=["time"],
            order_by="time asc",
        )
        first_in_by_day = {}
        for c in (checkins or []):
            dt = get_datetime(c.get("time"))
            d = dt.date()
            if d not in first_in_by_day:
                first_in_by_day[d] = dt

        for d, in_dt in first_in_by_day.items():
            # لا نستبدل يوم لديه Attendance-in_time
            if d in late_by_day:
                continue
            st_time, grace = self._get_shift_meta(employee, d)
            shift_start_dt = datetime.combine(d, st_time)
            late_after_grace = self._minutes_diff(in_dt, shift_start_dt) - grace
            if late_after_grace > 0:
                late_by_day[d] = late_after_grace

        return late_by_day

    @staticmethod
    def _sum_base_components(earnings_childtable) -> float:
        """مجموع مبالغ المكوّنات الأساسية المحددة في BASE_COMPONENTS من جدول Earnings."""
        total = 0.0
        for row in (earnings_childtable or []):
            comp = (row.salary_component or "").strip()
            if comp in BASE_COMPONENTS:
                total += float(row.amount or 0)
        return total

    def _upsert_deduction_row(self, amount: float, component_name: str = DEDUCTION_COMPONENT_NAME):
        """تحديث/إضافة بند الخصم في جدول deductions."""
        for row in (self.deductions or []):
            if (row.salary_component or "").strip() == component_name:
                row.amount = float(amount or 0)
                return
        self.append("deductions", {"salary_component": component_name, "amount": float(amount or 0)})

    # ========== المنطق الرئيسي ==========
    def apply_late_deduction(self):
        """
        يحسب التأخير يوميًا، يملأ الجدول الفرعي custom_late_days (date, minutes)،
        ويعبّي:
          - custom_number_of_late_days
          - custom_total_late_minutes
          - custom_total_late_hours
          - custom_late_deduction_amount
        ويضيف/يحدّث بند الخصم "خصم التاخيرات".
        """
        # خريطة دقائق التأخير لكل يوم
        by_day = self._late_minutes_by_day(self.employee, self.start_date, self.end_date)

        # تعبئة الجدول الفرعي custom_late_days
        # امسح القديم ثم أضف الجديد مرتّبًا تصاعديًا
        try:
            self.set("custom_late_days", [])
        except Exception:
            # لو الجدول غير موجود لن ينهار الكود
            pass

        days_count = 0
        total_minutes = 0.0

        for d in sorted(by_day.keys()):
            minutes = float(by_day[d] or 0)
            if minutes <= 0:
                continue
            days_count += 1
            total_minutes += minutes
            # أضف صفًا في الجدول الفرعي
            try:
                self.append("custom_late_days", {"date": d, "minutes": minutes})
            except Exception:
                # لو أسماء الحقول مختلفة، لن يتوقف التنفيذ
                pass

        # حقول الملخص
        if hasattr(self, "custom_number_of_late_days"):
            self.custom_number_of_late_days = float(days_count)

        if hasattr(self, "custom_total_late_minutes"):
            self.custom_total_late_minutes = float(total_minutes)

        if hasattr(self, "custom_total_late_hours"):
            self.custom_total_late_hours = round(float(total_minutes) / 60.0, 3)

        # مبلغ الخصم
        base_amount = self._sum_base_components(self.earnings)
        payment_days = float(self.payment_days or self.total_working_days or 26.0)
        minutes_in_period = WORKING_HOURS_PER_DAY * 60.0 * payment_days

        late_deduction = 0.0
        if base_amount > 0 and minutes_in_period > 0 and total_minutes > 0:
            late_deduction = base_amount * (total_minutes / minutes_in_period)

        if hasattr(self, "custom_late_deduction_amount"):
            self.custom_late_deduction_amount = float(late_deduction or 0)

        # سطر الخصم
        self._upsert_deduction_row(late_deduction, DEDUCTION_COMPONENT_NAME)
