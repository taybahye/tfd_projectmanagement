# # apps/tfd_projectmanagement/tfd_projectmanagement/overrides/salary_slip_override.py
# import frappe
# from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip
# from frappe.utils import get_datetime
# from datetime import datetime, date, time, timedelta


# ##################################################################################################
# def _safe_get_assigned_ssa(start_date, employee, company):
#     # حاول تواقيع الدالة في إصدارات HRMS المختلفة
#     try:
#         from hrms.payroll.doctype.salary_structure_assignment.salary_structure_assignment import get_assigned_salary_structure
#         try:
#             return get_assigned_salary_structure(start_date, employee, company)  # بعض الإصدارات
#         except TypeError:
#             try:
#                 return get_assigned_salary_structure(start_date, employee)       # إصدارات أخرى
#             except TypeError:
#                 return get_assigned_salary_structure(employee, start_date)       # احتمال ثالث
#     except Exception:
#         pass

#     # لو فشلت كل الطرق: ابحث يدويًا عن SSA صالح (<= start_date) لنفس الشركة
#     return frappe.db.get_value(
#         "Salary Structure Assignment",
#         {
#             "employee": employee,
#             "company": company,
#             "docstatus": 1,
#             "from_date": ["<=", start_date],
#         },
#         "name",
#         order_by="from_date desc",
#     )

# def _pick_structure_fallback(employee):
#     # آخر Salary Slip سابق
#     slip = frappe.db.get_value(
#         "Salary Slip",
#         {"employee": employee, "docstatus": 1},
#         ["salary_structure"],
#         order_by="start_date desc",
#         as_dict=True,
#     )
#     if slip and slip.get("salary_structure"):
#         return slip["salary_structure"]

#     # أو آخر SSA لأي شركة
#     any_ssa = frappe.db.get_value(
#         "Salary Structure Assignment",
#         {"employee": employee, "docstatus": 1},
#         ["salary_structure"],
#         order_by="from_date desc",
#         as_dict=True,
#     )
#     if any_ssa and any_ssa.get("salary_structure"):
#         return any_ssa["salary_structure"]

#     # لو تبغى تفرض هيكل افتراضي عام علّقه هنا بدل None (مثال: "Monthly - TFD")
#     return None


# def _ensure_ssa_for_period(start_date, employee, company):
#     """
#     يرجع (ssa_name, salary_structure).
#     لا ينشئ SSA جديدًا إطلاقًا لتجنّب DuplicateAssignment.
#     - إن وُجد SSA صالح لنفس الشركة: أعده (وقد نعدّل تاريخه فقط).
#     - إن وُجد SSA صالح لشركة أخرى: استخدم salary_structure منه وأعد (None, struct).
#     - إن لم يوجد أي SSA: خذ fallback structure (من آخر Slip/SSA) وأعد (None, struct).
#     """
#     # 1) هل يوجد SSA صالح لنفس الشركة يغطي start_date؟
#     ssa_name = _safe_get_assigned_ssa(start_date, employee, company)
#     if ssa_name:
#         ssa_doc = frappe.get_doc("Salary Structure Assignment", ssa_name)
#         # لو تاريخه > start_date عدّله محليًا بدون إنشاء جديد
#         if ssa_doc.from_date > start_date:
#             try:
#                 ssa_doc.cancel()
#                 ssa_doc.from_date = start_date
#                 ssa_doc.submit()
#             except Exception:
#                 pass
#         return ssa_doc.name, ssa_doc.salary_structure

#     # 2) لا يوجد لنفس الشركة -> ابحث عن أي SSA فعّال يغطي التاريخ لأي شركة
#     any_active = frappe.get_all(
#         "Salary Structure Assignment",
#         filters={"employee": employee, "docstatus": 1, "from_date": ["<=", start_date]},
#         fields=["name", "company", "salary_structure", "from_date"],
#         order_by="from_date desc",
#         limit=1,
#     )
#     if any_active:
#         cur = any_active[0]
#         # لو لنفس الشركة استخدمه
#         if cur["company"] == company:
#             return cur["name"], cur["salary_structure"]
#         # لشركة أخرى: خذ الهيكل فقط، واترك SSA فارغ
#         return None, cur["salary_structure"]

#     # 3) لا يوجد أي SSA -> خذ fallback structure (من آخر Slip/SSA)
#     struct = _pick_structure_fallback(employee)
#     return (None, struct) if struct else (None, None)

# # def _ensure_ssa_for_period(start_date, employee, company):
# #     """
# #     يضمن وجود SSA صالح للفترة والشركة.
# #     يتعامل مع قيود HRMS (SSA واحد فعّال لكل موظف).
# #     يرجّع (ssa_name, salary_structure) أو (None, None).
# #     """
# #     # 0) هل يوجد SSA صالح لنفس الشركة (<= start_date)؟
# #     ssa_name = _safe_get_assigned_ssa(start_date, employee, company)
# #     if ssa_name:
# #         ssa_doc = frappe.get_doc("Salary Structure Assignment", ssa_name)
# #         if ssa_doc.from_date > start_date:
# #             ssa_doc.cancel()
# #             ssa_doc.from_date = start_date
# #             ssa_doc.submit()
# #         struct = ssa_doc.salary_structure
# #         return ssa_doc.name, struct

# #     # 1) لا يوجد SSA صالح لنفس الشركة -> افحص هل يوجد أي SSA فعّال يغطي start_date (لأي شركة)
# #     any_active = frappe.get_all(
# #         "Salary Structure Assignment",
# #         filters={"employee": employee, "docstatus": 1, "from_date": ["<=", start_date]},
# #         fields=["name", "company", "salary_structure", "from_date"],
# #         order_by="from_date desc",
# #         limit=1,
# #     )
# #     if any_active:
# #         cur = any_active[0]
# #         # لو لشركة أخرى, يجب إلغاءه قبل إنشاء واحد للشركة المطلوبة وإلا سيظهر خطأ "already exists"
# #         if cur["company"] != company:
# #             try:
# #                 old = frappe.get_doc("Salary Structure Assignment", cur["name"])
# #                 old.cancel()
# #             except Exception:
# #                 # لو تعذّر إلغاءه لأي سبب، نتركها لك يدويًا
# #                 return None, None
# #             # سنستخدم نفس الـ structure (أو غيّره بفولباك لاحقًا)
# #             fallback_struct = cur["salary_structure"]
# #         else:
# #             # لنفس الشركة لكن تاريخه > start_date (غطّيناه فوق) أو لا يغطي الفترة
# #             fallback_struct = cur["salary_structure"]
# #     else:
# #         fallback_struct = None

# #     # 2) اختر Salary Structure منطقي
# #     struct = fallback_struct or _pick_structure_fallback(employee)
# #     if not struct:
# #         return None, None

# #     # 3) تحقّق من صلاحية الهيكل
# #     ss = frappe.get_doc("Salary Structure", struct)
# #     if hasattr(ss, "is_active") and not ss.is_active:
# #         return None, None
# #     if hasattr(ss, "payroll_frequency") and ss.payroll_frequency and ss.payroll_frequency != "Monthly":
# #         return None, None

# #     # 4) أنشئ SSA جديد لنفس الشركة وتاريخ الفترة
# #     try:
# #         new_ssa = frappe.new_doc("Salary Structure Assignment")
# #         new_ssa.employee = employee
# #         new_ssa.company = company
# #         new_ssa.salary_structure = struct
# #         new_ssa.from_date = start_date
# #         new_ssa.submit()
# #         return new_ssa.name, struct
# #     except frappe.ValidationError as e:
# #         # في حال ظهر "already exists" بسبب تسابق أو تحقق موازي
# #         if "already exists" in str(e):
# #             # ارجع لأحدث SSA فعّال بعد الإلغاء/الإنشاء
# #             name = _safe_get_assigned_ssa(start_date, employee, company)
# #             if name:
# #                 st = frappe.db.get_value("Salary Structure Assignment", name, "salary_structure")
# #                 return name, st
# #         raise

# ##################################################################################################
# # ================= إعدادات عامة قابلة للتعديل =================
# LATE_GRACE_MINUTES     = 15.0
# WORKING_HOURS_PER_DAY  = 8.0
# BASE_COMPONENTS        = {"راتب أساسي"}
# FALLBACK_SHIFT_START   = time(8, 0)

# # خصم التأخيرات
# DEDUCTION_COMPONENT_NAME = "خصم التاخيرات"
# DEDUCTION_ABBR           = "late_deduction"

# # الوعاء الضريبي
# TAXABLE_NAMES  = {"الوعاء الضريبي"}
# TAXABLE_ABBR   = "amd_taxable"

# # ضريبة يمني (ريال)
# YEMEN_TAX_NAMES = {"الضريبة يمني"}
# YEMEN_TAX_ABBR  = "tax_raiel_amd"

# # ضريبة بالدولار (الصف المسمى "الضريبة")
# USD_TAX_NAMES = {"الضريبة"}
# USD_TAX_ABBR  = "amd_tax_1"

# # غياب USD
# ABSENCE_NAMES  = {"غياب USD"}
# ABSENCE_ABBR   = "ABS_USD"

# # معامل التحويل (حقل مخصص في Salary Slip)
# TAX_EXCHANGE_FIELD = "custom_tax_exchange"

# # البنود التي تدخل في إجمالي الخصومات
# INCLUDE_IN_TOTAL_ABBRS = {"amd_tax_1", "loans", "ABS_USD", "late_deduction"}

# # صفوف خاصة في الخصميات
# TOTAL_DED_ROW_NAMES = {"اجمالي الخصومات", "إجمالي الخصومات"}
# TOTAL_DED_ROW_ABBRS = {"to_reb_amd", "amd_total"}

# NET_PAY_ROW_NAMES  = {"صافي الراتب", "صـافي الــراتب"}
# NET_PAY_ROW_ABBRS  = {"Amd_net_pay", "amd_net_pay"}

# # صف "إجمالي الكلي" في الإيرادات (مصدر الصافي)
# GROSS_ROW_NAMES = {"اجمالي الكلي", "إجمالي الكلي"}
# GROSS_ROW_ABBRS = {"amd_total"}
# # ===============================================================


# class CustomSalarySlip(SalarySlip):

#     # تشغيل الأوفررايد فقط لو مكوّن خصم التأخيرات موجود (أو سطره موجود)
#     def _should_run_override(self) -> bool:
#         if frappe.db.exists("Salary Component", DEDUCTION_COMPONENT_NAME):
#             return True
#         for r in (self.deductions or []):
#             if (r.salary_component or "").strip() == DEDUCTION_COMPONENT_NAME or (r.abbr or "").strip() == DEDUCTION_ABBR:
#                 return True
#         return False

#     # -------- دورة التنفيذ --------
    
#     # def validate(self):
#     #     run = self._should_run_override()

#     #     # 1) احسب خصم التأخيرات قبل معادلات الهيكل
#     #     if run:
           
