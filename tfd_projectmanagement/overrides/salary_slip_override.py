
# # -*- coding: utf-8 -*-# apps/tfd_projectmanagement/tfd_projectmanagement/overrides/salary_slip_override.py
# # apps/tfd_projectmanagement/tfd_projectmanagement/overrides/salary_slip_override.py
# #قبل تصحح  الضر و التاكد من وجود خصم التاخت
# import frappe
# from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip
# from frappe.utils import get_datetime
# from datetime import datetime, date, time, timedelta

# # ================= إعدادات عامة =================
# LATE_GRACE_MINUTES     = 15.0                 # سماح افتراضي إن لم نجد قيمة في الشفت
# WORKING_HOURS_PER_DAY  = 8.0                  # ساعات الدوام المعتمدة يوميًا
# BASE_COMPONENTS        = {"راتب أساسي"}       # المكوّن/ات التي يُحتسب الخصم منها
# FALLBACK_SHIFT_START   = time(8, 0)           # وقت بداية الشفت الافتراضي
# DEDUCTION_COMPONENT_NAME = "خصم التاخيرات"    # Salary Component (Deduction) لخصم التأخير
# DEDUCTION_ABBR         = "late_deduction"     # اختصار بند خصم التأخيرات

# # البنود التي تدخل في "إجمالي الخصومات" (حسب اختصاراتها)
# INCLUDE_IN_TOTAL_ABBRS = {"amd_tax_1", "loans", "ABS_USD", "late_deduction"}

# # اسم/اختصار سطر "إجمالي الخصومات" الموجود مسبقًا
# TOTAL_DED_ROW_NAMES    = {"اجمالي الخصومات", "إجمالي الخصومات"}
# TOTAL_DED_ROW_ABBRS    = {"to_reb_amd", "amd_total"}

# # اسم/اختصار سطر "صافي الراتب" الموجود مسبقًا
# NET_PAY_ROW_NAMES      = {"صافي الراتب", "صـافي الــراتب"}
# NET_PAY_ROW_ABBRS      = {"Amd_net_pay", "amd_net_pay"}

# # اسم/اختصار سطر "اجمالي الكلي" في جدول الـ Earnings (المطلوب للصافي)
# GROSS_ROW_NAMES        = {"اجمالي الكلي", "إجمالي الكلي"}
# GROSS_ROW_ABBRS        = {"amd_total", "amd_total"}
# # =================================================


# class CustomSalarySlip(SalarySlip):
#     # ترتيب التنفيذ:
#     #  - نترك HRMS يتحقق أولًا
#     #  - نحسب التأخيرات ونضيف بند الخصم
#     #  - قبل الحفظ نعيد تجميع إجمالي الخصومات والصافي ونُثبِّت السطرين
#     def validate(self):
#         super().validate()
#         self.apply_late_deduction()

#     def before_save(self):
#         self._recalc_totals_into_existing_rows()
#         self._freeze_total_and_net_rows()

#     # ================= أدوات مساعدة للوقت/الشفت =================
#     @staticmethod
#     def _minutes_diff(later_dt: datetime, earlier_dt: datetime) -> float:
#         try:
#             return (later_dt - earlier_dt).total_seconds() / 60.0
#         except Exception:
#             return 0.0

#     @staticmethod
#     def _coerce_shift_start(val) -> time:
#         # أحيانًا start_time يُخزَّن timedelta
#         if isinstance(val, time):
#             return val
#         if isinstance(val, timedelta):
#             base = datetime.min + val
#             return time(base.hour, base.minute, base.second)
#         return FALLBACK_SHIFT_START

#     def _get_shift_meta(self, employee, the_date: date):
#         """
#         إرجاع (start_time: time, late_grace: float) من الشفت الفعّال في ذلك اليوم.
#         نقرأ Enable Late Entry Marking و Late Entry Grace Period من Shift Type.
#         """
#         rec = frappe.db.sql(
#             """
#             SELECT st.start_time, st.enable_late_entry_marking, st.late_entry_grace_period
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
#             row = rec[0]
#             start_time = self._coerce_shift_start(row.get("start_time"))
#             enable_late = bool(row.get("enable_late_entry_marking"))
#             grace_val = row.get("late_entry_grace_period")
#             late_grace = 0.0 if not enable_late else (float(grace_val) if grace_val is not None else LATE_GRACE_MINUTES)

