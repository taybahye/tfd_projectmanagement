
# # apps/tfd_projectmanagement/tfd_projectmanagement/overrides/salary_slip_override.py
# import frappe
# from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip
# from frappe.utils import get_datetime
# from datetime import datetime, date, time, timedelta

# # ================= إعدادات عامة قابلة للتعديل =================
# LATE_GRACE_MINUTES     = 15.0
# WORKING_HOURS_PER_DAY  = 8.0
# BASE_COMPONENTS        = {"راتب أساسي"}            # يُحسب خصم التأخير من هذا/هذه المكونات
# FALLBACK_SHIFT_START   = time(8, 0)

# # مكوّن خصم التأخيرات
# DEDUCTION_COMPONENT_NAME = "خصم التاخيرات"
# DEDUCTION_ABBR           = "late_deduction"

# # بند الوعاء الضريبي + مختصره (حسب Salary Structure لديك)
# TAXABLE_NAMES  = {"الوعاء الضريبي"}
# TAXABLE_ABBR   = "amd_taxable"

# # بند غياب USD + مختصره
# ABSENCE_NAMES  = {"غياب USD"}
# ABSENCE_ABBR   = "ABS_USD"

# # اسم حقل معامل التحويل في Salary Slip (Custom Field)
# TAX_EXCHANGE_FIELD = "custom_tax_exchange"         # غيّره لو اسمك مختلف

# # البنود التي تدخل في إجمالي الخصومات (حسب اختصاراتها)
# INCLUDE_IN_TOTAL_ABBRS = {"amd_tax_1", "loans", "ABS_USD", "late_deduction"}

# # أسماء/اختصارات السطور الخاصة داخل جدول الخصميات
# TOTAL_DED_ROW_NAMES = {"اجمالي الخصومات", "إجمالي الخصومات"}
# TOTAL_DED_ROW_ABBRS = {"to_reb_amd", "amd_total"}

# NET_PAY_ROW_NAMES  = {"صافي الراتب", "صـافي الــراتب"}
# NET_PAY_ROW_ABBRS  = {"Amd_net_pay", "amd_net_pay"}

# # اسم/اختصار سطر "إجمالي الكلي" داخل الـ Earnings (لاحتساب الصافي)
# GROSS_ROW_NAMES = {"اجمالي الكلي", "إجمالي الكلي"}
# GROSS_ROW_ABBRS = {"amd_total"}
# # ===============================================================


# class CustomSalarySlip(SalarySlip):

#     # نشغّل المنطق فقط إذا كان مكوّن "خصم التاخيرات" موجودًا (أو موجود سطره)
#     def _should_run_override(self) -> bool:
#         if frappe.db.exists("Salary Component", DEDUCTION_COMPONENT_NAME):
#             return True
#         for r in (self.deductions or []):
#             name = (r.salary_component or "").strip()
#             abbr = (r.abbr or "").strip()
#             if name == DEDUCTION_COMPONENT_NAME or abbr == DEDUCTION_ABBR:
#                 return True
#         return False

#     # # -------- دورة التنفيذ --------
#     def validate(self):
#         # شغّل أوفررايد فقط إذا كان مكوّن "خصم التاخيرات" موجود
#         if self._should_run_override():
#             # 1) احسب خصم التأخيرات أولاً
#             self.apply_late_deduction()

#         # 2) الآن دَع HRMS يُعيد تشغيل معادلات Salary Structure
#         super().validate()

#         if self._should_run_override():
#             # 2.5) أعد إظهار سطر خصم التأخيرات إن اختفى أثناء super().validate()
#             self._restore_late_row_if_missing()
#             # 3) بعد انتهاء معادلات الـ Structure:
#             #    أعِد تجميع إجمالي الخصومات + صافي الراتب وثبّت السطرين
#             self._recalc_totals_into_existing_rows()
#             self._freeze_total_and_net_rows()

#     def before_save(self):
#         if not self._should_run_override():
#             return
#         # مجرّد ضمان أخير للترتيب النهائى في السليب:
#         self._recalc_totals_into_existing_rows()
#         self._freeze_total_and_net_rows()
#     # def validate(self):
#     #     super().validate()
#     #     if not self._should_run_override():
#     #         return
#     #     self.apply_late_deduction()
#     #     self._recompute_taxable_base()
#     #     self._recalc_totals_into_existing_rows()
#     #     self._freeze_total_and_net_rows()

#     # def before_save(self):
#     #     if not self._should_run_override():
#     #         return
#     #     # نتأكد أن آخر كتابة من عندنا
#     #     self._recompute_taxable_base()
#     #     self._recalc_totals_into_existing_rows()
#     #     self._freeze_total_and_net_rows()

#     # ================= أدوات مساعدة للوقت/الشفت =================
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