#     #         # تعبئة جدول الخروج المبكر
#     #         self.populate_early_exit_table()   # <-- الجديد
#     #         self.apply_late_deduction()
            
#     #     # 2) دع HRMS ينفذ معادلات Salary Structure
#     #     super().validate()

#     #     if run:
#     #         # قد يختفي سطر التأخيرات أثناء super().validate()، نعيده
#     #         self._restore_late_row_if_missing()

#     #         # 3) نحسب الوعاء الضريبي ثم الضريبة يمني ثم الضريبة بالدولار (ونثبت السطور)
#     #         self._recompute_taxable_base()
#     #         self._recompute_taxes_yer_and_usd()

#     #         # 4) نجمع الإجماليات ونثبت سطري "الإجمالي" و"الصافي"
#     #         self._recalc_totals_into_existing_rows()
#     #         self._freeze_total_and_net_rows()


#     def validate(self):
#         ##################################################################################################
#         self.set_salary_structure_assignment()
#         # اضمن SSA لو جاي من Payroll Entry (هنا دائمًا HRMS يطلب SSA)
#         try:
#             if getattr(self, "payroll_entry", None):
#                 ssa_name, struct = _ensure_ssa_for_period(self.start_date, self.employee, self.company)
#                 if ssa_name and struct:
#                     try:
#                         self.salary_structure_assignment = ssa_name
#                     except Exception:
#                         pass
#                     self.salary_structure = struct
#         except Exception:
#             # لا توقف الفاليديشن؛ HRMS سيعطي رسالة واضحة لو تعذّر
#             pass
#         ##################################################################################################
        
#         run = self._should_run_override()
#         if run:
#             # امسح الجداول أولاً
#             try:
#                 self.set("custom_late_days", [])
#                 self.set("custom_early_exit", [])
#             except Exception:
#                 pass

#             # --- Late Days ---
#             if getattr(self, "custom_calculate_late_days", 0):
#                 # حساب التأخيرات
#                 self._late_minutes_result = self._late_minutes_by_day(self.employee, self.start_date, self.end_date)
#                 for d, minutes in sorted(self._late_minutes_result.items()):
#                     self.append("custom_late_days", {"date": d, "minutes": minutes})
#             else:
#                 self._late_minutes_result = {}

#             # --- Early Exit ---
#             if getattr(self, "custom_calculate_early_exit", 0):
#                 # حساب الخروج المبكر
#                 self.populate_early_exit_table()
#             else:
#                 self._early_exit_result = {}

#             # --- حساب الخصم (يجمع الاثنين إذا مؤشر عليهم) ---
#             self.apply_late_deduction()

#         # super().validate()
#          # جرّب استدعاء super.validate لكن مع Catch للـ Salary Structure error
#         try:
#             super().validate()
#         except frappe.ValidationError as e:
#             if "Salary Structure Assignment for Employee already exists" in str(e):
#                 # تجاهل الخطأ لأن الـ Assignment موجود أصلاً
#                 frappe.msgprint("Using existing Salary Structure Assignment for this employee.")
#             else:
#                 raise

#         if run:
#             self._restore_late_row_if_missing()
#             self._recompute_taxable_base()
#             self._recompute_taxes_yer_and_usd()
#             self._recalc_totals_into_existing_rows()
#             self._freeze_total_and_net_rows()



#     def before_save(self):
#         if not self._should_run_override():
#             return
#         # ترتيب نهائي قبل الحفظ
#         self._recalc_totals_into_existing_rows()
#         self._freeze_total_and_net_rows()


#         # --- نُعيد تعريف ميثود HRMS التي ترمي الخطأ ---
    
#     def set_salary_structure_assignment(self):
#         """
#         اجلب/أنشئ SSA صالحًا للفترة والشركة واضبط الحقول.
#         لا ترمي خطأ إذا وُجد salary_structure يدويًا (نسمح بالمتابعة).
#         """
#         # 1) جرّب الموجود لنفس الشركة
#         ssa_name = _safe_get_assigned_ssa(self.start_date, self.employee, self.company)
#         struct = None
#         if ssa_name:
#             struct = frappe.db.get_value("Salary Structure Assignment", ssa_name, "salary_structure")

#         # 2) إن لم يوجد، ضمن/أنشئ واحدًا (مع معالجة تضارب "already exists")
#         if not ssa_name:
#             ssa_name, struct = _ensure_ssa_for_period(self.start_date, self.employee, self.company)

#         if ssa_name and struct:
#             self.salary_structure_assignment = ssa_name
#             self.salary_structure = struct
#             return
        
#         # # 3) لو صار معنا SSA صالح، اضبط الحقول وارجع بدون رمي استثناء
#         # if ssa_name and struct:
#         #     try:
#         #         self.salary_structure_assignment = ssa_name
#         #     except Exception:
#         #         pass
#         #     self.salary_structure = struct
#         #     return

#         # 4) إن تعذّر تحديد SSA لكن عندنا salary_structure أصلاً، اسمح بالمتابعة بدون throw
#         if getattr(self, "salary_structure", None):
#             return

#         # 5) آخر حل: نفس رسالة HRMS (لن تصل هنا غالبًا بعد التعديل)
#         frappe.throw(
#             f"Please assign a Salary Structure for Employee <strong>{frappe.utils.get_fullname(self.employee) or self.employee}</strong> "
#             f"applicable from or before <strong>{frappe.utils.format_date(self.start_date, 'dd-mm-yyyy')}</strong> first"
#         )

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

#         # Attendance
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

#         # Employee Checkin (أول دخول في اليوم)
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
#             if (row.salary_component or "").strip() in BASE_COMPONENTS:
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

#     # ====================== خصم التأخيرات ======================
    
#     def apply_late_deduction(self):
#         """
#         يحسب خصم التأخيرات بناءً على:
#         - custom_calculate_late_days  ✅/❌
#         - custom_calculate_early_exit ✅/❌
#         ويحدّث الجداول والحقول والخصم (سطر 'خصم التاخيرات') وفق الاختيار.
#         """
#         calc_late  = 1 if getattr(self, "custom_calculate_late_days", 0) else 0
#         calc_early = 1 if getattr(self, "custom_calculate_early_exit", 0) else 0

#         # ----------------- Late Days -----------------
#         total_late_minutes = 0.0
#         late_days_count = 0

#         try:
#             # نظّف دائمًا قبل إعادة التعبئة
#             self.set("custom_late_days", [])
#         except Exception:
#             pass

#         if calc_late:
#             late_by_day = self._late_minutes_by_day(self.employee, self.start_date, self.end_date)
#             for d in sorted(late_by_day.keys()):
#                 minutes = float(late_by_day[d] or 0)
#                 if minutes <= 0:
#                     continue
#                 late_days_count += 1
#                 total_late_minutes += minutes
#                 try:
#                     self.append("custom_late_days", {"date": d, "minutes": minutes})
#                 except Exception:
#                     pass
#             # حقول تلخيصية اختيارية
#             if hasattr(self, "custom_number_of_late_days"):
#                 self.custom_number_of_late_days = float(late_days_count)
#             if hasattr(self, "custom_total_late_minutes"):
#                 self.custom_total_late_minutes = float(total_late_minutes)
#             if hasattr(self, "custom_total_late_hours"):
#                 self.custom_total_late_hours = round(total_late_minutes / 60.0, 3)
#         else:
#             # مُعطّل -> صفّر الحقول الملخّصة إن وُجدت
#             if hasattr(self, "custom_number_of_late_days"):
#                 self.custom_number_of_late_days = 0.0
#             if hasattr(self, "custom_total_late_minutes"):
#                 self.custom_total_late_minutes = 0.0
#             if hasattr(self, "custom_total_late_hours"):
#                 self.custom_total_late_hours = 0.0

#         # ----------------- Early Exit -----------------
#         total_early_minutes = 0.0

#         try:
#             # نظّف دائمًا قبل إعادة التعبئة
#             self.set("custom_early_exit", [])
#         except Exception:
#             pass

#         if calc_early:
#             early_by_day = self._early_exit_minutes_by_day(self.employee, self.start_date, self.end_date)
#             for d in sorted(early_by_day.keys()):
#                 minutes = float(early_by_day[d] or 0)
#                 if minutes <= 0:
#                     continue
#                 total_early_minutes += minutes
#                 try:
#                     self.append("custom_early_exit", {
#                         "early_exit_date": d,
#                         "early_exit_minutes": minutes,
#                     })
#                 except Exception:
#                     pass
#             # حقول تلخيصية اختيارية
#             if hasattr(self, "custom_total_early_exit_minutes"):
#                 self.custom_total_early_exit_minutes = float(total_early_minutes)
#             if hasattr(self, "custom_total_early_exit_hours"):
#                 self.custom_total_early_exit_hours = round(total_early_minutes / 60.0, 3)
#         else:
#             # مُعطّل -> صفّر الحقول الملخّصة إن وُجدت
#             if hasattr(self, "custom_total_early_exit_minutes"):
#                 self.custom_total_early_exit_minutes = 0.0
#             if hasattr(self, "custom_total_early_exit_hours"):
#                 self.custom_total_early_exit_hours = 0.0

#         # ----------------- المجموع (Late + Early) -----------------
#         total_minutes_for_deduction = total_late_minutes + total_early_minutes

#         if hasattr(self, "custom_total_late_plus_early_minutes"):
#             self.custom_total_late_plus_early_minutes = float(total_minutes_for_deduction)
#         if hasattr(self, "custom_total_late_plus_early_hours"):
#             self.custom_total_late_plus_early_hours = round(total_minutes_for_deduction / 60.0, 3)

#         # ----------------- حساب مبلغ الخصم -----------------
#         base_amount = self._sum_base_components(self.earnings)
#         payment_days = float(self.payment_days or self.total_working_days or 26.0)
#         minutes_in_period = WORKING_HOURS_PER_DAY * 60.0 * payment_days

#         late_deduction = 0.0
#         if base_amount > 0 and minutes_in_period > 0 and total_minutes_for_deduction > 0:
#             late_deduction = base_amount * (total_minutes_for_deduction / minutes_in_period)

#         if hasattr(self, "custom_late_deduction_amount"):
#             self.custom_late_deduction_amount = float(late_deduction or 0)

#         # خزّن/حدّث بند "خصم التاخيرات" (صفر إن كان كلاهما غير مُفعّل)
#         self._late_amount = float(late_deduction or 0)
#         self._upsert_deduction_row(self._late_amount, DEDUCTION_COMPONENT_NAME)

#     def apply_late_deduction_ol(self):
#         # --- تأخير الدخول ---
#         late_by_day = self._late_minutes_by_day(self.employee, self.start_date, self.end_date)

#         # نظّف جدول التأخيرات وأعد تعبئته (كما هو سابقاً)
#         try:
#             self.set("custom_late_days", [])
#         except Exception:
#             pass