#         return start_time, late_grace

#     # ---------------- تجميع دقائق التأخير لكل يوم ----------------
#     def _late_minutes_by_day(self, employee, start_date, end_date):
#         """
#         يرجّع dict: {date: late_minutes_after_grace}
#         الأسبقية:
#           1) Attendance.in_time لو موجود
#           2) وإلا أول Employee Checkin في اليوم
#         """
#         late_by_day = {}

#         # 1) من Attendance
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
#         for a in (atts or []):
#             d = a.get("attendance_date")
#             if a.get("status") not in ("Present", "Work From Home", "On Duty"):
#                 continue
#             in_time_val = a.get("in_time")
#             if not in_time_val:
#                 continue
#             in_dt = get_datetime(in_time_val)
#             st_time, grace = self._get_shift_meta(employee, d)
#             shift_start_dt = datetime.combine(d, st_time)
#             late_after_grace = self._minutes_diff(in_dt, shift_start_dt) - grace
#             if late_after_grace > 0:
#                 late_by_day[d] = late_after_grace

#         # 2) من Employee Checkin (لأيام لا توجد لها in_time)
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
#         for c in (checkins or []):
#             dt = get_datetime(c.get("time"))
#             d = dt.date()
#             if d not in first_in_by_day:
#                 first_in_by_day[d] = dt

#         for d, in_dt in first_in_by_day.items():
#             if d in late_by_day:  # عندنا Attendance هذا اليوم
#                 continue
#             st_time, grace = self._get_shift_meta(employee, d)
#             shift_start_dt = datetime.combine(d, st_time)
#             late_after_grace = self._minutes_diff(in_dt, shift_start_dt) - grace
#             if late_after_grace > 0:
#                 late_by_day[d] = late_after_grace

#         return late_by_day

#     @staticmethod
#     def _sum_base_components(earnings_childtable) -> float:
#         total = 0.0
#         for row in (earnings_childtable or []):
#             comp = (row.salary_component or "").strip()
#             if comp in BASE_COMPONENTS:
#                 total += float(row.amount or 0)
#         return total

#     # ================== إنشاء/تحديث بند خصم التأخيرات ==================
#     def _upsert_deduction_row(self, amount: float, component_name: str = DEDUCTION_COMPONENT_NAME):
#         for row in (self.deductions or []):
#             if (row.salary_component or "").strip() == component_name:
#                 row.amount = float(amount or 0)
#                 row.abbr = DEDUCTION_ABBR
#                 row.do_not_include_in_total = 0
#                 return
#         self.append("deductions", {
#             "salary_component": component_name,
#             "amount": float(amount or 0),
#             "abbr": DEDUCTION_ABBR,
#             "do_not_include_in_total": 0,
#         })

#     # ====================== المنطق الرئيسي للتأخيرات ======================
#     def apply_late_deduction(self):
#         # خريطة دقائق التأخير لكل يوم
#         by_day = self._late_minutes_by_day(self.employee, self.start_date, self.end_date)

#         # تعبئة الجدول الفرعي custom_late_days (إن وُجد)
#         try:
#             self.set("custom_late_days", [])
#         except Exception:
#             pass

#         days_count = 0
#         total_minutes = 0.0

#         for d in sorted(by_day.keys()):
#             minutes = float(by_day[d] or 0)
#             if minutes <= 0:
#                 continue
#             days_count += 1
#             total_minutes += minutes
#             try:
#                 self.append("custom_late_days", {"date": d, "minutes": minutes})
#             except Exception:
#                 pass

#         # حقول مساعدة (إن وُجدت في الدوك تايب)
#         if hasattr(self, "custom_number_of_late_days"):
#             self.custom_number_of_late_days = float(days_count)
#         if hasattr(self, "custom_total_late_minutes"):
#             self.custom_total_late_minutes = float(total_minutes)
#         if hasattr(self, "custom_total_late_hours"):
#             self.custom_total_late_hours = round(float(total_minutes) / 60.0, 3)

#         # احسب مبلغ خصم التأخير
#         base_amount = self._sum_base_components(self.earnings)
#         payment_days = float(self.payment_days or self.total_working_days or 26.0)
#         minutes_in_period = WORKING_HOURS_PER_DAY * 60.0 * payment_days