#     def _get_shift_meta(self, employee, the_date: date):
#         rec = frappe.db.sql(
#             """
#             SELECT st.start_time, st.enable_late_entry_marking, st.late_entry_grace_period
#             FROM `tabShift Assignment` sa
#             JOIN `tabShift Type` st ON st.name = sa.shift_type
#             WHERE sa.employee = %s
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

#     # -------- تجميع دقائق التأخير لكل يوم --------
#     def _late_minutes_by_day(self, employee, start_date, end_date):
#         late_by_day = {}

#         # من Attendance
#         atts = frappe.get_all(
#             "Attendance",
#             filters={"employee": employee, "attendance_date": ["between", [start_date, end_date]], "docstatus": 1},
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

#         # من Employee Checkin (للأيام بلا in_time)
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
#             if d in late_by_day:
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
#                 try:
#                     row.do_not_include_in_total = 0
#                 except Exception:
#                     pass
#                 return
#         self.append("deductions", {
#             "salary_component": component_name,
#             "amount": float(amount or 0),
#             "abbr": DEDUCTION_ABBR,
#             "do_not_include_in_total": 0,
#         })

#     # ====================== المنطق الرئيسي للتأخيرات ======================
#     def apply_late_deduction(self):
#         by_day = self._late_minutes_by_day(self.employee, self.start_date, self.end_date)

#         # املأ جدول تفاصيل التأخيرات (إن وُجد)
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

#         # حقول مساعدة اختيارية
#         if hasattr(self, "custom_number_of_late_days"):
#             self.custom_number_of_late_days = float(days_count)
#         if hasattr(self, "custom_total_late_minutes"):
#             self.custom_total_late_minutes = float(total_minutes)
#         if hasattr(self, "custom_total_late_hours"):
#             self.custom_total_late_hours = round(float(total_minutes) / 60.0, 3)

#         # احسب مبلغ الخصم
#         base_amount = self._sum_base_components(self.earnings)
#         payment_days = float(self.payment_days or self.total_working_days or 26.0)
#         minutes_in_period = WORKING_HOURS_PER_DAY * 60.0 * payment_days

#         late_deduction = 0.0
#         if base_amount > 0 and minutes_in_period > 0 and total_minutes > 0:
#             late_deduction = base_amount * (total_minutes / minutes_in_period)

#         if hasattr(self, "custom_late_deduction_amount"):
#             self.custom_late_deduction_amount = float(late_deduction or 0)

#         # خزّن القيمة لنستعملها بعد super().validate() لو اختفى السطر
#         self._late_amount = float(late_deduction or 0)

#         self._upsert_deduction_row(late_deduction, DEDUCTION_COMPONENT_NAME)
        
        
#     def _restore_late_row_if_missing(self):
#         """أعد إظهار سطر 'خصم التاخيرات' بعد super().validate() لو أنه اختفى."""
#         amt = float(getattr(self, "_late_amount", 0.0))
#         found = False
#         for row in (self.deductions or []):
#             name = (row.salary_component or "").strip()
#             abbr = (row.abbr or "").strip()
#             if name == DEDUCTION_COMPONENT_NAME or abbr == DEDUCTION_ABBR:
#                 # حدّثه بالقيمة المخزّنة
#                 row.amount = amt
#                 row.abbr = DEDUCTION_ABBR
#                 try:
#                     row.do_not_include_in_total = 0
#                 except Exception:
#                     pass
#                 found = True
#                 break

#         if not found:
#             # لم نجده: أضفه من جديد
#             self.append("deductions", {
#                 "salary_component": DEDUCTION_COMPONENT_NAME,
#                 "abbr": DEDUCTION_ABBR,
#                 "amount": amt,
#                 "do_not_include_in_total": 0,
#             })

#     # =================== التعرف على السطور الخاصة ===================
#     def _match_row(self, row, names:set[str], abbrs:set[str]) -> bool:
#         name = (row.salary_component or "").strip()
#         abbr = (row.abbr or "").strip()
#         return (name in names) or (abbr in abbrs)

#     def _is_total_row(self, row) -> bool:
#         return self._match_row(row, TOTAL_DED_ROW_NAMES, TOTAL_DED_ROW_ABBRS) or \
#                ("إجمالي" in (row.salary_component or "") and "خصومات" in (row.salary_component or ""))

#     def _is_net_row(self, row) -> bool:
#         name = (row.salary_component or "").strip()
#         abbr = (row.abbr or "").strip().lower()
#         return (name in NET_PAY_ROW_NAMES) or (abbr in {a.lower() for a in NET_PAY_ROW_ABBRS}) or \
#                ("صافي" in name) or ("net" in abbr and "pay" in abbr)