#         late_days_count = 0
#         total_late_minutes = 0.0
#         for d in sorted(late_by_day.keys()):
#             minutes = float(late_by_day[d] or 0)
#             if minutes <= 0:
#                 continue
#             late_days_count += 1
#             total_late_minutes += minutes
#             try:
#                 self.append("custom_late_days", {"date": d, "minutes": minutes})
#             except Exception:
#                 pass

#         # --- الخروج المبكر ---
#         early_by_day = self._early_exit_minutes_by_day(self.employee, self.start_date, self.end_date)
#         total_early_minutes = 0.0
#         for d in early_by_day.keys():
#             m = float(early_by_day[d] or 0)
#             if m > 0:
#                 total_early_minutes += m

#         # إجمالي دقائق الخصم = تأخير + خروج مبكر
#         total_minutes_for_deduction = total_late_minutes + total_early_minutes

#         # تحديث الحقول المخصصة (إن وُجدت)
#         if hasattr(self, "custom_number_of_late_days"):
#             self.custom_number_of_late_days = float(late_days_count)

#         if hasattr(self, "custom_total_late_minutes"):
#             self.custom_total_late_minutes = float(total_late_minutes)
#         if hasattr(self, "custom_total_late_hours"):
#             self.custom_total_late_hours = round(total_late_minutes / 60.0, 3)

#         # من populate_early_exit_table تُعبأ هذه تلقائياً، لكن نضبطها هنا لو لم تُنشأ
#         if hasattr(self, "custom_total_early_exit_minutes") and not getattr(self, "custom_total_early_exit_minutes", None):
#             self.custom_total_early_exit_minutes = float(total_early_minutes)
#         if hasattr(self, "custom_total_early_exit_hours") and not getattr(self, "custom_total_early_exit_hours", None):
#             self.custom_total_early_exit_hours = round(total_early_minutes / 60.0, 3)

#         # لو تحب حقلًا ملخّصًا للمجموع:
#         if hasattr(self, "custom_total_late_plus_early_minutes"):
#             self.custom_total_late_plus_early_minutes = float(total_minutes_for_deduction)
#         if hasattr(self, "custom_total_late_plus_early_hours"):
#             self.custom_total_late_plus_early_hours = round(total_minutes_for_deduction / 60.0, 3)

#         # --- حساب مبلغ الخصم ---
#         base_amount = self._sum_base_components(self.earnings)
#         payment_days = float(self.payment_days or self.total_working_days or 26.0)
#         minutes_in_period = WORKING_HOURS_PER_DAY * 60.0 * payment_days

#         late_deduction = 0.0
#         if base_amount > 0 and minutes_in_period > 0 and total_minutes_for_deduction > 0:
#             late_deduction = base_amount * (total_minutes_for_deduction / minutes_in_period)

#         if hasattr(self, "custom_late_deduction_amount"):
#             self.custom_late_deduction_amount = float(late_deduction or 0)

#         # خزّن لاستخدامه بعد validate وأضف/حدّث البند
#         self._late_amount = float(late_deduction or 0)
#         self._upsert_deduction_row(late_deduction, DEDUCTION_COMPONENT_NAME)


#     def _restore_late_row_if_missing(self):
#         amt = float(getattr(self, "_late_amount", 0.0))
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
#                 return
#         # غير موجود -> أضفه
#         self.append("deductions", {
#             "salary_component": DEDUCTION_COMPONENT_NAME,
#             "abbr": DEDUCTION_ABBR,
#             "amount": amt,
#             "do_not_include_in_total": 0,
#         })

#     # =================== التعرف على السطور الخاصة ===================
#     def _match_row(self, row, names:set[str], abbrs:set[str]) -> bool:
#         name = (row.salary_component or "").strip()
#         abbr = (row.abbr or "").strip()
#         return (name in names) or (abbr in abbrs)

#     def _is_total_row(self, row) -> bool:
#         name = (row.salary_component or "") or ""
#         return self._match_row(row, TOTAL_DED_ROW_NAMES, TOTAL_DED_ROW_ABBRS) or ("إجمالي" in name and "خصومات" in name)

#     def _is_net_row(self, row) -> bool:
#         name = (row.salary_component or "").strip()
#         abbr = (row.abbr or "").strip().lower()
#         return (name in NET_PAY_ROW_NAMES) or (abbr in {a.lower() for a in NET_PAY_ROW_ABBRS}) or ("صافي" in name) or ("net" in abbr and "pay" in abbr)

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

#     # ==================== الوعاء + الضريبة يمني + الضريبة USD ====================
#     def _recompute_taxable_base(self):
#         # راتب أساسي (قد يكون أكثر من صف)
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
#         if taxable_val < 0:
#             taxable_val = 0.0

#         for row in (self.deductions or []):
#             if self._match_row(row, TAXABLE_NAMES, {TAXABLE_ABBR}):
#                 row.amount = float(taxable_val or 0)
#                 try:
#                     row.amount_based_on_formula = 0   # تثبيت
#                     row.do_not_include_in_total = 1   # لا يدخل في الإجمالي
#                 except Exception:
#                     pass
#                 break

#     def _recompute_taxes_yer_and_usd(self):
#         # اجلب الوعاء الضريبي الذي ثبتناه للتو
#         taxable_val = self._get_amount_any(TAXABLE_NAMES, {TAXABLE_ABBR})

#         # معادلة الصورة: ((amd_taxable - 20000) * 0.15 + 1000) إذا كان هناك وعاء
#         # نحمي من السالب
#         base_over = max(0.0, taxable_val - 20000.0)
#         yer_tax = 0.0
#         if taxable_val > 0:
#             yer_tax = base_over * 0.15 + 1000.0

#         # عيّن الضريبة يمني (tax_raiel_amd) وثبتها
#         for row in (self.deductions or []):
#             if self._match_row(row, YEMEN_TAX_NAMES, {YEMEN_TAX_ABBR}):
#                 row.amount = float(yer_tax or 0)
#                 try:
#                     row.amount_based_on_formula = 0   # تثبيت هذا السطر
#                     row.do_not_include_in_total = 1   # عادة لا يدخل في الإجمالي (الإجمالي بالدولار)
#                 except Exception:
#                     pass
#                 break

#         # الضريبة بالدولار = tax_raiel_amd / custom_tax_exchange
#         try:
#             exchange = float(getattr(self, TAX_EXCHANGE_FIELD))
#         except Exception:
#             exchange = 1.0
#         usd_tax = (yer_tax / exchange) if exchange else 0.0

#         for row in (self.deductions or []):
#             if self._match_row(row, USD_TAX_NAMES, {USD_TAX_ABBR}):
#                 row.amount = float(usd_tax or 0)
#                 try:
#                     row.amount_based_on_formula = 0  # تثبيت
#                     # هذه تدخل في إجمالي الخصومات حسب INCLUDE_IN_TOTAL_ABBRS
#                     row.do_not_include_in_total = 0
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


#     # ====== (2) أضف هذه الأدوات لمعلومة نهاية الشفت ======
#     def _get_shift_end_time(self, employee, the_date: date) -> time:
#         """يُرجع end_time من الشفت، وإن لم نجد نستخدم start_time + WORKING_HOURS_PER_DAY."""
#         rec = frappe.db.sql(
#             """
#             SELECT st.start_time, st.end_time
#             FROM `tabShift Assignment` sa
#             JOIN `tabShift Type` st ON st.name = sa.shift_type
#             WHERE sa.employee = %s
#             AND sa.start_date <= %s
#             AND (sa.end_date IS NULL OR sa.end_date >= %s)
#             ORDER BY sa.start_date DESC
#             LIMIT 1
#             """,
#             (employee, the_date, the_date),
#             as_dict=True,
#         )

#         def coerce_t(val):
#             if isinstance(val, time):
#                 return val
#             if isinstance(val, timedelta):
#                 base = datetime.min + val
#                 return time(base.hour, base.minute, base.second)
#             return None

#         if rec:
#             st = coerce_t(rec[0].get("start_time")) or FALLBACK_SHIFT_START
#             et = coerce_t(rec[0].get("end_time"))
#             if et:
#                 return et
#             # لا يوجد end_time -> احسبه من start + WORKING_HOURS_PER_DAY
#             dt = (datetime.combine(the_date, st) + timedelta(hours=WORKING_HOURS_PER_DAY))
#             return time(dt.hour, dt.minute, dt.second)

#         # لا يوجد شفت -> fallback
#         dt = (datetime.combine(the_date, FALLBACK_SHIFT_START) + timedelta(hours=WORKING_HOURS_PER_DAY))
#         return time(dt.hour, dt.minute, dt.second)

    
#     # ====== (3) اجمع دقائق الخروج المبكر لكل يوم ======
#     def _early_exit_minutes_by_day(self, employee, start_date, end_date):
#         early_by_day = {}

#         # 3.1 من Attendance (الخيار المفضل إن وُجد out_time)
#         atts = frappe.get_all(
#             "Attendance",
#             filters={"employee": employee, "attendance_date": ["between", [start_date, end_date]], "docstatus": 1},
#             fields=["attendance_date", "status", "out_time"],
#             order_by="attendance_date asc",
#         )
#         for a in (atts or []):
#             d = a.get("attendance_date")
#             if a.get("status") not in ("Present", "Work From Home", "On Duty"):
#                 continue
#             out_time_val = a.get("out_time")
#             if not out_time_val:
#                 continue
#             out_dt = get_datetime(out_time_val)
#             end_t = self._get_shift_end_time(employee, d)
#             shift_end_dt = datetime.combine(d, end_t)
#             # دقائق الخروج المبكر = نهاية الشفت - وقت الخروج (إن كان موجب)
#             minutes = (shift_end_dt - out_dt).total_seconds() / 60.0
#             if minutes > 0:
#                 early_by_day[d] = minutes

#         # 3.2 من Employee Checkin (آخر OUT في اليوم، أو آخر حركة عند عدم وجود OUT)
#         checkins = frappe.get_all(
#             "Employee Checkin",
#             filters={
#                 "employee": employee,
#                 "time": ["between", [f"{start_date} 00:00:00", f"{end_date} 23:59:59"]],
#                 "docstatus": 1,
#             },
#             fields=["time", "log_type"],
#             order_by="time asc",
#         )

#         last_by_day = {}
#         for c in (checkins or []):
#             dt = get_datetime(c.get("time"))
#             d = dt.date()
#             lt = (c.get("log_type") or "").upper().strip()
#             # نفضّل OUT، وإن لم يكن نحفظ آخر حدث في اليوم
#             if d not in last_by_day:
#                 last_by_day[d] = {"last": dt, "last_out": None}
#             last_by_day[d]["last"] = dt
#             if lt == "OUT":
#                 last_by_day[d]["last_out"] = dt

#         for d, info in last_by_day.items():
#             if d in early_by_day:
#                 continue  # لدينا من الحضور
#             last_out = info.get("last_out") or info.get("last")
#             if not last_out:
#                 continue
#             end_t = self._get_shift_end_time(employee, d)
#             shift_end_dt = datetime.combine(d, end_t)
#             minutes = (shift_end_dt - last_out).total_seconds() / 60.0
#             if minutes > 0:
#                 early_by_day[d] = minutes

