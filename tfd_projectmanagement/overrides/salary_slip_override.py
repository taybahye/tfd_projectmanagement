# apps/tfd_projectmanagement/tfd_projectmanagement/overrides/salary_slip_override.py
import frappe
from hrms.payroll.doctype.salary_slip.salary_slip import SalarySlip
from frappe.utils import get_datetime
from datetime import datetime, date, time, timedelta

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

# ضريبة بالدولار (الصف المسمى "الضريبة")
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

    # -------- دورة التنفيذ --------
    def validate(self):
        run = self._should_run_override()

        # 1) احسب خصم التأخيرات قبل معادلات الهيكل
        if run:
            self.apply_late_deduction()

        # 2) دع HRMS ينفذ معادلات Salary Structure
        super().validate()

        if run:
            # قد يختفي سطر التأخيرات أثناء super().validate()، نعيده
            self._restore_late_row_if_missing()

            # 3) نحسب الوعاء الضريبي ثم الضريبة يمني ثم الضريبة بالدولار (ونثبت السطور)
            self._recompute_taxable_base()
            self._recompute_taxes_yer_and_usd()

            # 4) نجمع الإجماليات ونثبت سطري "الإجمالي" و"الصافي"
            self._recalc_totals_into_existing_rows()
            self._freeze_total_and_net_rows()

    def before_save(self):
        if not self._should_run_override():
            return
        # ترتيب نهائي قبل الحفظ
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

        # Employee Checkin (أول دخول في اليوم)
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

        self._late_amount = float(late_deduction or 0)  # قد نحتاجه بعد validate()
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
        # غير موجود -> أضفه
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
        name = (row.salary_component or "") or ""
        return self._match_row(row, TOTAL_DED_ROW_NAMES, TOTAL_DED_ROW_ABBRS) or ("إجمالي" in name and "خصومات" in name)

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
        # راتب أساسي (قد يكون أكثر من صف)
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
                    row.amount_based_on_formula = 0   # تثبيت
                    row.do_not_include_in_total = 1   # لا يدخل في الإجمالي
                except Exception:
                    pass
                break

    def _recompute_taxes_yer_and_usd(self):
        # اجلب الوعاء الضريبي الذي ثبتناه للتو
        taxable_val = self._get_amount_any(TAXABLE_NAMES, {TAXABLE_ABBR})

        # معادلة الصورة: ((amd_taxable - 20000) * 0.15 + 1000) إذا كان هناك وعاء
        # نحمي من السالب
        base_over = max(0.0, taxable_val - 20000.0)
        yer_tax = 0.0
        if taxable_val > 0:
            yer_tax = base_over * 0.15 + 1000.0

        # عيّن الضريبة يمني (tax_raiel_amd) وثبتها
        for row in (self.deductions or []):
            if self._match_row(row, YEMEN_TAX_NAMES, {YEMEN_TAX_ABBR}):
                row.amount = float(yer_tax or 0)
                try:
                    row.amount_based_on_formula = 0   # تثبيت هذا السطر
                    row.do_not_include_in_total = 1   # عادة لا يدخل في الإجمالي (الإجمالي بالدولار)
                except Exception:
                    pass
                break

        # الضريبة بالدولار = tax_raiel_amd / custom_tax_exchange
        try:
            exchange = float(getattr(self, TAX_EXCHANGE_FIELD))
        except Exception:
            exchange = 1.0
        usd_tax = (yer_tax / exchange) if exchange else 0.0

        for row in (self.deductions or []):
            if self._match_row(row, USD_TAX_NAMES, {USD_TAX_ABBR}):
                row.amount = float(usd_tax or 0)
                try:
                    row.amount_based_on_formula = 0  # تثبيت
                    # هذه تدخل في إجمالي الخصومات حسب INCLUDE_IN_TOTAL_ABBRS
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