#     def _is_gross_row_earn(self, r) -> bool:
#         name = (r.salary_component or "").strip()
#         abbr = (r.abbr or "").strip()
#         return (name in GROSS_ROW_NAMES) or (abbr in GROSS_ROW_ABBRS)

#     def _get_gross_from_earnings(self) -> float:
#         for r in (self.earnings or []):
#             if self._is_gross_row_earn(r):
#                 return float(r.amount or 0)
#         return float(self.gross_pay or 0)

#     def _get_amount_any(self, names:set[str], abbrs:set[str]) -> float:
#         for r in (self.deductions or []):
#             if self._match_row(r, names, abbrs):
#                 return float(r.amount or 0)
#         return 0.0

#     # ==================== تحديث الوعاء الضريبي ====================
#     def _recompute_taxable_base(self):
#         # راتب أساسي (قد يكون أكثر من صف)
#         base_salary = 0.0
#         for r in (self.earnings or []):
#             if (r.salary_component or "").strip() in BASE_COMPONENTS:
#                 base_salary += float(r.amount or 0)

#         abs_usd = self._get_amount_any(ABSENCE_NAMES, {ABSENCE_ABBR})
#         late    = self._get_amount_any({DEDUCTION_COMPONENT_NAME}, {DEDUCTION_ABBR})

#         # معامل التحويل
#         try:
#             exchange = float(getattr(self, TAX_EXCHANGE_FIELD))
#         except Exception:
#             exchange = 1.0

#         taxable_val = (base_salary - abs_usd - late) * exchange

#         # حدّث صف الوعاء الضريبي (بالاسم أو بالاختصار) وثبّته
#         for row in (self.deductions or []):
#             if self._match_row(row, TAXABLE_NAMES, {TAXABLE_ABBR}):
#                 row.amount = float(taxable_val or 0)
#                 try:
#                     row.amount_based_on_formula = 0   # إيقاف الصيغة
#                     row.do_not_include_in_total = 1   # لا يدخل في الإجمالي
#                 except Exception:
#                     pass
#                 break

#     # ===================== إعادة تجميع الإجماليات =====================
#     def _recalc_totals_into_existing_rows(self):
#         # إجمالي الخصومات من اختصارات محددة
#         total_ded = 0.0
#         for row in (self.deductions or []):
#             if self._is_total_row(row) or self._is_net_row(row):
#                 continue
#             if (row.abbr or "").strip() in INCLUDE_IN_TOTAL_ABBRS:
#                 total_ded += float(row.amount or 0)

#         try:
#             prec_ded = self.precision("total_deduction")
#             prec_net = self.precision("net_pay")
#         except Exception:
#             prec_ded = prec_net = 2

#         self.total_deduction = round(total_ded, prec_ded)
#         gross_from_earnings = self._get_gross_from_earnings()
#         self.net_pay = round(gross_from_earnings - self.total_deduction, prec_net)
#         try:
#             self.rounded_total = round(self.net_pay)
#         except Exception:
#             pass

#         # اكتب النتائج في الصفوف الخاصة إن وُجدت
#         for r in (self.deductions or []):
#             if self._is_total_row(r):
#                 r.amount = float(self.total_deduction)
#                 try:
#                     r.amount_based_on_formula = 0
#                 except Exception:
#                     pass
#             elif self._is_net_row(r):
#                 r.amount = float(self.net_pay)
#                 try:
#                     r.amount_based_on_formula = 0
#                     r.do_not_include_in_total = 1
#                 except Exception:
#                     pass

#     # تثبيت الصفوف الخاصة حتى لا تُعاد كتابتها بمعادلات الـ Structure
#     def _freeze_total_and_net_rows(self):
#         for row in (self.deductions or []):
#             if self._is_total_row(row) or self._is_net_row(row):
#                 try:
#                     row.amount_based_on_formula = 0
#                 except Exception:
#                     pass
#                 if self._is_net_row(row):
#                     try:
#                         row.do_not_include_in_total = 1
#                     except Exception:
#                         pass

# # apps/tfd_projectmanagement/tfd_projectmanagement/overrides/salary_slip_override.py
# import frappe
# from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip
# from frappe.utils import get_datetime
# from datetime import datetime, date, time, timedelta

# # ================= إعدادات عامة قابلة للتعديل =================
# LATE_GRACE_MINUTES    = 15.0
# WORKING_HOURS_PER_DAY = 8.0
# BASE_COMPONENTS       = {"راتب أساسي"}
# FALLBACK_SHIFT_START  = time(8, 0)

# # مكوّن خصم التأخيرات
# DEDUCTION_COMPONENT_NAME = "خصم التاخيرات"
# DEDUCTION_ABBR           = "late_deduction"

# # بند الوعاء الضريبي
# TAXABLE_NAMES  = {"الوعاء الضريبي"}
# TAXABLE_ABBR   = "amd_taxable"