#         return early_by_day

#     # ====== (4) تعبئة جدول الخروج المبكر في السليب ======
#     def populate_early_exit_table(self):
#         """
#         يملأ child table: custom_early_exit
#         - field early_exit_date
#         - field early_exit_minutes
#         لا يحسب أي خصومات الآن (فقط تعبئة الجدول).
#         """
#         # امسح القديم
#         try:
#             self.set("custom_early_exit", [])
#         except Exception:
#             pass

#         by_day = self._early_exit_minutes_by_day(self.employee, self.start_date, self.end_date)

#         total_early = 0.0
#         for d in sorted(by_day.keys()):
#             minutes = float(by_day[d] or 0)
#             if minutes <= 0:
#                 continue
#             total_early += minutes
#             try:
#                 self.append("custom_early_exit", {
#                     "early_exit_date": d,
#                     "early_exit_minutes": minutes,
#                 })
#             except Exception:
#                 pass

#         # إن وُجدت حقول إجمالي مخصصة، عبّئها (اختياري)
#         if hasattr(self, "custom_total_early_exit_minutes"):
#             self.custom_total_early_exit_minutes = float(total_early)
#         if hasattr(self, "custom_total_early_exit_hours"):
#             self.custom_total_early_exit_hours = round(total_early / 60.0, 3)

# #---------------------------------------------------from heeerrrr--------------------
# # apps/tfd_projectmanagement/tfd_projectmanagement/overrides/salary_slip_override.py
# import frappe
# from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip
# from frappe.utils import get_datetime, format_date
# from datetime import datetime, date, time, timedelta


# ##################################################################################################
# # أدوات مساعدة للعثور على SSA أو اختيار Salary Structure مناسب بدون إنشاء SSA جديد
# ##################################################################################################
# def _safe_get_assigned_ssa(start_date, employee, company):
#     """يحاول استدعاء الدالة الرسمية مع تواقيع متعددة عبر إصدارات HRMS.
#     وإن فشل، يرجع آخر SSA صالح (<= start_date) لنفس الشركة.
#     """
#     try:
#         from hrms.payroll.doctype.salary_structure_assignment.salary_structure_assignment import (
#             get_assigned_salary_structure,
#         )
#         try:
#             return get_assigned_salary_structure(start_date, employee, company)
#         except TypeError:
#             try:
#                 return get_assigned_salary_structure(start_date, employee)
#             except TypeError:
#                 return get_assigned_salary_structure(employee, start_date)
#     except Exception:
#         pass

#     return frappe.db.get_value(
#         "Salary Structure Assignment",
#         {
#             "employee": employee,
#             "company": company,
#             "docstatus": 1,
#             "from_date": ["<=", start_date],
#         },
#         "name",
#         order_by="from_date desc",
#     )


# def _pick_structure_fallback(employee):
#     """اختر Salary Structure منطقي عند عدم توفر SSA صالح."""
#     # آخر Salary Slip سابق
#     slip = frappe.db.get_value(
#         "Salary Slip",
#         {"employee": employee, "docstatus": 1},
#         ["salary_structure"],
#         order_by="start_date desc",
#         as_dict=True,
#     )
#     if slip and slip.get("salary_structure"):
#         return slip["salary_structure"]

#     # آخر SSA لأي شركة
#     any_ssa = frappe.db.get_value(
#         "Salary Structure Assignment",
#         {"employee": employee, "docstatus": 1},
#         ["salary_structure"],
#         order_by="from_date desc",
#         as_dict=True,
#     )
#     if any_ssa and any_ssa.get("salary_structure"):
#         return any_ssa["salary_structure"]

#     # ضع اسم هيكل افتراضي إن رغبت، وإلا ارجع None
#     return None


# def _ensure_ssa_for_period(start_date, employee, company):
#     """لا ينشئ SSA جديدًا إطلاقًا لتجنب DuplicateAssignment.
#     يرجع (ssa_name, salary_structure) وفق المتاح:
#     - SSA صالح لنفس الشركة (وقد نعدل تاريخه للأسفل إن لزم)
#     - أو SSA صالح لشركة أخرى: نأخذ salary_structure فقط
#     - أو fallback structure من آخر Slip/SSA
#     """
#     # 1) SSA صالح لنفس الشركة
#     ssa_name = _safe_get_assigned_ssa(start_date, employee, company)
#     if ssa_name:
#         ssa_doc = frappe.get_doc("Salary Structure Assignment", ssa_name)
#         if ssa_doc.from_date > start_date:
#             # حاول جعل SSA يبدأ من تاريخ الفترة (إن فشل لا نوقف)
#             try:
#                 ssa_doc.cancel()
#                 ssa_doc.from_date = start_date
#                 ssa_doc.submit()
#             except Exception:
#                 pass
#         return ssa_doc.name, ssa_doc.salary_structure

#     # 2) SSA فعّال لأي شركة (نأخذ منه الـ structure فقط إن كان لشركة أخرى)
#     any_active = frappe.get_all(
#         "Salary Structure Assignment",
#         filters={"employee": employee, "docstatus": 1, "from_date": ["<=", start_date]},
#         fields=["name", "company", "salary_structure", "from_date"],
#         order_by="from_date desc",
#         limit=1,
#     )
#     if any_active:
#         cur = any_active[0]
#         if cur["company"] == company:
#             return cur["name"], cur["salary_structure"]
#         return None, cur["salary_structure"]

#     # 3) لا شيء -> fallback
#     struct = _pick_structure_fallback(employee)
#     return (None, struct) if struct else (None, None)


# def _load_ssa_min_dict(ssa_name: str) -> dict:
#     """ديكت بسيط لـ self._salary_structure_assignment.
#     يقرأ فقط الحقول الموجودة فعلاً في SSA (تفادي Unknown column) ويملأ الباقي بـ None.
#     """
#     if not ssa_name:
#         return {}

#     # الحقول المرغوبة نظريًا (بعضها قد لا يكون موجودًا في SSA في نسخ معينة)
#     desired_fields = ["base", "variable", "payroll_frequency", "from_date", "name"]

#     # خذ فقط الحقول الموجودة فعلاً في هذا الـ DocType
#     try:
#         meta = frappe.get_meta("Salary Structure Assignment")
#         existing = []
#         for f in desired_fields:
#             # في بعض النسخ الحقل "name" ليس في meta.fields لكنه دائمًا موجود كـ PK
#             if f == "name" or meta.has_field(f):
#                 existing.append(f)
#     except Exception:
#         # لو فشل جلب الميتاداتا، خذ الأقل أمانًا
#         existing = ["base", "variable", "from_date", "name"]

#     vals = frappe.db.get_value(
#         "Salary Structure Assignment",
#         ssa_name,
#         existing,
#         as_dict=True,
#     ) or {}

#     # أضف المفاتيح الناقصة بقيمة None حتى لا تتفاجأ كودات داخل HRMS
#     for f in desired_fields:
#         vals.setdefault(f, None)

#     return vals



# ##################################################################################################
# # ================= إعدادات عامة قابلة للتعديل =================
# LATE_GRACE_MINUTES     = 15.0
# WORKING_HOURS_PER_DAY  = 8.0
# BASE_COMPONENTS        = {"راتب أساسي"}
# FALLBACK_SHIFT_START   = time(8, 0)

# # خصم التأخيرات
# DEDUCTION_COMPONENT_NAME = "خصم التاخيرات"
# DEDUCTION_ABBR           = "late_deduction"

# # الوعاء الضريبي
# TAXABLE_NAMES  = {"الوعاء الضريبي"}
# TAXABLE_ABBR   = "amd_taxable"

# # ضريبة يمني (ريال)
# YEMEN_TAX_NAMES = {"الضريبة يمني"}
# YEMEN_TAX_ABBR  = "tax_raiel_amd"

# # ضريبة بالدولار (صف باسم "الضريبة")
# USD_TAX_NAMES = {"الضريبة"}
# USD_TAX_ABBR  = "amd_tax_1"

# # غياب USD
# ABSENCE_NAMES  = {"غياب USD"}
# ABSENCE_ABBR   = "ABS_USD"

# # معامل التحويل (حقل مخصص في Salary Slip)
# TAX_EXCHANGE_FIELD = "custom_tax_exchange"

# # البنود التي تدخل في إجمالي الخصومات
# INCLUDE_IN_TOTAL_ABBRS = {"amd_tax_1", "loans", "ABS_USD", "late_deduction"}

# # صفوف خاصة في الخصميات
# TOTAL_DED_ROW_NAMES = {"اجمالي الخصومات", "إجمالي الخصومات"}
# TOTAL_DED_ROW_ABBRS = {"to_reb_amd", "amd_total"}

# NET_PAY_ROW_NAMES  = {"صافي الراتب", "صـافي الــراتب"}
# NET_PAY_ROW_ABBRS  = {"Amd_net_pay", "amd_net_pay"}

# # صف "إجمالي الكلي" في الإيرادات (مصدر الصافي)
# GROSS_ROW_NAMES = {"اجمالي الكلي", "إجمالي الكلي"}
# GROSS_ROW_ABBRS = {"amd_total"}
# # ===============================================================


# class CustomSalarySlip(SalarySlip):

#     # تشغيل الأوفررايد فقط لو مكوّن خصم التأخيرات موجود (أو سطره موجود)
#     def _should_run_override(self) -> bool:
#         if frappe.db.exists("Salary Component", DEDUCTION_COMPONENT_NAME):
#             return True
#         for r in (self.deductions or []):
#             if (r.salary_component or "").strip() == DEDUCTION_COMPONENT_NAME or (r.abbr or "").strip() == DEDUCTION_ABBR:
#                 return True
#         return False

#     # ---------------------------------------------------------------------------------------------
#     # 1) إعداد SSA/Structure بشكل آمن قبل مناداة super().validate()
#     # 2) حساب التأخيرات/الخروج المبكر
#     # 3) استدعاء HRMS ثم تثبيت الإجماليات
#     # ---------------------------------------------------------------------------------------------
#     def validate(self):
#         # اجلب SSA/Structure بدون إنشاء SSA جديد
#         ssa_name, struct = _ensure_ssa_for_period(self.start_date, self.employee, self.company)

#         # اضبط الحقول المتاحة
#         if struct:
#             self.salary_structure = struct
#         if ssa_name:
#             self.salary_structure_assignment = ssa_name

#         # جهّز دائمًا الديكت الداخلي الذي يحتاجه HRMS (حتى لو بدون SSA)
#         if not hasattr(self, "_salary_structure_assignment") or self._salary_structure_assignment is None:
#             self._salary_structure_assignment = _load_ssa_min_dict(ssa_name)

#         run = self._should_run_override()
#         if run:
#             # نظّف الجداول
#             try:
#                 self.set("custom_late_days", [])
#                 self.set("custom_early_exit", [])
#             except Exception:
#                 pass

