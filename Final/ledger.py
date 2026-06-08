import ttkbootstrap as tb
from ttkbootstrap.constants import BOTH, YES
from tkinter import messagebox, ttk
import tkinter as tk
from datetime import date
from decimal import Decimal, InvalidOperation
from transactions import get_all_transactions
from database import get_db_connection
from timeframe import get_date_range, filter_transactions, PRESETS



def _get_transaction_id(tx_date, description, amount, tx_type):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT id FROM transactions
            WHERE transaction_date = %s
              AND description      = %s
              AND ABS(amount)      = %s
              AND transaction_type = %s
            ORDER BY id DESC LIMIT 1;
        """, (tx_date, description, Decimal(str(abs(amount))), tx_type))
        row = cursor.fetchone()
        return row[0] if row else None
    except Exception as e:
        print(f"Lookup error: {e}")
        return None
    finally:
        cursor.close()
        conn.close()


def _delete_transaction(transaction_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM transactions WHERE id = %s;", (transaction_id,))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Delete error: {e}")
        return False
    finally:
        cursor.close()
        conn.close()


def _update_transaction(transaction_id: int, tx_date, amount, description,
                        tx_type: str, category_name: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO categories (name) VALUES (%s) ON CONFLICT (name) DO UPDATE SET name=EXCLUDED.name RETURNING id;",
            (category_name,)
        )
        category_id = cursor.fetchone()[0]
        cursor.execute("""
            UPDATE transactions
            SET transaction_date = %s,
                amount           = %s,
                description      = %s,
                transaction_type = %s,
                category_id      = %s
            WHERE id = %s;
        """, (tx_date, Decimal(str(amount)), description, tx_type, category_id, transaction_id))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Update error: {e}")
        return False
    finally:
        cursor.close()
        conn.close()



def get_transaction_ledger(preset="All Time", cycle_start_day=1,
                           custom_start=None, custom_end=None):
                               
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
        "start":          start,
        "end":            end,
    }
    return transactions, summary


class _CellEditor:

    EXPENSE_CATEGORIES = ["Food", "Rent", "Phone", "Utilities", "Commute", "Leisure", "Other"]
    INCOME_CATEGORIES  = ["Salary", "Bonus", "Other"]
    TYPE_OPTIONS       = ["Income", "Expense"]

    def __init__(self, tree: tb.Treeview, item_id: str, col_index: int,
                 current_value: str, on_commit):
        self._tree      = tree
        self._item_id   = item_id
        self._col_index = col_index
        self._on_commit = on_commit
        self._widget    = None

        col_id   = tree["columns"][col_index]
        bbox     = tree.bbox(item_id, column=col_id)
        if not bbox:
            return
        x, y, w, h = bbox
        col_name = tree.heading(col_id)["text"]

        if col_name == "Type":
            self._widget = ttk.Combobox(tree, values=self.TYPE_OPTIONS,
                                        state="readonly", width=w // 10)
            self._widget.set(current_value)
            self._widget.bind("<<ComboboxSelected>>", self._commit)

        elif col_name == "Category":
            values_col = tree["columns"][3]
            tx_type    = tree.set(item_id, values_col)
            cats = self.INCOME_CATEGORIES if tx_type == "Income" else self.EXPENSE_CATEGORIES
            self._widget = ttk.Combobox(tree, values=cats,
                                        state="readonly", width=w // 10)
            self._widget.set(current_value)
            self._widget.bind("<<ComboboxSelected>>", self._commit)

        else:
            var = tk.StringVar(value=current_value)
            self._widget = ttk.Entry(tree, textvariable=var)
            self._widget.bind("<Return>", self._commit)
            self._widget.bind("<Escape>", self._cancel)

        self._widget.place(x=x, y=y, width=w, height=h)
        self._widget.focus_set()
        self._widget.bind("<FocusOut>", self._commit)

    def _commit(self, _event=None):
        if self._widget is None:
            return
        value = self._widget.get()
        self._widget.destroy()
        self._widget = None
        self._on_commit(self._item_id, self._col_index, value)

    def _cancel(self, _event=None):
        if self._widget:
            self._widget.destroy()
            self._widget = None



class LedgerFrame(tb.Frame):
  
    COLUMNS = [
        ("Date",        True),
        ("Description", True),
        ("Category",    True),
        ("Type",        True),
        ("Amount",      True),
    ]

    _BUTTON_PRESETS = [
        "All Time",
        "This Month",
        "Last Month",
        "Last 7 Days",
        "Last 30 Days",
        "This Year",
    ]

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self._tree            = None
        self._raw_rows        = []
        self._editor          = None
        self._preset          = "All Time"
        self._cycle_start_day = 1
        self._custom_start    = None
        self._custom_end      = None
        self._preset_buttons  = {}

        self._build_controls()
        self._refresh()


    def set_custom_range(self, start: date, end: date):
        """
        Call this from outside (e.g. gui.py) to apply a custom date range.
        Switches the active preset to Custom and refreshes the table.
        """
        self._custom_start = start
        self._custom_end   = end
        self._set_preset("Custom")


    def _build_controls(self):
        bar = tb.Frame(self)
        bar.pack(fill="x", padx=20, pady=(10, 4))

        for preset in self._BUTTON_PRESETS:
            btn = tb.Button(
                bar, text=preset, width=10,
                bootstyle="primary" if preset == self._preset else "outline-secondary",
                command=lambda p=preset: self._set_preset(p),
            )
            btn.pack(side="left", padx=(0, 4))
            self._preset_buttons[preset] = btn

    def _set_preset(self, preset: str):
        self._preset = preset
        for p, btn in self._preset_buttons.items():
            btn.configure(bootstyle="primary" if p == preset else "outline-secondary")
        self._refresh()

    def _on_cycle_change(self):
        try:
            self._cycle_start_day = int(self._day_var.get())
        except ValueError:
            self._cycle_start_day = 1
        self._refresh()

    def _refresh(self):
        children = self.winfo_children()
        for widget in children[1:]:
            widget.destroy()
        self._editor = None

        transactions, summary = get_transaction_ledger(
            preset=self._preset,
            cycle_start_day=self._cycle_start_day,
            custom_start=self._custom_start,
            custom_end=self._custom_end,
        )
        self._raw_rows = list(transactions)

        self._build_period_label(summary)
        self._build_summary_cards(summary)
        self._build_action_bar()
        self._build_table(transactions, summary)


    def _build_period_label(self, summary):
        start, end = summary["start"], summary["end"]
        if start and end:
            text = f"{start.strftime('%b %d, %Y')}  →  {end.strftime('%b %d, %Y')}"
        else:
            text = "All Time"

        tb.Label(self, text=text, font=("Helvetica", 9),
                 bootstyle="secondary").pack(anchor="w", padx=22, pady=(2, 0))


    def _build_summary_cards(self, summary):
        card_row = tb.Frame(self)
        card_row.pack(fill="x", padx=20, pady=(6, 8))

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
            if i == 2:
                tb.Label(card, text=summary["status"], font=("Helvetica", 9),
                         bootstyle=style).pack(anchor="w", pady=(2, 0))


    def _build_action_bar(self):
        bar = tb.Frame(self)
        bar.pack(fill="x", padx=20, pady=(0, 4))

        tb.Label(bar, text="Double-click a cell to edit  •  Select a row and press Delete to remove",
                 font=("Helvetica", 9), bootstyle="secondary").pack(side="left")

        tb.Button(bar, text="🗑  Delete", bootstyle="outline-danger",
                  command=self._on_delete).pack(side="right")


    def _build_table(self, transactions, summary):
        col_ids = [c[0] for c in self.COLUMNS]

        self._tree = tb.Treeview(
            self, columns=col_ids, show="headings",
            bootstyle="secondary", height=10, selectmode="browse",
        )

        widths = {"Date": 110, "Description": 200, "Category": 120,
                  "Type": 90, "Amount": 110}
        for col in col_ids:
            self._tree.heading(col, text=col)
            anchor = "e" if col == "Amount" else "w"
            self._tree.column(col, anchor=anchor, width=widths[col])

        self._tree.tag_configure("income",  foreground="#28a745")
        self._tree.tag_configure("expense", foreground="#dc3545")
        self._tree.tag_configure("net",     foreground="gray")

        if not transactions:
            self._tree.insert("", "end",
                              values=("—", "No transactions in this period", "", "", "—"),
                              tags=("net",))
        else:
            for row in transactions:
                tx_date, desc, cat, amount, tx_type, _ = row
                signed = (f"+${amount:,.2f}" if tx_type == "Income"
                          else f"-${abs(amount):,.2f}")
                tag = "income" if tx_type == "Income" else "expense"
                self._tree.insert("", "end",
                                  values=(tx_date, desc, cat, tx_type, signed),
                                  tags=(tag,))

            net_str = (f"+${summary['net']:,.2f}" if summary["net"] >= 0
                       else f"-${abs(summary['net']):,.2f}")
            self._tree.insert("", "end",
                              values=(f"Net  ({summary['count']} transactions)",
                                      "", "", "", net_str),
                              tags=("net",))

        self._tree.bind("<Double-1>", self._on_double_click)
        self._tree.bind("<Delete>",   self._on_delete)

        scrollbar = tb.Scrollbar(self, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=scrollbar.set)

        self._tree.pack(side="left", fill=BOTH, expand=YES, padx=(20, 0), pady=10)
        scrollbar.pack(side="left", fill="y", pady=10, padx=(0, 20))


    def _on_double_click(self, event):
        item_id = self._tree.identify_row(event.y)
        col_id  = self._tree.identify_column(event.x)
        if not item_id or not col_id:
            return
        if "net" in self._tree.item(item_id, "tags"):
            return

        col_index   = int(col_id.replace("#", "")) - 1
        _, editable = self.COLUMNS[col_index]
        if not editable:
            return

        current_val = self._tree.item(item_id, "values")[col_index]
        if self.COLUMNS[col_index][0] == "Amount":
            current_val = current_val.replace("+", "").replace("-", "").replace("$", "").replace(",", "")

        self._editor = _CellEditor(
            tree=self._tree,
            item_id=item_id,
            col_index=col_index,
            current_value=current_val,
            on_commit=self._on_cell_commit,
        )

    def _on_cell_commit(self, item_id, col_index, new_value):
        values   = list(self._tree.item(item_id, "values"))
        col_name = self.COLUMNS[col_index][0]

        try:
            if col_name == "Date":
                date.fromisoformat(new_value)
            elif col_name == "Amount":
                amt = Decimal(new_value)
                if amt <= 0:
                    raise ValueError("Amount must be > 0")
            elif col_name == "Type":
                if new_value not in ("Income", "Expense"):
                    raise ValueError("Type must be Income or Expense")
        except (ValueError, InvalidOperation) as e:
            messagebox.showerror("Invalid Value", str(e))
            return

        if col_name == "Amount":
            tx_type = values[3]
            amt     = Decimal(new_value)
            values[col_index] = (f"+${amt:,.2f}" if tx_type == "Income"
                                 else f"-${amt:,.2f}")
        else:
            values[col_index] = new_value

        if col_name == "Type":
            tag = "income" if new_value == "Income" else "expense"
            self._tree.item(item_id, values=values, tags=(tag,))
        else:
            self._tree.item(item_id, values=values)

        self._save_row(item_id, values)

    def _save_row(self, item_id, values):
        all_items = self._tree.get_children()
        tx_items  = all_items[:-1]
        idx       = list(tx_items).index(item_id)
        raw       = self._raw_rows[idx]

        tx_id = _get_transaction_id(raw[0], raw[1], raw[3], raw[4])
        if tx_id is None:
            messagebox.showerror("Error", "Could not find transaction in database.")
            return

        try:
            new_date   = date.fromisoformat(str(values[0]))
            new_desc   = str(values[1]).strip()
            new_cat    = str(values[2]).strip()
            new_type   = str(values[3]).strip()
            new_amount = Decimal(
                str(values[4]).replace("+", "").replace("-", "")
                              .replace("$", "").replace(",", "")
            )
        except (ValueError, InvalidOperation) as e:
            messagebox.showerror("Parse Error", str(e))
            return

        success = _update_transaction(
            transaction_id=tx_id,
            tx_date=new_date,
            amount=new_amount,
            description=new_desc,
            tx_type=new_type,
            category_name=new_cat,
        )

        if success:
            self._raw_rows[idx] = (new_date, new_desc, new_cat,
                                   new_amount if new_type == "Income" else -new_amount,
                                   new_type, raw[5])
        else:
            messagebox.showerror("Error", "Failed to save changes to database.")
            self._refresh()


    def _get_selected(self):
        selected = self._tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select a row first.")
            return None, None

        item_id = selected[0]
        if "net" in self._tree.item(item_id, "tags"):
            messagebox.showwarning("Invalid Selection",
                                   "Please select a transaction row, not the net total.")
            return None, None

        all_items = self._tree.get_children()
        idx = list(all_items[:-1]).index(item_id)
        return item_id, self._raw_rows[idx]

    def _on_delete(self, _event=None):
        _, raw = self._get_selected()
        if raw is None:
            return

        confirmed = messagebox.askyesno(
            "Confirm Delete",
            f"Delete transaction:\n\n"
            f"  {raw[0]}  |  {raw[1]}  |  ${abs(raw[3]):,.2f}\n\n"
            "This cannot be undone.",
        )
        if not confirmed:
            return

        tx_id = _get_transaction_id(raw[0], raw[1], raw[3], raw[4])
        if tx_id is None:
            messagebox.showerror("Error", "Could not find transaction in database.")
            return

        if _delete_transaction(tx_id):
            self._refresh()
        else:
            messagebox.showerror("Error", "Failed to delete transaction.")