# # بند غياب USD
# ABSENCE_NAMES  = {"غياب USD"}
# ABSENCE_ABBR   = "ABS_USD"

# # اسم حقل معامل التحويل في Salary Slip (Custom Field)
# TAX_EXCHANGE_FIELD = "custom_tax_exchange"

# # البنود التي تدخل في إجمالي الخصومات (حسب اختصاراتها)
# INCLUDE_IN_TOTAL_ABBRS = {"amd_tax_1", "loans", "ABS_USD", "late_deduction"}

# # أسماء/اختصارات السطور الخاصة داخل جدول الخصميات
# TOTAL_DED_ROW_NAMES = {"اجمالي الخصومات", "إجمالي الخصومات"}
# TOTAL_DED_ROW_ABBRS = {"to_reb_amd", "amd_total"}

# NET_PAY_ROW_NAMES = {"صافي الراتب", "صـافي الــراتب"}
# NET_PAY_ROW_ABBRS = {"Amd_net_pay", "amd_net_pay"}

# # سطر "إجمالي الكلي" داخل Earnings (لاحتساب الصافي)
# GROSS_ROW_NAMES = {"اجمالي الكلي", "إجمالي الكلي"}
# GROSS_ROW_ABBRS = {"amd_total"}
# # ===============================================================


# class CustomSalarySlip(SalarySlip):

#     # نشغّل الأوفررايد فقط إذا كان مكوّن "خصم التاخيرات" موجودًا (كمكوّن أو كسطر)
#     def _should_run_override(self) -> bool:
#         if frappe.db.exists("Salary Component", DEDUCTION_COMPONENT_NAME):
#             return True
#         for r in (self.deductions or []):
#             name = (r.salary_component or "").strip()
#             abbr = (r.abbr or "").strip()
#             if name == DEDUCTION_COMPONENT_NAME or abbr == DEDUCTION_ABBR:
#                 return True
#         return False

#     # -------- دورة التنفيذ --------
#     def validate(self):
#         second_pass = getattr(self, "_second_pass", False)

#         if self._should_run_override() and not second_pass:
#             # (1) احسب خصم التأخيرات أولًا
#             self.apply_late_deduction()

#         # (2) شغّل معادلات الـ Structure
#         super().validate()

#         if not self._should_run_override():
#             return

#         # (3) أعِد إظهار بند التأخيرات إن اختفى
#         self._restore_late_row_if_missing()

#         # (4) أعِد توليد الوعاء الضريبي بعد خصم الغياب + التأخيرات
#         self._recompute_taxable_base()

#         # (5) شغّل super().validate() ثانيةً ليتم حساب الضرائب بناءً على الوعاء الجديد
#         if not second_pass:
#             self._second_pass = True
#             super().validate()
#             # بعد الإعادة قد يختفي بند التأخيرات مجددًا — أعِده
#             self._restore_late_row_if_missing()

#         # (6) إجمالي الخصومات + الصافي وتثبيت السطور
#         self._recalc_totals_into_existing_rows()
#         self._freeze_total_and_net_rows()

#     def before_save(self):
#         if not self._should_run_override():
#             return
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
#         if isinstance(val, time):
#             return val
#         if isinstance(val, timedelta):
#             base = datetime.min + val
#             return time(base.hour, base.minute, base.second)
#         return FALLBACK_SHIFT_START

#     def _get_shift_meta(self, employee, the_date: date):
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

#     # -------- تجميع دقائق التأخير لكل يوم --------
#     def _late_minutes_by_day(self, employee, start_date, end_date):
#         late_by_day = {}

#         # من Attendance
#         atts = frappe.get_all(
#             "Attendance",
#             filters={"employee": employee, "attendance_date": ["between", [start_date, end_date]], "docstatus": 1},
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

#         # من Employee Checkin (للأيام بلا in_time)
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
#             if d in late_by_day:
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
#                 try:
#                     row.do_not_include_in_total = 0
#                 except Exception:
#                     pass
#                 return
#         self.append("deductions", {
#             "salary_component": component_name,
#             "amount": float(amount or 0),
#             "abbr": DEDUCTION_ABBR,
#             "do_not_include_in_total": 0,
#         })

#     # ====================== المنطق الرئيسي للتأخيرات ======================
#     def apply_late_deduction(self):
#         by_day = self._late_minutes_by_day(self.employee, self.start_date, self.end_date)

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

#         if hasattr(self, "custom_number_of_late_days"):
#             self.custom_number_of_late_days = float(days_count)
#         if hasattr(self, "custom_total_late_minutes"):
#             self.custom_total_late_minutes = float(total_minutes)
#         if hasattr(self, "custom_total_late_hours"):
#             self.custom_total_late_hours = round(float(total_minutes) / 60.0, 3)

