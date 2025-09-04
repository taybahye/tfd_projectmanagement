# my_app/payroll/late_deduction.py
import frappe
from datetime import datetime, time, timedelta
from frappe.utils import get_datetime

LATE_GRACE_MINUTES = 10.0
WORKING_HOURS_PER_DAY = 8.0
BASE_COMPONENTS = {"Basic", "IMC Basic Salary"}
FALLBACK_SHIFT_START = time(8, 0)

def minutes_diff(later_dt, earlier_dt):
    return (later_dt - earlier_dt).total_seconds() / 60.0

def get_shift_meta(employee, the_date):
    rec = frappe.db.sql("""
        SELECT st.start_time, st.late_entry_grace_period
        FROM `tabShift Assignment` sa
        JOIN `tabShift Type` st ON st.name = sa.shift_type
        WHERE sa.employee=%s
          AND sa.start_date <= %s
          AND (sa.end_date IS NULL OR sa.end_date >= %s)
        ORDER BY sa.start_date DESC
        LIMIT 1
    """, (employee, the_date, the_date), as_dict=True)

    start_time = FALLBACK_SHIFT_START
    late_grace = LATE_GRACE_MINUTES
    if rec:
        st = rec[0].get("start_time")
        if isinstance(st, timedelta):
            start_time = (datetime.min + st).time()
        elif isinstance(st, time):
            start_time = st
        lg = rec[0].get("late_entry_grace_period")
        if lg is not None:
            late_grace = float(lg)
    return start_time, late_grace

def total_late_from_attendance(employee, start_date, end_date):
    total = 0.0
    atts = frappe.get_all("Attendance",
        filters={"employee": employee, "attendance_date": ["between", [start_date, end_date]], "docstatus": 1},
        fields=["attendance_date", "status", "in_time"]
    )
    for a in atts:
        if a.status not in ("Present","Work From Home","On Duty"): 
            continue
        if not a.in_time: 
            continue
        in_dt = get_datetime(a.in_time)
        st_time, grace = get_shift_meta(employee, a.attendance_date)
        shift_start_dt = datetime.combine(a.attendance_date, st_time)
        late = minutes_diff(in_dt, shift_start_dt) - grace
        if late > 0: 
            total += late
    return total

def total_late_from_checkin(employee, start_date, end_date):
    checkins = frappe.get_all("Employee Checkin",
        filters={"employee": employee, "time": ["between", [f"{start_date} 00:00:00", f"{end_date} 23:59:59"]], "docstatus":1},
        fields=["time"], order_by="time asc"
    )
    first_in = {}
    for c in checkins:
        dt = get_datetime(c.time)
        d = dt.date()
        first_in.setdefault(d, dt)
    total = 0.0
    for d, in_dt in first_in.items():
        st_time, grace = get_shift_meta(employee, d)
        shift_start_dt = datetime.combine(d, st_time)
        late = minutes_diff(in_dt, shift_start_dt) - grace
        if late > 0: 
            total += late
    return total

def sum_base(earnings):
    total = 0.0
    for row in (earnings or []):
        if (row.salary_component or "").strip() in BASE_COMPONENTS:
            total += float(row.amount or 0)
    return total

def upsert_deduction(doc, amount, component="Late Deduction"):
    for row in (doc.deductions or []):
        if (row.salary_component or "").strip() == component:
            row.amount = float(amount or 0)
            return
    doc.append("deductions", {"salary_component": component, "amount": float(amount or 0)})

def apply_late_deduction(doc, method):
    # 1) ???? ????? ???????
    total_late = total_late_from_attendance(doc.employee, doc.start_date, doc.end_date)
    if total_late <= 0:
        total_late = total_late_from_checkin(doc.employee, doc.start_date, doc.end_date)

    # (???????) ?????? ?? ???? ????? ?? ????
    if hasattr(doc, "custom_total_late_minutes"):
        doc.custom_total_late_minutes = float(total_late or 0)

    # 2) ???? ????? ????? ?? ???????? ????????
    base_amount = sum_base(doc.earnings)
    payment_days = float(doc.payment_days or doc.total_working_days or 26.0)
    minutes_in_period = WORKING_HOURS_PER_DAY * 60.0 * payment_days

    late_deduction = 0.0
    if base_amount > 0 and minutes_in_period > 0 and total_late > 0:
        late_deduction = base_amount * (total_late / minutes_in_period)

    if hasattr(doc, "custom_late_deduction_amount"):
        doc.custom_late_deduction_amount = float(late_deduction or 0)

    # 3) ???/???? ????? ?????
    upsert_deduction(doc, late_deduction)