#         late_deduction = 0.0
#         if base_amount > 0 and minutes_in_period > 0 and total_minutes > 0:
#             late_deduction = base_amount * (total_minutes / minutes_in_period)

#         if hasattr(self, "custom_late_deduction_amount"):
#             self.custom_late_deduction_amount = float(late_deduction or 0)

#         # أضِف/حدّث بند الخصم
#         self._upsert_deduction_row(late_deduction, DEDUCTION_COMPONENT_NAME)

#     # =================== التعرف على السطور الخاصة ===================
#     def _is_total_row(self, row) -> bool:
#         name = (row.salary_component or "").strip()
#         abbr = (row.abbr or "").strip()
#         return (name in TOTAL_DED_ROW_NAMES) or (abbr in TOTAL_DED_ROW_ABBRS) or ("إجمالي" in name and "خصومات" in name)

#     def _is_net_row(self, row) -> bool:
#         name = (row.salary_component or "").strip()
#         abbr = (row.abbr or "").strip().lower()
#         return (name in NET_PAY_ROW_NAMES) or (row.abbr in NET_PAY_ROW_ABBRS) or ("صافي" in name) or ("net" in abbr and "pay" in abbr)

#     def _is_gross_row(self, row) -> bool:
#         name = (row.salary_component or "").strip()
#         abbr = (row.abbr or "").strip()
#         return (name in GROSS_ROW_NAMES) or (abbr in GROSS_ROW_ABBRS)

#     def _get_gross_from_earnings(self) -> float:
#         # نبحث عن سطر "اجمالي الكلي" داخل الـ Earnings
#         for r in (self.earnings or []):
#             if self._is_gross_row(r):
#                 return float(r.amount or 0)
#         # إن لم نجده، نرجع gross_pay الافتراضي
#         return float(self.gross_pay or 0)

#     # ===================== إعادة تجميع الإجماليات =====================
#     def _recalc_totals_into_existing_rows(self):
#         # 1) إجمالي الخصومات من البنود المحددة باختصارات INCLUDE_IN_TOTAL_ABBRS
#         total_ded = 0.0
#         for row in (self.deductions or []):
#             if self._is_total_row(row) or self._is_net_row(row):
#                 continue
#             if (row.abbr or "").strip() in INCLUDE_IN_TOTAL_ABBRS:
#                 total_ded += float(row.amount or 0)

#         # 2) حدّث الحقول الرأسية
#         try:
#             prec_ded = self.precision("total_deduction")
#             prec_net = self.precision("net_pay")
#         except Exception:
#             prec_ded = prec_net = 2

#         self.total_deduction = round(total_ded, prec_ded)

#         gross_from_earnings = self._get_gross_from_earnings()  # ← من "اجمالي الكلي"
#         self.net_pay = round(gross_from_earnings - self.total_deduction, prec_net)
#         try:
#             self.rounded_total = round(self.net_pay)
#         except Exception:
#             pass

#         # 3) اكتب النتائج في سطرَي "إجمالي الخصومات" و"صافي الراتب" إن وُجدا
#         row_total = next((r for r in (self.deductions or []) if self._is_total_row(r)), None)
#         if row_total:
#             row_total.amount = float(self.total_deduction)
#             try:
#                 row_total.amount_based_on_formula = 0
#             except Exception:
#                 pass

#         row_net = next((r for r in (self.deductions or []) if self._is_net_row(r)), None)
#         if row_net:
#             row_net.amount = float(self.net_pay)
#             try:
#                 row_net.amount_based_on_formula = 0
#                 row_net.do_not_include_in_total = 1
#             except Exception:
#                 pass

#     def _freeze_total_and_net_rows(self):
#         # تثبيت السطرين حتى لا تُعيد الـ Salary Structure الكتابة فوقهما
#         for row in (self.deductions or []):
#             name = (row.salary_component or "").strip()
#             abbr = (row.abbr or "").strip().lower()

#             is_total = (name in TOTAL_DED_ROW_NAMES) or (abbr in {a.lower() for a in TOTAL_DED_ROW_ABBRS}) or ("إجمالي" in name and "خصومات" in name)
#             is_net = (name in NET_PAY_ROW_NAMES) or (abbr in {a.lower() for a in NET_PAY_ROW_ABBRS}) or ("صافي" in name) or ("net" in abbr and "pay" in abbr)