#         base_amount = self._sum_base_components(self.earnings)
#         payment_days = float(self.payment_days or self.total_working_days or 26.0)
#         minutes_in_period = WORKING_HOURS_PER_DAY * 60.0 * payment_days

#         late_deduction = 0.0
#         if base_amount > 0 and minutes_in_period > 0 and total_minutes > 0:
#             late_deduction = base_amount * (total_minutes / minutes_in_period)

#         if hasattr(self, "custom_late_deduction_amount"):
#             self.custom_late_deduction_amount = float(late_deduction or 0)

#         # خزّن القيمة لنستعملها إن اختفى السطر بعد الـ Structure
#         self._late_amount = float(late_deduction or 0)

#         self._upsert_deduction_row(late_deduction, DEDUCTION_COMPONENT_NAME)

#     def _restore_late_row_if_missing(self):
#         """أعد إظهار سطر 'خصم التاخيرات' لو اختفى أثناء super().validate()."""
#         amt = float(getattr(self, "_late_amount", 0.0))
#         found = False
#         for row in (self.deductions or []):
#             name = (row.salary_component or "").strip()
#             abbr = (row.abbr or "").strip()
#             if name == DEDUCTION_COMPONENT_NAME or abbr == DEDUCTION_ABBR:
#                 row.amount = amt
#                 row.abbr = DEDUCTION_ABBR
#                 try:
#                     row.do_not_include_in_total = 0
#                 except Exception:
#                     pass
#                 found = True
#                 break
#         if not found:
#             self.append("deductions", {
#                 "salary_component": DEDUCTION_COMPONENT_NAME,
#                 "abbr": DEDUCTION_ABBR,
#                 "amount": amt,
#                 "do_not_include_in_total": 0,
#             })

#     # =================== التعرف على السطور الخاصة ===================
#     def _match_row(self, row, names:set[str], abbrs:set[str]) -> bool:
#         name = (row.salary_component or "").strip()
#         abbr = (row.abbr or "").strip()
#         return (name in names) or (abbr in abbrs)

#     def _is_total_row(self, row) -> bool:
#         return self._match_row(row, TOTAL_DED_ROW_NAMES, TOTAL_DED_ROW_ABBRS) or \
#                ("إجمالي" in (row.salary_component or "") and "خصومات" in (row.salary_component or ""))

#     def _is_net_row(self, row) -> bool:
#         name = (row.salary_component or "").strip()
#         abbr = (row.abbr or "").strip().lower()
#         return (name in NET_PAY_ROW_NAMES) or (abbr in {a.lower() for a in NET_PAY_ROW_ABBRS}) or \
#                ("صافي" in name) or ("net" in abbr and "pay" in abbr)

#     def _is_gross_row_earn(self, r) -> bool:
#         name = (r.salary_component or "").strip()
#         abbr = (r.abbr or "").strip()
#         return (name in GROSS_ROW_NAMES) or (abbr in GROSS_ROW_ABBRS)

#     def _get_gross_from_earnings(self) -> float:
#         for r in (self.earnings or []):
#             if self._is_gross_row_earn(r):
#                 return float(r.amount or 0)
#         return float(self.gross_pay or 0)

#     def _get_amount_any(self, names:set[str], abbrs:set[str]) -> float:
#         for r in (self.deductions or []):
#             if self._match_row(r, names, abbrs):
#                 return float(r.amount or 0)
#         return 0.0

#     # ==================== تحديث الوعاء الضريبي ====================
#     def _recompute_taxable_base(self):
#         base_salary = 0.0
#         for r in (self.earnings or []):
#             if (r.salary_component or "").strip() in BASE_COMPONENTS:
#                 base_salary += float(r.amount or 0)

#         abs_usd = self._get_amount_any(ABSENCE_NAMES, {ABSENCE_ABBR})
#         late    = self._get_amount_any({DEDUCTION_COMPONENT_NAME}, {DEDUCTION_ABBR})

#         try:
#             exchange = float(getattr(self, TAX_EXCHANGE_FIELD))
#         except Exception:
#             exchange = 1.0

#         taxable_val = (base_salary - abs_usd - late) * exchange

#         for row in (self.deductions or []):
#             if self._match_row(row, TAXABLE_NAMES, {TAXABLE_ABBR}):
#                 row.amount = float(taxable_val or 0)
#                 # لا نجعل هذا البند يدخل الإجمالي، لكن لا نمنع الـ Structure من قراءته
#                 try:
#                     row.amount_based_on_formula = 0
#                     row.do_not_include_in_total = 1
#                 except Exception:
#                     pass
#                 break

#     # ===================== إعادة تجميع الإجماليات =====================
#     def _recalc_totals_into_existing_rows(self):
#         total_ded = 0.0
#         for row in (self.deductions or []):
#             if self._is_total_row(row) or self._is_net_row(row):
#                 continue
#             if (row.abbr or "").strip() in INCLUDE_IN_TOTAL_ABBRS:
#                 total_ded += float(row.amount or 0)

