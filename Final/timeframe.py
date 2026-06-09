from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from transactions import get_all_transactions


def get_date_range(preset: str, cycle_start_day: int = 1, custom_start: date = None, custom_end: date = None):
    today = date.today()
    day   = max(1, min(cycle_start_day, 28))

    if preset == "All Time":
        return None, None

    if preset == "Custom":
        return custom_start, custom_end

    if preset == "Last 7 Days":
        return today - timedelta(days=6), today

    if preset == "Last 30 Days":
        return today - timedelta(days=29), today

    if preset == "This Year":
        return date(today.year, 1, 1), date(today.year, 12, 31)

    # Billing-cycle-aware presets
    if today.day >= day:
        cycle_start = date(today.year, today.month, day)
    else:
        prev        = today - relativedelta(months=1)
        cycle_start = date(prev.year, prev.month, day)

    cycle_end = cycle_start + relativedelta(months=1) - timedelta(days=1)

    if preset == "This Month":
        return cycle_start, cycle_end

    if preset == "Last Month":
        prev_start = cycle_start - relativedelta(months=1)
        prev_end   = cycle_start - timedelta(days=1)
        return prev_start, prev_end

    return None, None


def filter_transactions(transactions, start: date, end: date):
    if start is None and end is None:
        return transactions

    filtered = []
    for row in transactions:
        tx_date = row[0]
        if isinstance(tx_date, str):
            tx_date = date.fromisoformat(tx_date)
        if start <= tx_date <= end:
            filtered.append(row)
    return filtered


def get_ledger_for_period(preset: str = "This Month",
                          cycle_start_day: int = 1,
                          custom_start: date = None,
                          custom_end: date = None):
    all_transactions = get_all_transactions()
    start, end       = get_date_range(preset, cycle_start_day, custom_start, custom_end)
    transactions     = filter_transactions(all_transactions, start, end)

    total_income   = sum(row[3] for row in transactions if row[4] == "Income")
    total_expenses = sum(abs(row[3]) for row in transactions if row[4] == "Expense")
    net            = total_income - total_expenses

    summary = {
        "total_income":   total_income,
        "total_expenses": total_expenses,
        "net":            net,
        "status":         "Under control" if net >= 0 else "Overspending",
        "count":          len(transactions),
    }

    return transactions, summary, start, end
                              
def apply_custom_range(ledger, from_date_entry, to_date_entry):
    try:
        start = date.fromisoformat(from_date_entry.entry.get())
        end   = date.fromisoformat(to_date_entry.entry.get())
        if start > end:
            raise ValueError("From date must be before To date.")
    except ValueError as e:
        print(f"Date range error: {e}")
        return False
    if ledger is not None:
        ledger.set_custom_range(start, end)
    return True
    
def apply_cycle_day(ledger, cycle_day_var):
    try:
        day = max(1, min(int(cycle_day_var.get()), 28))
    except ValueError:
        day = 1
    if ledger is not None:
        ledger._cycle_start_day = day
        ledger._refresh()
PRESETS = [
    "This Month",
    "Last Month",
    "Last 7 Days",
    "Last 30 Days",
    "This Year",
    "All Time",
    "Custom",
]