#             if is_total or is_net:
#                 try:
#                     row.amount_based_on_formula = 0
#                 except Exception:
#                     pass
#                 try:
#                     row.do_not_include_in_total = 1 if is_net else 0
#                 except Exception:
#                     pass

import frappe
from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip
from frappe.utils import get_datetime
from datetime import datetime, date, time, timedelta

# ================= إعدادات عامة =================
LATE_GRACE_MINUTES     = 15.0                 # سماح افتراضي إن لم نجد قيمة في الشفت
WORKING_HOURS_PER_DAY  = 8.0                  # ساعات الدوام المعتمدة يوميًا
BASE_COMPONENTS        = {"راتب أساسي"}       # المكوّن/ات التي يُحتسب الخصم منها
FALLBACK_SHIFT_START   = time(8, 0)           # وقت بداية الشفت الافتراضي

DEDUCTION_COMPONENT_NAME = "خصم التاخيرات"    # Salary Component (Deduction) لخصم التأخير
DEDUCTION_ABBR           = "late_deduction"    # اختصار بند خصم التأخيرات

# البنود التي تدخل في "إجمالي الخصومات" (حسب اختصاراتها)
INCLUDE_IN_TOTAL_ABBRS = {"amd_tax_1", "loans", "ABS_USD", "late_deduction"}

# اسم/اختصار سطر "إجمالي الخصومات" الموجود مسبقًا
TOTAL_DED_ROW_NAMES = {"اجمالي الخصومات", "إجمالي الخصومات"}
TOTAL_DED_ROW_ABBRS = {"to_reb_amd", "amd_total"}

# اسم/اختصار سطر "صافي الراتب" الموجود مسبقًا
NET_PAY_ROW_NAMES = {"صافي الراتب", "صـافي الــراتب"}
NET_PAY_ROW_ABBRS = {"Amd_net_pay", "amd_net_pay"}

# اسم/اختصار سطر "اجمالي الكلي" في جدول الـ Earnings (المطلوب للصافي)
GROSS_ROW_NAMES = {"اجمالي الكلي", "إجمالي الكلي"}
GROSS_ROW_ABBRS = {"amd_total", "amd_total"}
# =================================================