#         try:
#             prec_ded = self.precision("total_deduction")
#             prec_net = self.precision("net_pay")
#         except Exception:
#             prec_ded = prec_net = 2

#         self.total_deduction = round(total_ded, prec_ded)
#         gross_from_earnings = self._get_gross_from_earnings()
#         self.net_pay = round(gross_from_earnings - self.total_deduction, prec_net)
#         try:
#             self.rounded_total = round(self.net_pay)
#         except Exception:
#             pass

#         for r in (self.deductions or []):
#             if self._is_total_row(r):
#                 r.amount = float(self.total_deduction)
#                 try:
#                     r.amount_based_on_formula = 0
#                 except Exception:
#                     pass
#             elif self._is_net_row(r):
#                 r.amount = float(self.net_pay)
#                 try:
#                     r.amount_based_on_formula = 0
#                     r.do_not_include_in_total = 1
#                 except Exception:
#                     pass

#     def _freeze_total_and_net_rows(self):
#         for row in (self.deductions or []):
#             if self._is_total_row(row) or self._is_net_row(row):
#                 try:
#                     row.amount_based_on_formula = 0
#                 except Exception:
#                     pass
#                 if self._is_net_row(row):
#                     try:
#                         row.do_not_include_in_total = 1
#                     except Exception:
#                         pass
# apps/tfd_projectmanagement/tfd_projectmanagement/overrides/salary_slip_override.py
import frappe
from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip
from frappe.utils import get_datetime
from datetime import datetime, date, time, timedelta
from frappe import _,msgprint

# ================= إعدادات عامة قابلة للتعديل =================
LATE_GRACE_MINUTES    = 15.0
WORKING_HOURS_PER_DAY = 8.0
BASE_COMPONENTS       = {"راتب أساسي"}
FALLBACK_SHIFT_START  = time(8, 0)

# مكوّن خصم التأخيرات
DEDUCTION_COMPONENT_NAME = "خصم التاخيرات"
DEDUCTION_ABBR           = "late_deduction"

# بند الوعاء الضريبي
TAXABLE_NAMES  = {"الوعاء الضريبي"}
TAXABLE_ABBR   = "amd_taxable"

# بند غياب USD
ABSENCE_NAMES  = {"غياب USD"}
ABSENCE_ABBR   = "ABS_USD"

# اسم حقل معامل التحويل في Salary Slip (Custom Field)
TAX_EXCHANGE_FIELD = "custom_tax_exchange"

# البنود الداخلة في إجمالي الخصومات
INCLUDE_IN_TOTAL_ABBRS = {"amd_tax_1", "loans", "ABS_USD", "late_deduction"}

# صفوف خاصة في الخصميات
TOTAL_DED_ROW_NAMES = {"اجمالي الخصومات", "إجمالي الخصومات"}
TOTAL_DED_ROW_ABBRS = {"to_reb_amd", "amd_total"}

NET_PAY_ROW_NAMES = {"صافي الراتب", "صـافي الــراتب"}
NET_PAY_ROW_ABBRS = {"Amd_net_pay", "amd_net_pay"}

# سطر "إجمالي الكلي" داخل Earnings (لاحتساب الصافي)
GROSS_ROW_NAMES = {"اجمالي الكلي", "إجمالي الكلي"}
GROSS_ROW_ABBRS = {"amd_total"}
# ===============================================================