#             # Late Days
#             if getattr(self, "custom_calculate_late_days", 0):
#                 self._late_minutes_result = self._late_minutes_by_day(self.employee, self.start_date, self.end_date)
#                 for d, minutes in sorted(self._late_minutes_result.items()):
#                     self.append("custom_late_days", {"date": d, "minutes": minutes})
#             else:
#                 self._late_minutes_result = {}

#             # Early Exit
#             if getattr(self, "custom_calculate_early_exit", 0):
#                 self.populate_early_exit_table()
#             else:
#                 self._early_exit_result = {}

#             # إجمالي الخصم من الاثنين
#             self.apply_late_deduction()

#         # استدعِ HRMS. لو رمى خطأ "existing SSA" نتجاوزه، والباقي نعيد رميه
#         try:
#             super().validate()
#         except frappe.ValidationError as e:
#             msg = str(e)
#             if "Salary Structure Assignment for Employee already exists" in msg:
#                 frappe.msgprint("Using existing Salary Structure Assignment for this employee.")
#             elif "Please assign a Salary Structure" in msg and getattr(self, "salary_structure", None):
#                 # عندنا هيكل بدون SSA: أكمل (الديكت الداخلي موجود)
#                 pass
#             else:
#                 raise

#         if run:
#             self._restore_late_row_if_missing()
#             self._recompute_taxable_base()
#             self._recompute_taxes_yer_and_usd()
#             self._recalc_totals_into_existing_rows()
#             self._freeze_total_and_net_rows()

#     def before_save(self):
#         if not self._should_run_override():
#             return
#         self._recalc_totals_into_existing_rows()
#         self._freeze_total_and_net_rows()



#     def _auto_enable_calc_flags(self):
#         """فعّل حساب التأخيرات/الخروج المبكر تلقائياً عند الإنشاء من Payroll Entry
#         أو عندما تكون الحقول غير معيّنة/0.
#         """
#         pe_mode = bool(getattr(self, "payroll_entry", None))

#         # لو الفلاغ غير موجود أو قيمته 0 وفاتحة من Payroll Entry -> فعّله
#         if pe_mode or getattr(self, "custom_calculate_late_days", None) in (None, 0, "0"):
#             try:
#                 self.custom_calculate_late_days = 1
#             except Exception:
#                 pass

#         if pe_mode or getattr(self, "custom_calculate_early_exit", None) in (None, 0, "0"):
#             try:
#                 self.custom_calculate_early_exit = 1
#             except Exception:
#                 pass
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

#         # Attendance
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

#         # Employee Checkin (أول دخول)
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
#             if (row.salary_component or "").strip() in BASE_COMPONENTS:
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

#     # ====================== خصم التأخيرات ======================
#     def apply_late_deduction(self):
#         """يجمع تأخير الدخول + الخروج المبكر (حسب الفلاجز) ويحسب مبلغ الخصم."""
#         calc_late  = 1 if getattr(self, "custom_calculate_late_days", 0) else 0
#         calc_early = 1 if getattr(self, "custom_calculate_early_exit", 0) else 0

#         # Late
#         total_late_minutes = 0.0
#         late_days_count = 0
#         try:
#             self.set("custom_late_days", [])
#         except Exception:
#             pass

#         if calc_late:
#             late_by_day = self._late_minutes_by_day(self.employee, self.start_date, self.end_date)
#             for d in sorted(late_by_day.keys()):
#                 minutes = float(late_by_day[d] or 0)
#                 if minutes <= 0:
#                     continue
#                 late_days_count += 1
#                 total_late_minutes += minutes
#                 try:
#                     self.append("custom_late_days", {"date": d, "minutes": minutes})
#                 except Exception:
#                     pass
#             if hasattr(self, "custom_number_of_late_days"):
#                 self.custom_number_of_late_days = float(late_days_count)
#             if hasattr(self, "custom_total_late_minutes"):
#                 self.custom_total_late_minutes = float(total_late_minutes)
#             if hasattr(self, "custom_total_late_hours"):
#                 self.custom_total_late_hours = round(total_late_minutes / 60.0, 3)
#         else:
#             if hasattr(self, "custom_number_of_late_days"):
#                 self.custom_number_of_late_days = 0.0
#             if hasattr(self, "custom_total_late_minutes"):
#                 self.custom_total_late_minutes = 0.0
#             if hasattr(self, "custom_total_late_hours"):
#                 self.custom_total_late_hours = 0.0

#         # Early Exit
#         total_early_minutes = 0.0
#         try:
#             self.set("custom_early_exit", [])
#         except Exception:
#             pass

#         if calc_early:
#             early_by_day = self._early_exit_minutes_by_day(self.employee, self.start_date, self.end_date)
#             for d in sorted(early_by_day.keys()):
#                 minutes = float(early_by_day[d] or 0)
#                 if minutes <= 0:
#                     continue
#                 total_early_minutes += minutes
#                 try:
#                     self.append("custom_early_exit", {
#                         "early_exit_date": d,
#                         "early_exit_minutes": minutes,
#                     })
#                 except Exception:
#                     pass
#             if hasattr(self, "custom_total_early_exit_minutes"):
#                 self.custom_total_early_exit_minutes = float(total_early_minutes)
#             if hasattr(self, "custom_total_early_exit_hours"):
#                 self.custom_total_early_exit_hours = round(total_early_minutes / 60.0, 3)
#         else:
#             if hasattr(self, "custom_total_early_exit_minutes"):
#                 self.custom_total_early_exit_minutes = 0.0
#             if hasattr(self, "custom_total_early_exit_hours"):
#                 self.custom_total_early_exit_hours = 0.0

#         # المجموع والخصم
#         total_minutes_for_deduction = total_late_minutes + total_early_minutes
#         if hasattr(self, "custom_total_late_plus_early_minutes"):
#             self.custom_total_late_plus_early_minutes = float(total_minutes_for_deduction)
#         if hasattr(self, "custom_total_late_plus_early_hours"):
#             self.custom_total_late_plus_early_hours = round(total_minutes_for_deduction / 60.0, 3)

#         base_amount = self._sum_base_components(self.earnings)
#         payment_days = float(self.payment_days or self.total_working_days or 26.0)
#         minutes_in_period = WORKING_HOURS_PER_DAY * 60.0 * payment_days

#         late_deduction = 0.0
#         if base_amount > 0 and minutes_in_period > 0 and total_minutes_for_deduction > 0:
#             late_deduction = base_amount * (total_minutes_for_deduction / minutes_in_period)

#         if hasattr(self, "custom_late_deduction_amount"):
#             self.custom_late_deduction_amount = float(late_deduction or 0)

#         self._late_amount = float(late_deduction or 0)
#         self._upsert_deduction_row(self._late_amount, DEDUCTION_COMPONENT_NAME)

#     def apply_late_deduction_ol(self):
#         # نسخة أقدم، أبقيناها كما هي لمن يحتاجها
#         late_by_day = self._late_minutes_by_day(self.employee, self.start_date, self.end_date)
#         try:
#             self.set("custom_late_days", [])
#         except Exception:
#             pass

#         late_days_count = 0
#         total_late_minutes = 0.0
#         for d in sorted(late_by_day.keys()):
#             minutes = float(late_by_day[d] or 0)
#             if minutes <= 0:
#                 continue
#             late_days_count += 1
#             total_late_minutes += minutes
#             try:
#                 self.append("custom_late_days", {"date": d, "minutes": minutes})
#             except Exception:
#                 pass

#         early_by_day = self._early_exit_minutes_by_day(self.employee, self.start_date, self.end_date)
#         total_early_minutes = 0.0
#         for d in early_by_day.keys():
#             m = float(early_by_day[d] or 0)
#             if m > 0:
#                 total_early_minutes += m

#         total_minutes_for_deduction = total_late_minutes + total_early_minutes

#         if hasattr(self, "custom_number_of_late_days"):
#             self.custom_number_of_late_days = float(late_days_count)
#         if hasattr(self, "custom_total_late_minutes"):
#             self.custom_total_late_minutes = float(total_late_minutes)
#         if hasattr(self, "custom_total_late_hours"):
#             self.custom_total_late_hours = round(total_late_minutes / 60.0, 3)

#         if hasattr(self, "custom_total_early_exit_minutes") and not getattr(self, "custom_total_early_exit_minutes", None):
#             self.custom_total_early_exit_minutes = float(total_early_minutes)
#         if hasattr(self, "custom_total_early_exit_hours") and not getattr(self, "custom_total_early_exit_hours", None):
#             self.custom_total_early_exit_hours = round(total_early_minutes / 60.0, 3)

#         if hasattr(self, "custom_total_late_plus_early_minutes"):
#             self.custom_total_late_plus_early_minutes = float(total_minutes_for_deduction)
#         if hasattr(self, "custom_total_late_plus_early_hours"):
#             self.custom_total_late_plus_early_hours = round(total_minutes_for_deduction / 60.0, 3)

#         base_amount = self._sum_base_components(self.earnings)
#         payment_days = float(self.payment_days or self.total_working_days or 26.0)
#         minutes_in_period = WORKING_HOURS_PER_DAY * 60.0 * payment_days

#         late_deduction = 0.0
#         if base_amount > 0 and minutes_in_period > 0 and total_minutes_for_deduction > 0:
#             late_deduction = base_amount * (total_minutes_for_deduction / minutes_in_period)

#         if hasattr(self, "custom_late_deduction_amount"):
#             self.custom_late_deduction_amount = float(late_deduction or 0)

#         self._late_amount = float(late_deduction or 0)
#         self._upsert_deduction_row(late_deduction, DEDUCTION_COMPONENT_NAME)

#     def _restore_late_row_if_missing(self):
#         amt = float(getattr(self, "_late_amount", 0.0))
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
#                 return
#         self.append("deductions", {
#             "salary_component": DEDUCTION_COMPONENT_NAME,
#             "abbr": DEDUCTION_ABBR,
#             "amount": amt,
#             "do_not_include_in_total": 0,
#         })

#     # =================== التعرف على السطور الخاصة ===================
#     def _match_row(self, row, names:set[str], abbrs:set[str]) -> bool:
#         name = (row.salary_component or "").strip()
#         abbr = (row.abbr or "").strip()
#         return (name in names) or (abbr in abbrs)

#     def _is_total_row(self, row) -> bool:
#         name = (row.salary_component or "") or ""
#         return self._match_row(row, TOTAL_DED_ROW_NAMES, TOTAL_DED_ROW_ABBRS) or ("إجمالي" in name and "خصومات" in name)

#     def _is_net_row(self, row) -> bool:
#         name = (row.salary_component or "").strip()
#         abbr = (row.abbr or "").strip().lower()
#         return (name in NET_PAY_ROW_NAMES) or (abbr in {a.lower() for a in NET_PAY_ROW_ABBRS}) or ("صافي" in name) or ("net" in abbr and "pay" in abbr)

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

#     # ==================== الوعاء + الضريبة يمني + الضريبة USD ====================
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
#         if taxable_val < 0:
#             taxable_val = 0.0