class CustomSalarySlip(SalarySlip):

    # ======= تشغيل المنطق فقط عند توفر مكوّن "خصم التاخيرات" =======
    def _late_component_available(self) -> bool:
        # موجود كـ Salary Component؟
        if not frappe.db.exists("Salary Component", DEDUCTION_COMPONENT_NAME):
            return False

        # لو للسليب Salary Structure: هل المكوّن موجود فيها؟
        if self.salary_structure and frappe.db.exists(
            "Salary Detail",
            {
                "parenttype": "Salary Structure",
                "parent": self.salary_structure,
                "salary_component": DEDUCTION_COMPONENT_NAME,
            },
        ):
            return True

        # أو هل المكوّن موجود بالفعل كسطر داخل هذا السليب؟
        for r in (self.deductions or []):
            if (r.salary_component or "").strip() == DEDUCTION_COMPONENT_NAME:
                return True

        # إن أردت الاكتفاء بوجود الـ Component فقط، غيّر السطر التالي إلى: return True
        return False

    # ترتيب التنفيذ:
    #  - نترك HRMS يتحقق أولًا
    #  - (إن توفّر المكوّن) نحسب التأخيرات ونضيف بند الخصم
    #  - (إن توفّر المكوّن) قبل الحفظ نعيد تجميع إجمالي الخصومات والصافي ونُثبِّت السطرين
    def validate(self):
        super().validate()
        if self._late_component_available():
            self.apply_late_deduction()

    def before_save(self):
        if self._late_component_available():
            self._recalc_totals_into_existing_rows()
            self._freeze_total_and_net_rows()

    # ================= أدوات مساعدة للوقت/الشفت =================
    @staticmethod
    def _minutes_diff(later_dt: datetime, earlier_dt: datetime) -> float:
        try:
            return (later_dt - earlier_dt).total_seconds() / 60.0
        except Exception:
            return 0.0

    @staticmethod
    def _coerce_shift_start(val) -> time:
        # أحيانًا start_time يُخزَّن timedelta
        if isinstance(val, time):
            return val
        if isinstance(val, timedelta):
            base = datetime.min + val
            return time(base.hour, base.minute, base.second)
        return FALLBACK_SHIFT_START

    def _get_shift_meta(self, employee, the_date: date):
        """
        إرجاع (start_time: time, late_grace: float) من الشفت الفعّال في ذلك اليوم.
        نقرأ Enable Late Entry Marking و Late Entry Grace Period من Shift Type.
        """
        rec = frappe.db.sql(
            """
            SELECT st.start_time, st.enable_late_entry_marking, st.late_entry_grace_period
            FROM `tabShift Assignment` sa
            JOIN `tabShift Type` st ON st.name = sa.shift_type
            WHERE sa.employee=%s
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
            late_grace = 0.0 if not enable_late else (float(grace_val) if grace_val is not None else LATE_GRACE_MINUTES)

        return start_time, late_grace

    # ---------------- تجميع دقائق التأخير لكل يوم ----------------
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

        # 2) من Employee Checkin (لأيام لا توجد لها in_time)
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
            if d in late_by_day:  # عندنا Attendance هذا اليوم
                continue
            st_time, grace = self._get_shift_meta(employee, d)
            shift_start_dt = datetime.combine(d, st_time)
            late_after_grace = self._minutes_diff(in_dt, shift_start_dt) - grace
            if late_after_grace > 0:
                late_by_day[d] = late_after_grace

        return late_by_day

    @staticmethod
    def _sum_base_components(earnings_childtable) -> float:
        total = 0.0
        for row in (earnings_childtable or []):
            comp = (row.salary_component or "").strip()
            if comp in BASE_COMPONENTS:
                total += float(row.amount or 0)
        return total

    # ================== إنشاء/تحديث بند خصم التأخيرات ==================
    def _upsert_deduction_row(self, amount: float, component_name: str = DEDUCTION_COMPONENT_NAME):
        # لا تُنشئ/تُحدّث لو المكوّن غير متوفر
        if not self._late_component_available():
            return

        for row in (self.deductions or []):
            if (row.salary_component or "").strip() == component_name:
                row.amount = float(amount or 0)
                row.abbr = DEDUCTION_ABBR
                row.do_not_include_in_total = 0
                return
        self.append("deductions", {
            "salary_component": component_name,
            "amount": float(amount or 0),
            "abbr": DEDUCTION_ABBR,
            "do_not_include_in_total": 0,
        })

    # ====================== المنطق الرئيسي للتأخيرات ======================
    def apply_late_deduction(self):
        # إن لم يكن المكوّن متوفرًا، لا نفعل شيئًا
        if not self._late_component_available():
            return

        # خريطة دقائق التأخير لكل يوم
        by_day = self._late_minutes_by_day(self.employee, self.start_date, self.end_date)

        # تعبئة الجدول الفرعي custom_late_days (إن وُجد)
        try:
            self.set("custom_late_days", [])
        except Exception:
            pass

        days_count = 0
        total_minutes = 0.0

        for d in sorted(by_day.keys()):
            minutes = float(by_day[d] or 0)
            if minutes <= 0:
                continue
            days_count += 1
            total_minutes += minutes
            try:
                self.append("custom_late_days", {"date": d, "minutes": minutes})
            except Exception:
                pass
  
        # حقول مساعدة (إن وُجدت في الدوك تايب)
        if hasattr(self, "custom_number_of_late_days"):
            self.custom_number_of_late_days = float(days_count)
        if hasattr(self, "custom_total_late_minutes"):
            self.custom_total_late_minutes = float(total_minutes)
        if hasattr(self, "custom_total_late_hours"):
            self.custom_total_late_hours = round(float(total_minutes) / 60.0, 3)

        # احسب مبلغ خصم التأخير
        base_amount = self._sum_base_components(self.earnings)
        payment_days = float(self.payment_days or self.total_working_days or 26.0)
        minutes_in_period = WORKING_HOURS_PER_DAY * 60.0 * payment_days

        late_deduction = 0.0
        if base_amount > 0 and minutes_in_period > 0 and total_minutes > 0:
            late_deduction = base_amount * (total_minutes / minutes_in_period)

        if hasattr(self, "custom_late_deduction_amount"):
            self.custom_late_deduction_amount = float(late_deduction or 0)

        # أضِف/حدّث بند الخصم
        self._upsert_deduction_row(late_deduction, DEDUCTION_COMPONENT_NAME)

    # =================== التعرف على السطور الخاصة ===================
    def _is_total_row(self, row) -> bool:
        name = (row.salary_component or "").strip()
        abbr = (row.abbr or "").strip()
        return (name in TOTAL_DED_ROW_NAMES) or (abbr in TOTAL_DED_ROW_ABBRS) or ("إجمالي" in name and "خصومات" in name)

    def _is_net_row(self, row) -> bool:
        name = (row.salary_component or "").strip()
        abbr = (row.abbr or "").strip().lower()
        return (name in NET_PAY_ROW_NAMES) or (row.abbr in NET_PAY_ROW_ABBRS) or ("صافي" in name) or ("net" in abbr and "pay" in abbr)

    def _is_gross_row(self, row) -> bool:
        name = (row.salary_component or "").strip()
        abbr = (row.abbr or "").strip()
        return (name in GROSS_ROW_NAMES) or (abbr in GROSS_ROW_ABBRS)

    def _get_gross_from_earnings(self) -> float:
        # نبحث عن سطر "اجمالي الكلي" داخل الـ Earnings
        for r in (self.earnings or []):
            if self._is_gross_row(r):
                return float(r.amount or 0)
        # إن لم نجده، نرجع gross_pay الافتراضي
        return float(self.gross_pay or 0)

    # ===================== إعادة تجميع الإجماليات =====================
    def _recalc_totals_into_existing_rows(self):
        # 1) إجمالي الخصومات من البنود المحددة باختصارات INCLUDE_IN_TOTAL_ABBRS
        total_ded = 0.0
        for row in (self.deductions or []):
            if self._is_total_row(row) or self._is_net_row(row):
                continue
            if (row.abbr or "").strip() in INCLUDE_IN_TOTAL_ABBRS:
                total_ded += float(row.amount or 0)

        # 2) حدّث الحقول الرأسية
        try:
            prec_ded = self.precision("total_deduction")
            prec_net = self.precision("net_pay")
        except Exception:
            prec_ded = prec_net = 2

        self.total_deduction = round(total_ded, prec_ded)

        gross_from_earnings = self._get_gross_from_earnings()  # ← من "اجمالي الكلي"
        self.net_pay = round(gross_from_earnings - self.total_deduction, prec_net)
        try:
            self.rounded_total = round(self.net_pay)
        except Exception:
            pass

        # 3) اكتب النتائج في سطرَي "إجمالي الخصومات" و"صافي الراتب" إن وُجدا
        row_total = next((r for r in (self.deductions or []) if self._is_total_row(r)), None)
        if row_total:
            row_total.amount = float(self.total_deduction)
            try:
                row_total.amount_based_on_formula = 0
            except Exception:
                pass

        row_net = next((r for r in (self.deductions or []) if self._is_net_row(r)), None)
        if row_net:
            row_net.amount = float(self.net_pay)
            try:
                row_net.amount_based_on_formula = 0
                row_net.do_not_include_in_total = 1
            except Exception:
                pass

    def _freeze_total_and_net_rows(self):
        # تثبيت السطرين حتى لا تُعيد الـ Salary Structure الكتابة فوقهما
        for row in (self.deductions or []):
            name = (row.salary_component or "").strip()
            abbr = (row.abbr or "").strip().lower()

            is_total = (name in TOTAL_DED_ROW_NAMES) or (abbr in {a.lower() for a in TOTAL_DED_ROW_ABBRS}) or ("إجمالي" in name and "خصومات" in name)
            is_net = (name in NET_PAY_ROW_NAMES) or (abbr in {a.lower() for a in NET_PAY_ROW_ABBRS}) or ("صافي" in name) or ("net" in abbr and "pay" in abbr)

            if is_total or is_net:
                try:
                    row.amount_based_on_formula = 0
                except Exception:
                    pass
                try:
                    row.do_not_include_in_total = 1 if is_net else 0
                except Exception:
                    pass