class CustomSalarySlip(SalarySlip):

    # نشغّل الأوفررايد فقط إذا كان مكوّن "خصم التاخيرات" موجودًا (كمكوّن أو كسطر)
    def _should_run_override(self) -> bool:
        if frappe.db.exists("Salary Component", DEDUCTION_COMPONENT_NAME):
            return True
        for r in (self.deductions or []):
            name = (r.salary_component or "").strip()
            abbr = (r.abbr or "").strip()
            if name == DEDUCTION_COMPONENT_NAME or abbr == DEDUCTION_ABBR:
                return True
        return False

    # -------- دورة التنفيذ --------
    def validate(self):
        if self._should_run_override():
            # (1) احسب خصم التأخيرات أولًا (قبل الـ Structure)
            self.apply_late_deduction()

        # (2) مرّة واحدة: دَع الـ Structure يحسب باقي البنود/الضرائب
        super().validate()
        msgprint(_(str("taxable_val")))
        if not self._should_run_override():
            return

        # (3) أعِد إظهار بند التأخيرات لو اختفى أثناء الـ Structure
        self._restore_late_row_if_missing()

        # (4) أعِد حساب "الوعاء الضريبي" الصحيح وجمّده كي لا يُعاد استبداله
        self._recompute_and_freeze_taxable_base()
        msgprint(_(str('ffffff')))
        self._recompute_yemeni_tax()
        # (5) أعِد تجميع إجمالي الخصومات والصافي وثبّت سطور الإجمالي/الصافي
        self._recalc_totals_into_existing_rows()
        self._freeze_total_and_net_rows()

    def before_save(self):
        if not self._should_run_override():
            return
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
        if isinstance(val, time):
            return val
        if isinstance(val, timedelta):
            base = datetime.min + val
            return time(base.hour, base.minute, base.second)
        return FALLBACK_SHIFT_START

    def _get_shift_meta(self, employee, the_date: date):
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

    # -------- تجميع دقائق التأخير لكل يوم --------
    def _late_minutes_by_day(self, employee, start_date, end_date):
        late_by_day = {}

        # من Attendance
        atts = frappe.get_all(
            "Attendance",
            filters={"employee": employee, "attendance_date": ["between", [start_date, end_date]], "docstatus": 1},
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

        # من Employee Checkin (للأيام بلا in_time)
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
        total = 0.0
        for row in (earnings_childtable or []):
            comp = (row.salary_component or "").strip()
            if comp in BASE_COMPONENTS:
                total += float(row.amount or 0)
        return total

    # ================== إنشاء/تحديث بند خصم التأخيرات ==================
    def _upsert_deduction_row(self, amount: float, component_name: str = DEDUCTION_COMPONENT_NAME):
        for row in (self.deductions or []):
            if (row.salary_component or "").strip() == component_name:
                row.amount = float(amount or 0)
                row.abbr = DEDUCTION_ABBR
                try:
                    row.do_not_include_in_total = 0
                except Exception:
                    pass
                return
        self.append("deductions", {
            "salary_component": component_name,
            "amount": float(amount or 0),
            "abbr": DEDUCTION_ABBR,
            "do_not_include_in_total": 0,
            "is_additional_salary_component": 1,  
        })

   
    # ====================== المنطق الرئيسي للتأخيرات ======================
    def apply_late_deduction(self):
        by_day = self._late_minutes_by_day(self.employee, self.start_date, self.end_date)

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

        if hasattr(self, "custom_number_of_late_days"):
            self.custom_number_of_late_days = float(days_count)
        if hasattr(self, "custom_total_late_minutes"):
            self.custom_total_late_minutes = float(total_minutes)
        if hasattr(self, "custom_total_late_hours"):
            self.custom_total_late_hours = round(float(total_minutes) / 60.0, 3)

        base_amount = self._sum_base_components(self.earnings)
        payment_days = float(self.payment_days or self.total_working_days or 26.0)
        minutes_in_period = WORKING_HOURS_PER_DAY * 60.0 * payment_days

        late_deduction = 0.0
        if base_amount > 0 and minutes_in_period > 0 and total_minutes > 0:
            late_deduction = base_amount * (total_minutes / minutes_in_period)

        if hasattr(self, "custom_late_deduction_amount"):
            self.custom_late_deduction_amount = float(late_deduction or 0)

        self._late_amount = float(late_deduction or 0)  # للاستخدام بعد الـ Structure
        self._upsert_deduction_row(late_deduction, DEDUCTION_COMPONENT_NAME)

    def _restore_late_row_if_missing(self):
        amt = float(getattr(self, "_late_amount", 0.0))
        found = False
        for row in (self.deductions or []):
            name = (row.salary_component or "").strip()
            abbr = (row.abbr or "").strip()
            if name == DEDUCTION_COMPONENT_NAME or abbr == DEDUCTION_ABBR:
                row.amount = amt
                row.abbr = DEDUCTION_ABBR
                try:
                    row.do_not_include_in_total = 0
                except Exception:
                    pass
                found = True
                break
        if not found:
            self.append("deductions", {
                "salary_component": DEDUCTION_COMPONENT_NAME,
                "abbr": DEDUCTION_ABBR,
                "amount": amt,
                "do_not_include_in_total": 0,
            })

    # =================== التعرف على السطور الخاصة ===================
    def _match_row(self, row, names:set[str], abbrs:set[str]) -> bool:
        name = (row.salary_component or "").strip()
        abbr = (row.abbr or "").strip()
        return (name in names) or (abbr in abbrs)

    def _is_total_row(self, row) -> bool:
        return self._match_row(row, TOTAL_DED_ROW_NAMES, TOTAL_DED_ROW_ABBRS) or \
               ("إجمالي" in (row.salary_component or "") and "خصومات" in (row.salary_component or ""))

    def _is_net_row(self, row) -> bool:
        name = (row.salary_component or "").strip()
        abbr = (row.abbr or "").strip().lower()
        return (name in NET_PAY_ROW_NAMES) or (abbr in {a.lower() for a in NET_PAY_ROW_ABBRS}) or \
               ("صافي" in name) or ("net" in abbr and "pay" in abbr)

    def _is_gross_row_earn(self, r) -> bool:
        name = (r.salary_component or "").strip()
        abbr = (r.abbr or "").strip()
        return (name in GROSS_ROW_NAMES) or (abbr in GROSS_ROW_ABBRS)

    def _get_gross_from_earnings(self) -> float:
        for r in (self.earnings or []):
            if self._is_gross_row_earn(r):
                return float(r.amount or 0)
        return float(self.gross_pay or 0)

    def _get_amount_any(self, names:set[str], abbrs:set[str]) -> float:
        for r in (self.deductions or []):
            if self._match_row(r, names, abbrs):
                return float(r.amount or 0)
        return 0.0

    # ==================== الوعاء الضريبي (إعادة حساب + تجميد) ====================
    def _recompute_and_freeze_taxable_base(self):
        # اجمع راتب أساسي من الـ Earnings
        base_salary = 0.0
        for r in (self.earnings or []):
            if (r.salary_component or "").strip() in BASE_COMPONENTS:
                base_salary += float(r.amount or 0)

        abs_usd = self._get_amount_any(ABSENCE_NAMES, {ABSENCE_ABBR})
        late    = self._get_amount_any({DEDUCTION_COMPONENT_NAME}, {DEDUCTION_ABBR})

        # معامل التحويل
        try:
            exchange = float(getattr(self, TAX_EXCHANGE_FIELD))
        except Exception:
            exchange = 1.0

        taxable_val = (base_salary - abs_usd - late) * exchange

        # حدّث صف الوعاء الضريبي وجمّده حتى لا يستبدله الـ Structure
        for row in (self.deductions or []):
            if self._match_row(row, TAXABLE_NAMES, {TAXABLE_ABBR}):
                row.amount = float(taxable_val or 0)
                try:
                    row.amount_based_on_formula = 0   # << التجميد المهم
                    row.do_not_include_in_total = 1   # لا يدخل في إجمالي الخصومات
                except Exception:
                    pass
                break

     # ((amd_taxable - 20000) * 0.15 + 1000) if amd_taxable

    def _recompute_yemeni_tax(self):
        # 1) خذ قيمة الوعاء الضريبي بعد الخصم والتحديث
        taxable_val = self._get_amount_any(TAXABLE_NAMES, {TAXABLE_ABBR})
        
        msgprint(_(str(taxable_val)))
        # 2) احسب الضريبة
        yemeni_tax = 0.0
        if taxable_val > 0:
            yemeni_tax = ((taxable_val - 20000) * 0.15 + 1000) if taxable_val else 0.0
        
        msgprint(_(str(yemeni_tax)))
        
        # 3) حدّث سطر "الضريبة يمني" في الخصميات
        for row in (self.deductions or []):
            if (row.salary_component or "").strip() in {"الضريبة يمني"} or (row.abbr or "").strip() == "tax_raiel_amd":
                row.amount = float(yemeni_tax or 0)
                try:
                    row.amount_based_on_formula = 0   # وقف معادلة الـ Salary Structure
                except Exception:
                    pass
                break


    # ===================== إعادة تجميع الإجماليات =====================
    def _recalc_totals_into_existing_rows(self):
        total_ded = 0.0
        for row in (self.deductions or []):
            if self._is_total_row(row) or self._is_net_row(row):
                continue
            if (row.abbr or "").strip() in INCLUDE_IN_TOTAL_ABBRS:
                total_ded += float(row.amount or 0)

        try:
            prec_ded = self.precision("total_deduction")
            prec_net = self.precision("net_pay")
        except Exception:
            prec_ded = prec_net = 2

        self.total_deduction = round(total_ded, prec_ded)
        gross_from_earnings = self._get_gross_from_earnings()
        self.net_pay = round(gross_from_earnings - self.total_deduction, prec_net)
        try:
            self.rounded_total = round(self.net_pay)
        except Exception:
            pass

        for r in (self.deductions or []):
            if self._is_total_row(r):
                r.amount = float(self.total_deduction)
                try:
                    r.amount_based_on_formula = 0
                except Exception:
                    pass
            elif self._is_net_row(r):
                r.amount = float(self.net_pay)
                try:
                    r.amount_based_on_formula = 0
                    r.do_not_include_in_total = 1
                except Exception:
                    pass

    def _freeze_total_and_net_rows(self):
        for row in (self.deductions or []):
            if self._is_total_row(row) or self._is_net_row(row):
                try:
                    row.amount_based_on_formula = 0
                except Exception:
                    pass
                if self._is_net_row(row):
                    try:
                        row.do_not_include_in_total = 1
                    except Exception:
                        pass