#         for row in (self.deductions or []):
#             if self._match_row(row, TAXABLE_NAMES, {TAXABLE_ABBR}):
#                 row.amount = float(taxable_val or 0)
#                 try:
#                     row.amount_based_on_formula = 0
#                     row.do_not_include_in_total = 1
#                 except Exception:
#                     pass
#                 break

#     def _recompute_taxes_yer_and_usd(self):
#         taxable_val = self._get_amount_any(TAXABLE_NAMES, {TAXABLE_ABBR})

#         base_over = max(0.0, taxable_val - 20000.0)
#         yer_tax = 0.0
#         if taxable_val > 0:
#             yer_tax = base_over * 0.15 + 1000.0

#         for row in (self.deductions or []):
#             if self._match_row(row, YEMEN_TAX_NAMES, {YEMEN_TAX_ABBR}):
#                 row.amount = float(yer_tax or 0)
#                 try:
#                     row.amount_based_on_formula = 0
#                     row.do_not_include_in_total = 1
#                 except Exception:
#                     pass
#                 break

#         try:
#             exchange = float(getattr(self, TAX_EXCHANGE_FIELD))
#         except Exception:
#             exchange = 1.0
#         usd_tax = (yer_tax / exchange) if exchange else 0.0

#         for row in (self.deductions or []):
#             if self._match_row(row, USD_TAX_NAMES, {USD_TAX_ABBR}):
#                 row.amount = float(usd_tax or 0)
#                 try:
#                     row.amount_based_on_formula = 0
#                     row.do_not_include_in_total = 0
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

#     # ====== نهاية الشفت ======
#     def _get_shift_end_time(self, employee, the_date: date) -> time:
#         """end_time من الشفت، وإن لم نجد نستخدم start + WORKING_HOURS_PER_DAY."""
#         rec = frappe.db.sql(
#             """
#             SELECT st.start_time, st.end_time
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

#         def coerce_t(val):
#             if isinstance(val, time):
#                 return val
#             if isinstance(val, timedelta):
#                 base = datetime.min + val
#                 return time(base.hour, base.minute, base.second)
#             return None

#         if rec:
#             st = coerce_t(rec[0].get("start_time")) or FALLBACK_SHIFT_START
#             et = coerce_t(rec[0].get("end_time"))
#             if et:
#                 return et
#             dt = (datetime.combine(the_date, st) + timedelta(hours=WORKING_HOURS_PER_DAY))
#             return time(dt.hour, dt.minute, dt.second)

#         dt = (datetime.combine(the_date, FALLBACK_SHIFT_START) + timedelta(hours=WORKING_HOURS_PER_DAY))
#         return time(dt.hour, dt.minute, dt.second)

#     # ====== دقائق الخروج المبكر ======
#     def _early_exit_minutes_by_day(self, employee, start_date, end_date):
#         early_by_day = {}

#         # من Attendance (إن وُجد out_time)
#         atts = frappe.get_all(
#             "Attendance",
#             filters={"employee": employee, "attendance_date": ["between", [start_date, end_date]], "docstatus": 1},
#             fields=["attendance_date", "status", "out_time"],
#             order_by="attendance_date asc",
#         )
#         for a in (atts or []):
#             d = a.get("attendance_date")
#             if a.get("status") not in ("Present", "Work From Home", "On Duty"):
#                 continue
#             out_time_val = a.get("out_time")
#             if not out_time_val:
#                 continue
#             out_dt = get_datetime(out_time_val)
#             end_t = self._get_shift_end_time(employee, d)
#             shift_end_dt = datetime.combine(d, end_t)
#             minutes = (shift_end_dt - out_dt).total_seconds() / 60.0
#             if minutes > 0:
#                 early_by_day[d] = minutes

#         # من Employee Checkin (آخر OUT أو آخر سجل)
#         checkins = frappe.get_all(
#             "Employee Checkin",
#             filters={
#                 "employee": employee,
#                 "time": ["between", [f"{start_date} 00:00:00", f"{end_date} 23:59:59"]],
#                 "docstatus": 1,
#             },
#             fields=["time", "log_type"],
#             order_by="time asc",
#         )

#         last_by_day = {}
#         for c in (checkins or []):
#             dt = get_datetime(c.get("time"))
#             d = dt.date()
#             lt = (c.get("log_type") or "").upper().strip()
#             if d not in last_by_day:
#                 last_by_day[d] = {"last": dt, "last_out": None}
#             last_by_day[d]["last"] = dt
#             if lt == "OUT":
#                 last_by_day[d]["last_out"] = dt

#         for d, info in last_by_day.items():
#             if d in early_by_day:
#                 continue
#             last_out = info.get("last_out") or info.get("last")
#             if not last_out:
#                 continue
#             end_t = self._get_shift_end_time(employee, d)
#             shift_end_dt = datetime.combine(d, end_t)
#             minutes = (shift_end_dt - last_out).total_seconds() / 60.0
#             if minutes > 0:
#                 early_by_day[d] = minutes

#         return early_by_day

#     # ====== تعبئة جدول الخروج المبكر ======
#     def populate_early_exit_table(self):
#         try:
#             self.set("custom_early_exit", [])
#         except Exception:
#             pass

#         by_day = self._early_exit_minutes_by_day(self.employee, self.start_date, self.end_date)

#         total_early = 0.0
#         for d in sorted(by_day.keys()):
#             minutes = float(by_day[d] or 0)
#             if minutes <= 0:
#                 continue
#             total_early += minutes
#             try:
#                 self.append("custom_early_exit", {
#                     "early_exit_date": d,
#                     "early_exit_minutes": minutes,
#                 })
#             except Exception:
#                 pass

#         if hasattr(self, "custom_total_early_exit_minutes"):
#             self.custom_total_early_exit_minutes = float(total_early)
#         if hasattr(self, "custom_total_early_exit_hours"):
#             self.custom_total_early_exit_hours = round(total_early / 60.0, 3)
# #---------------------------------------------------from heeerrrr--------------------

import frappe
from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip
from frappe.utils import get_datetime, format_date
from datetime import datetime, date, time, timedelta


##################################################################################################
# أدوات مساعدة للعثور على SSA أو اختيار Salary Structure مناسب بدون إنشاء SSA جديد
##################################################################################################
def _safe_get_assigned_ssa(start_date, employee, company):
    """يحاول استدعاء الدالة الرسمية مع تواقيع متعددة عبر إصدارات HRMS.
    وإن فشل، يرجع آخر SSA صالح (<= start_date) لنفس الشركة.
    """
    try:
        from hrms.payroll.doctype.salary_structure_assignment.salary_structure_assignment import (
            get_assigned_salary_structure,
        )
        try:
            return get_assigned_salary_structure(start_date, employee, company)
        except TypeError:
            try:
                return get_assigned_salary_structure(start_date, employee)
            except TypeError:
                return get_assigned_salary_structure(employee, start_date)
    except Exception:
        pass

    return frappe.db.get_value(
        "Salary Structure Assignment",
        {
            "employee": employee,
            "company": company,
            "docstatus": 1,
            "from_date": ["<=", start_date],
        },
        "name",
        order_by="from_date desc",
    )


def _pick_structure_fallback(employee):
    """اختر Salary Structure منطقي عند عدم توفر SSA صالح."""
    # آخر Salary Slip سابق
    slip = frappe.db.get_value(
        "Salary Slip",
        {"employee": employee, "docstatus": 1},
        ["salary_structure"],
        order_by="start_date desc",
        as_dict=True,
    )
    if slip and slip.get("salary_structure"):
        return slip["salary_structure"]

    # آخر SSA لأي شركة
    any_ssa = frappe.db.get_value(
        "Salary Structure Assignment",
        {"employee": employee, "docstatus": 1},
        ["salary_structure"],
        order_by="from_date desc",
        as_dict=True,
    )
    if any_ssa and any_ssa.get("salary_structure"):
        return any_ssa["salary_structure"]

    # ضع اسم هيكل افتراضي إن رغبت، وإلا ارجع None
    return None


def _ensure_ssa_for_period(start_date, employee, company):
    """لا ينشئ SSA جديدًا إطلاقًا لتجنب DuplicateAssignment.
    يرجع (ssa_name, salary_structure) وفق المتاح:
    - SSA صالح لنفس الشركة (وقد نعدل تاريخه للأسفل إن لزم)
    - أو SSA صالح لشركة أخرى: نأخذ salary_structure فقط
    - أو fallback structure من آخر Slip/SSA
    """
    # 1) SSA صالح لنفس الشركة
    ssa_name = _safe_get_assigned_ssa(start_date, employee, company)
    if ssa_name:
        ssa_doc = frappe.get_doc("Salary Structure Assignment", ssa_name)
        if ssa_doc.from_date > start_date:
            # حاول جعل SSA يبدأ من تاريخ الفترة (إن فشل لا نوقف)
            try:
                ssa_doc.cancel()
                ssa_doc.from_date = start_date
                ssa_doc.submit()
            except Exception:
                pass
        return ssa_doc.name, ssa_doc.salary_structure

    # 2) SSA فعّال لأي شركة (نأخذ منه الـ structure فقط إن كان لشركة أخرى)
    any_active = frappe.get_all(
        "Salary Structure Assignment",
        filters={"employee": employee, "docstatus": 1, "from_date": ["<=", start_date]},
        fields=["name", "company", "salary_structure", "from_date"],
        order_by="from_date desc",
        limit=1,
    )
    if any_active:
        cur = any_active[0]
        if cur["company"] == company:
            return cur["name"], cur["salary_structure"]
        return None, cur["salary_structure"]

    # 3) لا شيء -> fallback
    struct = _pick_structure_fallback(employee)
    return (None, struct) if struct else (None, None)


def _load_ssa_min_dict(ssa_name: str) -> dict:
    """ديكت بسيط لـ self._salary_structure_assignment.
    يقرأ فقط الحقول الموجودة فعلاً في SSA (تفادي Unknown column) ويملأ الباقي بـ None.
    """
    if not ssa_name:
        return {}

    # الحقول المرغوبة نظريًا (بعضها قد لا يكون موجودًا في SSA في نسخ معينة)
    desired_fields = ["base", "variable", "payroll_frequency", "from_date", "name"]

    # خذ فقط الحقول الموجودة فعلاً في هذا الـ DocType
    try:
        meta = frappe.get_meta("Salary Structure Assignment")
        existing = []
        for f in desired_fields:
            # في بعض النسخ الحقل "name" ليس في meta.fields لكنه دائمًا موجود كـ PK
            if f == "name" or meta.has_field(f):
                existing.append(f)
    except Exception:
        # لو فشل جلب الميتاداتا، خذ الأقل أمانًا
        existing = ["base", "variable", "from_date", "name"]

    vals = frappe.db.get_value(
        "Salary Structure Assignment",
        ssa_name,
        existing,
        as_dict=True,
    ) or {}

    # أضف المفاتيح الناقصة بقيمة None حتى لا تتفاجأ كودات داخل HRMS
    for f in desired_fields:
        vals.setdefault(f, None)

    return vals



