import ttkbootstrap as tb
from ttkbootstrap.constants import BOTH, YES
from transactions import get_all_transactions
 
 
def get_transaction_ledger():

    transactions = get_all_transactions()
 
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
 
    return transactions, summary
 
 
 
class LedgerFrame(tb.Frame):

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._build()
 
 
    def _build(self):
        transactions, summary = get_transaction_ledger()
        self._build_summary_cards(summary)
        self._build_table(transactions, summary)
 
    def _build_summary_cards(self, summary):
        card_row = tb.Frame(self)
        card_row.pack(fill="x", padx=20, pady=(16, 8))
 
        cards = [
            ("Total Income",   f"+${summary['total_income']:,.2f}",   "success"),
            ("Total Expenses", f"-${summary['total_expenses']:,.2f}", "danger"),
            (
                "Net Balance",
                f"{'+' if summary['net'] >= 0 else ''}${summary['net']:,.2f}",
                "success" if summary["net"] >= 0 else "danger",
            ),
        ]
 
        for i, (label, value, style) in enumerate(cards):
            card = tb.Frame(card_row, bootstyle="secondary", padding=12)
            card.pack(side="left", expand=True, fill="x", padx=6)
 
            tb.Label(card, text=label, font=("Helvetica", 9),
                     bootstyle="secondary").pack(anchor="w")
            tb.Label(card, text=value, font=("Helvetica", 18, "bold"),
                     bootstyle=style).pack(anchor="w")
 
            # Show status text on the Net Balance card only
            if i == 2:
                tb.Label(card, text=summary["status"], font=("Helvetica", 9),
                         bootstyle=style).pack(anchor="w", pady=(2, 0))
 
    def _build_table(self, transactions, summary):
        columns = ("Date", "Description", "Category", "Type", "Amount")
 
        tree = tb.Treeview(
            self,
            columns=columns,
            show="headings",
            bootstyle="secondary",
            height=15,
        )
 
        # Column widths
        widths = {"Date": 110, "Description": 200, "Category": 120,
                  "Type": 90, "Amount": 110}
        for col in columns:
            tree.heading(col, text=col)
            anchor = "e" if col == "Amount" else "w"
            tree.column(col, anchor=anchor, width=widths[col])
 
        # Row colour tags
        tree.tag_configure("income",  foreground="#28a745")
        tree.tag_configure("expense", foreground="#dc3545")
 
        # Populate rows
        for row in transactions:
            date, desc, cat, amount, tx_type, _ = row
            signed = (f"+${amount:,.2f}" if tx_type == "Income"
                      else f"-${abs(amount):,.2f}")
            tag = "income" if tx_type == "Income" else "expense"
            tree.insert("", "end",
                        values=(date, desc, cat, tx_type, signed),
                        tags=(tag,))
 
        # Net total row
        net_str = (f"+${summary['net']:,.2f}" if summary["net"] >= 0
                   else f"-${abs(summary['net']):,.2f}")
        net_tag = "income" if summary["net"] >= 0 else "expense"
        tree.insert("", "end",
                    values=(f"Net  ({summary['count']} transactions)",
                            "", "", "", net_str),
                    tags=(net_tag,))
 
        # Scrollbar
        scrollbar = tb.Scrollbar(self, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
 
        tree.pack(side="left", fill=BOTH, expand=YES,
                  padx=(20, 0), pady=10)
        scrollbar.pack(side="left", fill="y", pady=10, padx=(0, 20))