##################################################################################################
# ================= إعدادات عامة قابلة للتعديل =================
LATE_GRACE_MINUTES     = 15.0
WORKING_HOURS_PER_DAY  = 8.0
BASE_COMPONENTS        = {"راتب أساسي"}
FALLBACK_SHIFT_START   = time(8, 0)

# خصم التأخيرات
DEDUCTION_COMPONENT_NAME = "خصم التاخيرات"
DEDUCTION_ABBR           = "late_deduction"

# الوعاء الضريبي
TAXABLE_NAMES  = {"الوعاء الضريبي"}
TAXABLE_ABBR   = "amd_taxable"

# ضريبة يمني (ريال)
YEMEN_TAX_NAMES = {"الضريبة يمني"}
YEMEN_TAX_ABBR  = "tax_raiel_amd"

# ضريبة بالدولار (صف باسم "الضريبة")
USD_TAX_NAMES = {"الضريبة"}
USD_TAX_ABBR  = "amd_tax_1"

# غياب USD
ABSENCE_NAMES  = {"غياب USD"}
ABSENCE_ABBR   = "ABS_USD"

# معامل التحويل (حقل مخصص في Salary Slip)
TAX_EXCHANGE_FIELD = "custom_tax_exchange"

# البنود التي تدخل في إجمالي الخصومات
INCLUDE_IN_TOTAL_ABBRS = {"amd_tax_1", "loans", "ABS_USD", "late_deduction"}

# صفوف خاصة في الخصميات
TOTAL_DED_ROW_NAMES = {"اجمالي الخصومات", "إجمالي الخصومات"}
TOTAL_DED_ROW_ABBRS = {"to_reb_amd", "amd_total"}

NET_PAY_ROW_NAMES  = {"صافي الراتب", "صـافي الــراتب"}
NET_PAY_ROW_ABBRS  = {"Amd_net_pay", "amd_net_pay"}

# صف "إجمالي الكلي" في الإيرادات (مصدر الصافي)
GROSS_ROW_NAMES = {"اجمالي الكلي", "إجمالي الكلي"}
GROSS_ROW_ABBRS = {"amd_total"}
# ===============================================================


class CustomSalarySlip(SalarySlip):

    # تشغيل الأوفررايد فقط لو مكوّن خصم التأخيرات موجود (أو سطره موجود)
    def _should_run_override(self) -> bool:
        if frappe.db.exists("Salary Component", DEDUCTION_COMPONENT_NAME):
            return True
        for r in (self.deductions or []):
            if (r.salary_component or "").strip() == DEDUCTION_COMPONENT_NAME or (r.abbr or "").strip() == DEDUCTION_ABBR:
                return True
        return False

    # ---------------------------------------------------------------------------------------------
    # 1) إعداد SSA/Structure بشكل آمن قبل مناداة super().validate()
    # 2) حساب التأخيرات/الخروج المبكر
    # 3) استدعاء HRMS ثم تثبيت الإجماليات
    # ---------------------------------------------------------------------------------------------
    def validate(self):
        # اجلب SSA/Structure بدون إنشاء SSA جديد
        ssa_name, struct = _ensure_ssa_for_period(self.start_date, self.employee, self.company)

        # اضبط الحقول المتاحة
        if struct:
            self.salary_structure = struct
        if ssa_name:
            self.salary_structure_assignment = ssa_name

        # جهّز دائمًا الديكت الداخلي الذي يحتاجه HRMS (حتى لو بدون SSA)
        if not hasattr(self, "_salary_structure_assignment") or self._salary_structure_assignment is None:
            self._salary_structure_assignment = _load_ssa_min_dict(ssa_name)

        # ✅ فعّل فلاغات الحساب تلقائياً (مهم لروتين Payroll Entry)
        self._auto_enable_calc_flags()

        run = self._should_run_override()
        if run:
            # نظّف الجداول
            try:
                self.set("custom_late_days", [])
                self.set("custom_early_exit", [])
            except Exception:
                pass

            # Late Days
            if getattr(self, "custom_calculate_late_days", 0):
                self._late_minutes_result = self._late_minutes_by_day(self.employee, self.start_date, self.end_date)
                for d, minutes in sorted(self._late_minutes_result.items()):
                    self.append("custom_late_days", {"date": d, "minutes": minutes})
            else:
                self._late_minutes_result = {}

            # Early Exit
            if getattr(self, "custom_calculate_early_exit", 0):
                self.populate_early_exit_table()
            else:
                self._early_exit_result = {}

            # إجمالي الخصم من الاثنين
            self.apply_late_deduction()

        # استدعِ HRMS. لو رمى خطأ "existing SSA" نتجاوزه، والباقي نعيد رميه
        try:
            super().validate()
        except frappe.ValidationError as e:
            msg = str(e)
            if "Salary Structure Assignment for Employee already exists" in msg:
                frappe.msgprint("Using existing Salary Structure Assignment for this employee.")
            elif "Please assign a Salary Structure" in msg and getattr(self, "salary_structure", None):
                # عندنا هيكل بدون SSA: أكمل (الديكت الداخلي موجود)
                pass
            else:
                raise

                
         # إجمالي الخصم من الاثنين
        self.apply_late_deduction()
        if run:
            self._restore_late_row_if_missing()
            self._recompute_taxable_base()
            self._recompute_taxes_yer_and_usd()
            self._recalc_totals_into_existing_rows()
            self._freeze_total_and_net_rows()

    def before_save(self):
        if not self._should_run_override():
            return
        self._recalc_totals_into_existing_rows()
        self._freeze_total_and_net_rows()


    def _auto_enable_calc_flags(self):
        """
        فعّل الحقول التلقائية فقط عند المستند الجديد، أو عند الإنشاء من Payroll Entry
        بشرط أن الحقل غير مهيّأ (None). لا تغيّر اختيار المستخدم إذا كان 0.
        """
        pe_mode = bool(getattr(self, "payroll_entry", None))
        new_doc = False
        try:
            new_doc = self.is_new()
        except Exception:
            # fallback
            new_doc = not bool(getattr(self, "name", None))

        # لا تعدّل شيء إلا لو المستند جديد أو جاي من Payroll Entry
        if not (new_doc or pe_mode):
            return

        # فعّل فقط لو القيمة None (غير مهيّأة)، لا تحوّل 0 إلى 1
        if getattr(self, "custom_calculate_late_days", None) is None:
            try:
                self.custom_calculate_late_days = 1
            except Exception:
                pass

        if getattr(self, "custom_calculate_early_exit", None) is None:
            try:
                self.custom_calculate_early_exit = 1
            except Exception:
                pass

    def _auto_enable_calc_flags_ol(self):
        """فعّل حساب التأخيرات/الخروج المبكر تلقائياً عند الإنشاء من Payroll Entry
        أو عندما تكون الحقول غير معيّنة/0.
        """
        pe_mode = bool(getattr(self, "payroll_entry", None))

        # لو الفلاغ غير موجود أو قيمته 0 وفاتحة من Payroll Entry -> فعّله
        if pe_mode or getattr(self, "custom_calculate_late_days", None) in (None, 0, "0"):
            try:
                self.custom_calculate_late_days = 1
            except Exception:
                pass

        if pe_mode or getattr(self, "custom_calculate_early_exit", None) in (None, 0, "0"):
            try:
                self.custom_calculate_early_exit = 1
            except Exception:
                pass
            
            
            
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
            late_grace = 0.0 if not enable_late else (float(grace_val) if grace_val is not None else LATE_GRACE_MINUTES)
        return start_time, late_grace

    # -------- تجميع دقائق التأخير لكل يوم --------
    def _late_minutes_by_day(self, employee, start_date, end_date):
        late_by_day = {}

        # Attendance
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

        # Employee Checkin (أول دخول)
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
            if (row.salary_component or "").strip() in BASE_COMPONENTS:
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
        })

    # ====================== خصم التأخيرات ======================
    def apply_late_deduction(self):
        """يجمع تأخير الدخول + الخروج المبكر (حسب الفلاجز) ويحسب مبلغ الخصم."""
        calc_late  = 1 if getattr(self, "custom_calculate_late_days", 0) else 0
        calc_early = 1 if getattr(self, "custom_calculate_early_exit", 0) else 0

        # Late
        total_late_minutes = 0.0
        late_days_count = 0
        try:
            self.set("custom_late_days", [])
        except Exception:
            pass

        if calc_late:
            late_by_day = self._late_minutes_by_day(self.employee, self.start_date, self.end_date)
            for d in sorted(late_by_day.keys()):
                minutes = float(late_by_day[d] or 0)
                if minutes <= 0:
                    continue
                late_days_count += 1
                total_late_minutes += minutes
                try:
                    self.append("custom_late_days", {"date": d, "minutes": minutes})
                except Exception:
                    pass
            if hasattr(self, "custom_number_of_late_days"):
                self.custom_number_of_late_days = float(late_days_count)
            if hasattr(self, "custom_total_late_minutes"):
                self.custom_total_late_minutes = float(total_late_minutes)
            if hasattr(self, "custom_total_late_hours"):
                self.custom_total_late_hours = round(total_late_minutes / 60.0, 3)
        else:
            if hasattr(self, "custom_number_of_late_days"):
                self.custom_number_of_late_days = 0.0
            if hasattr(self, "custom_total_late_minutes"):
                self.custom_total_late_minutes = 0.0
            if hasattr(self, "custom_total_late_hours"):
                self.custom_total_late_hours = 0.0

        # Early Exit
        total_early_minutes = 0.0
        try:
            self.set("custom_early_exit", [])
        except Exception:
            pass

        if calc_early:
            early_by_day = self._early_exit_minutes_by_day(self.employee, self.start_date, self.end_date)
            for d in sorted(early_by_day.keys()):
                minutes = float(early_by_day[d] or 0)
                if minutes <= 0:
                    continue
                total_early_minutes += minutes
                try:
                    self.append("custom_early_exit", {
                        "early_exit_date": d,
                        "early_exit_minutes": minutes,
                    })
                except Exception:
                    pass
            if hasattr(self, "custom_total_early_exit_minutes"):
                self.custom_total_early_exit_minutes = float(total_early_minutes)
            if hasattr(self, "custom_total_early_exit_hours"):
                self.custom_total_early_exit_hours = round(total_early_minutes / 60.0, 3)
        else:
            if hasattr(self, "custom_total_early_exit_minutes"):
                self.custom_total_early_exit_minutes = 0.0
            if hasattr(self, "custom_total_early_exit_hours"):
                self.custom_total_early_exit_hours = 0.0

        # المجموع والخصم
        total_minutes_for_deduction = total_late_minutes + total_early_minutes
        if hasattr(self, "custom_total_late_plus_early_minutes"):
            self.custom_total_late_plus_early_minutes = float(total_minutes_for_deduction)
        if hasattr(self, "custom_total_late_plus_early_hours"):
            self.custom_total_late_plus_early_hours = round(total_minutes_for_deduction / 60.0, 3)

        base_amount = self._sum_base_components(self.earnings)
        payment_days = float(self.payment_days or self.total_working_days or 26.0)
        minutes_in_period = WORKING_HOURS_PER_DAY * 60.0 * payment_days

        late_deduction = 0.0
        if base_amount > 0 and minutes_in_period > 0 and total_minutes_for_deduction > 0:
            late_deduction = base_amount * (total_minutes_for_deduction / minutes_in_period)

        if hasattr(self, "custom_late_deduction_amount"):
            self.custom_late_deduction_amount = float(late_deduction or 0)

        self._late_amount = float(late_deduction or 0)
        self._upsert_deduction_row(self._late_amount, DEDUCTION_COMPONENT_NAME)

    def apply_late_deduction_ol(self):
        # نسخة أقدم، أبقيناها كما هي لمن يحتاجها
        late_by_day = self._late_minutes_by_day(self.employee, self.start_date, self.end_date)
        try:
            self.set("custom_late_days", [])
        except Exception:
            pass

        late_days_count = 0
        total_late_minutes = 0.0
        for d in sorted(late_by_day.keys()):
            minutes = float(late_by_day[d] or 0)
            if minutes <= 0:
                continue
            late_days_count += 1
            total_late_minutes += minutes
            try:
                self.append("custom_late_days", {"date": d, "minutes": minutes})
            except Exception:
                pass

        early_by_day = self._early_exit_minutes_by_day(self.employee, self.start_date, self.end_date)
        total_early_minutes = 0.0
        for d in early_by_day.keys():
            m = float(early_by_day[d] or 0)
            if m > 0:
                total_early_minutes += m

        total_minutes_for_deduction = total_late_minutes + total_early_minutes

        if hasattr(self, "custom_number_of_late_days"):
            self.custom_number_of_late_days = float(late_days_count)
        if hasattr(self, "custom_total_late_minutes"):
            self.custom_total_late_minutes = float(total_late_minutes)
        if hasattr(self, "custom_total_late_hours"):
            self.custom_total_late_hours = round(total_late_minutes / 60.0, 3)

        if hasattr(self, "custom_total_early_exit_minutes") and not getattr(self, "custom_total_early_exit_minutes", None):
            self.custom_total_early_exit_minutes = float(total_early_minutes)
        if hasattr(self, "custom_total_early_exit_hours") and not getattr(self, "custom_total_early_exit_hours", None):
            self.custom_total_early_exit_hours = round(total_early_minutes / 60.0, 3)

        if hasattr(self, "custom_total_late_plus_early_minutes"):
            self.custom_total_late_plus_early_minutes = float(total_minutes_for_deduction)
        if hasattr(self, "custom_total_late_plus_early_hours"):
            self.custom_total_late_plus_early_hours = round(total_minutes_for_deduction / 60.0, 3)

        base_amount = self._sum_base_components(self.earnings)
        payment_days = float(self.payment_days or self.total_working_days or 26.0)
        minutes_in_period = WORKING_HOURS_PER_DAY * 60.0 * payment_days

        late_deduction = 0.0
        if base_amount > 0 and minutes_in_period > 0 and total_minutes_for_deduction > 0:
            late_deduction = base_amount * (total_minutes_for_deduction / minutes_in_period)

        if hasattr(self, "custom_late_deduction_amount"):
            self.custom_late_deduction_amount = float(late_deduction or 0)

        self._late_amount = float(late_deduction or 0)
        self._upsert_deduction_row(late_deduction, DEDUCTION_COMPONENT_NAME)

    def _restore_late_row_if_missing(self):
        amt = float(getattr(self, "_late_amount", 0.0))
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
                return
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

    # def _is_total_row(self, row) -> bool:
    #     name = (row.salary_component or "") or ""
    #     return self._match_row(row, TOTAL_DED_ROW_NAMES, TOTAL_DED_ROW_ABBRS) or ("إجمالي" in name and "خصومات" في name)


    def _is_total_row(self, row) -> bool:
        name = (row.salary_component or "") or ""
        # يتحمّل "إجمالي/اجمالي" و"خصومات/الخصومات"
        is_total_phrase = (
            ("إجمالي" in name or "اجمالي" in name) and
            ("خصومات" in name or "الخصومات" in name)
        )
        return self._match_row(row, TOTAL_DED_ROW_NAMES, TOTAL_DED_ROW_ABBRS) or is_total_phrase

    def _is_net_row(self, row) -> bool:
        name = (row.salary_component or "").strip()
        abbr = (row.abbr or "").strip().lower()
        return (name in NET_PAY_ROW_NAMES) or (abbr in {a.lower() for a in NET_PAY_ROW_ABBRS}) or ("صافي" in name) or ("net" in abbr and "pay" in abbr)

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

    # ==================== الوعاء + الضريبة يمني + الضريبة USD ====================
    def _recompute_taxable_base(self):
        base_salary = 0.0
        for r in (self.earnings or []):
            if (r.salary_component or "").strip() in BASE_COMPONENTS:
                base_salary += float(r.amount or 0)

        abs_usd = self._get_amount_any(ABSENCE_NAMES, {ABSENCE_ABBR})
        late    = self._get_amount_any({DEDUCTION_COMPONENT_NAME}, {DEDUCTION_ABBR})

        try:
            exchange = float(getattr(self, TAX_EXCHANGE_FIELD))
        except Exception:
            exchange = 1.0

        taxable_val = (base_salary - abs_usd - late) * exchange
        if taxable_val < 0:
            taxable_val = 0.0

        for row in (self.deductions or []):
            if self._match_row(row, TAXABLE_NAMES, {TAXABLE_ABBR}):
                row.amount = float(taxable_val or 0)
                try:
                    row.amount_based_on_formula = 0
                    row.do_not_include_in_total = 1
                except Exception:
                    pass
                break

    def _recompute_taxes_yer_and_usd(self):
        taxable_val = self._get_amount_any(TAXABLE_NAMES, {TAXABLE_ABBR})

        base_over = max(0.0, taxable_val - 20000.0)
        yer_tax = 0.0
        if taxable_val > 0:
            yer_tax = base_over * 0.15 + 1000.0

        for row in (self.deductions or []):
            if self._match_row(row, YEMEN_TAX_NAMES, {YEMEN_TAX_ABBR}):
                row.amount = float(yer_tax or 0)
                try:
                    row.amount_based_on_formula = 0
                    row.do_not_include_in_total = 1
                except Exception:
                    pass
                break

        try:
            exchange = float(getattr(self, TAX_EXCHANGE_FIELD))
        except Exception:
            exchange = 1.0
        usd_tax = (yer_tax / exchange) if exchange else 0.0

        for row in (self.deductions or []):
            if self._match_row(row, USD_TAX_NAMES, {USD_TAX_ABBR}):
                row.amount = float(usd_tax or 0)
                try:
                    row.amount_based_on_formula = 0
                    row.do_not_include_in_total = 0
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

    # ====== نهاية الشفت ======
    def _get_shift_end_time(self, employee, the_date: date) -> time:
        """end_time من الشفت، وإن لم نجد نستخدم start + WORKING_HOURS_PER_DAY."""
        rec = frappe.db.sql(
            """
            SELECT st.start_time, st.end_time
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

        def coerce_t(val):
            if isinstance(val, time):
                return val
            if isinstance(val, timedelta):
                base = datetime.min + val
                return time(base.hour, base.minute, base.second)
            return None

        if rec:
            st = coerce_t(rec[0].get("start_time")) or FALLBACK_SHIFT_START
            et = coerce_t(rec[0].get("end_time"))
            if et:
                return et
            dt = (datetime.combine(the_date, st) + timedelta(hours=WORKING_HOURS_PER_DAY))
            return time(dt.hour, dt.minute, dt.second)

        dt = (datetime.combine(the_date, FALLBACK_SHIFT_START) + timedelta(hours=WORKING_HOURS_PER_DAY))
        return time(dt.hour, dt.minute, dt.second)

    # ====== دقائق الخروج المبكر ======
    def _early_exit_minutes_by_day(self, employee, start_date, end_date):
        early_by_day = {}

        # من Attendance (إن وُجد out_time)
        atts = frappe.get_all(
            "Attendance",
            filters={"employee": employee, "attendance_date": ["between", [start_date, end_date]], "docstatus": 1},
            fields=["attendance_date", "status", "out_time"],
            order_by="attendance_date asc",
        )
        for a in (atts or []):
            d = a.get("attendance_date")
            if a.get("status") not in ("Present", "Work From Home", "On Duty"):
                continue
            out_time_val = a.get("out_time")
            if not out_time_val:
                continue
            out_dt = get_datetime(out_time_val)
            end_t = self._get_shift_end_time(employee, d)
            shift_end_dt = datetime.combine(d, end_t)
            minutes = (shift_end_dt - out_dt).total_seconds() / 60.0
            if minutes > 0:
                early_by_day[d] = minutes

        # من Employee Checkin (آخر OUT أو آخر سجل)
        checkins = frappe.get_all(
            "Employee Checkin",
            filters={
                "employee": employee,
                "time": ["between", [f"{start_date} 00:00:00", f"{end_date} 23:59:59"]],
                "docstatus": 1,
            },
            fields=["time", "log_type"],
            order_by="time asc",
        )

        last_by_day = {}
        for c in (checkins or []):
            dt = get_datetime(c.get("time"))
            d = dt.date()
            lt = (c.get("log_type") or "").upper().strip()
            if d not in last_by_day:
                last_by_day[d] = {"last": dt, "last_out": None}
            last_by_day[d]["last"] = dt
            if lt == "OUT":
                last_by_day[d]["last_out"] = dt

        for d, info in last_by_day.items():
            if d in early_by_day:
                continue
            last_out = info.get("last_out") or info.get("last")
            if not last_out:
                continue
            end_t = self._get_shift_end_time(employee, d)
            shift_end_dt = datetime.combine(d, end_t)
            minutes = (shift_end_dt - last_out).total_seconds() / 60.0
            if minutes > 0:
                early_by_day[d] = minutes

        return early_by_day

    # ====== تعبئة جدول الخروج المبكر ======
    def populate_early_exit_table(self):
        try:
            self.set("custom_early_exit", [])
        except Exception:
            pass

        by_day = self._early_exit_minutes_by_day(self.employee, self.start_date, self.end_date)

        total_early = 0.0
        for d in sorted(by_day.keys()):
            minutes = float(by_day[d] or 0)
            if minutes <= 0:
                continue
            total_early += minutes
            try:
                self.append("custom_early_exit", {
                    "early_exit_date": d,
                    "early_exit_minutes": minutes,
                })
            except Exception:
                pass

        if hasattr(self, "custom_total_early_exit_minutes"):
            self.custom_total_early_exit_minutes = float(total_early)
        if hasattr(self, "custom_total_early_exit_hours"):
            self.custom_total_early_exit_hours = round(total_early / 60.0, 3)
