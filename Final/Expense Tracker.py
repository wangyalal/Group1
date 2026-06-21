import threading
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import defaultdict
import transactions as tx
import pandas as pd
import ttkbootstrap as tb
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
from datetime import datetime
from ttkbootstrap.scrolled import ScrolledText
from ledger import LedgerFrame
from current_rates import currency_rate as cr
from parser import parse_natural_language_expense
from timeframe import apply_custom_range
from transactions import delete_all_data 
from timeframe import apply_cycle_day


#Displays Graphs
class graph_page(tb.Frame):
    def __init__(self, parent): 
        super().__init__(parent)
        self.title = tb.Label(self, text="Analytics")
        self.title.pack(anchor= "center", pady= 10)
        self._ledger_ref = None
        self.after(10, self.generate_analytics_chart)
    def generate_analytics_chart(self):
            self.update_idletasks()
            try:
                tx_data = tx.get_all_transactions()
            except Exception as e:
                print(f"Error fetching chart data: {e}")
                return

            # --- 1. Filter and Group Data ---
            df = pd.DataFrame(tx_data, columns=['Date', 'Description', 'Category', 'Amount', 'Type'])
            df['Amount'] = df['Amount'].apply(lambda x: abs(float(x)))

            # Expenses Data Split
            expenses_df = df[df['Type'] == 'Expense']
            final_expense_data = expenses_df.groupby('Category')['Amount'].sum().sort_values(ascending=False)

            # Income Data Split
            income_df = df[df['Type'] == 'Income']
            final_income_data = income_df.groupby('Category')['Amount'].sum().sort_values(ascending=False)

            # Safety Check: If there's absolutely no data at all, do nothing
            if final_expense_data.empty and final_income_data.empty:
                return


            for widget in self.winfo_children():
                if widget != self.title: 
                    widget.destroy()
            chart_container = tb.Frame(self)
            chart_container.pack(fill=BOTH, expand= True)
            chart_container.pack_propagate(False)
            chart_container.update_idletasks()

            dpi = 100
            container_w = self.winfo_width()
            container_h = self.winfo_height()

            fig_w = max(container_w -20, 400) / dpi
            fig_h = max(container_h -20, 300) / dpi
            # --- 2. Create Side-by-Side Subplots (1 Row, 2 Columns) ---
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(fig_w, fig_h), dpi=dpi)
            modern_colors = ['#2962FF', '#00C853', '#FFAB40', '#4DD0E1', '#FDD835', '#AA00FF']

            # --- 3. Plot Left Graph: Expenditure Breakdown ---
            if not final_expense_data.empty:
                ax1.pie(
                    final_expense_data,
                    labels=final_expense_data.index,
                    colors=modern_colors,
                    autopct='%1.1f%%',
                    startangle=90,
                    radius = 0.8,
                    wedgeprops={'linewidth': 1.5, 'edgecolor': 'white'},
                    textprops={'color': 'black', 'fontweight': 'bold', 'fontsize': 9},
                    pctdistance=0.75
                )
                ax1.set_title("Expenditure Breakdown", fontsize=11, fontweight='bold', pad=10)
                ax1.axis('equal')
            else:
                ax1.text(0.5, 0.5, 'No Expense Data', ha='center', va='center', fontsize=12, color='gray')
                ax1.axis('off')

            # --- 4. Plot Right Graph: Income Breakdown ---
            if not final_income_data.empty:
                ax2.pie(
                    final_income_data,
                    labels=final_income_data.index,
                    colors=modern_colors,
                    autopct='%1.1f%%',
                    startangle=90,
                    radius = 0.8,
                    wedgeprops={'linewidth': 1.5, 'edgecolor': 'white'},
                    textprops={'color': 'black', 'fontweight': 'bold', 'fontsize': 9},
                    pctdistance=0.75
                )
                ax2.set_title("Income Breakdown", fontsize=11, fontweight='bold', pad=10)
                ax2.axis('equal')
            else:
                ax2.text(0.5, 0.5, 'No Income Data', ha='center', va='center', fontsize=12, color='gray')
                ax2.axis('off')

            # --- 5. Embed Into Tkinter Window Frame ---

            canvas = FigureCanvasTkAgg(fig, master=chart_container)
            canvas_widget = canvas.get_tk_widget()
            canvas_widget.pack(fill="both", expand=True, padx=10, pady=10)
            canvas.draw()

            def on_resize(event):
                w = event.width - 40 / 100
                h = event.height - 40 / 100
                if 0.5 < w < 50 and 0.5 < h < 50:
                    fig.set_size_inches(w, h)
                    fig.tight_layout()
                    canvas.draw_idle()

            chart_container.bind("<Configure>", on_resize)

            # Force initial sizing after window is fully rendered
            self.after(10, lambda: on_resize(type('E', (), {
                'width': self.winfo_width(),
                'height': self.winfo_height() -80
            })()))

#displays Transtion history
class transaction_page(tb.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        title = tb.Label(self, text="Transactions")
        title.pack(anchor="center", pady=10)
        self.ledger = LedgerFrame(self, app_reference = parent)
        self.ledger.pack(fill=BOTH, expand=YES)


      
        
#display currency page

class currency_page(tb.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        title = tb.Label(self, text="Currency", font=("helvetica", 16, "bold"))
        title.pack(anchor="center", pady=10)
        refresh_btn = tb.Button(self, text="Refresh Page", command= self.load_table_data, bootstyle= "primary")
        refresh_btn.pack(padx= "5", pady= "5", side= "top")
        table_frame = tb.Frame(self)
        table_frame.pack(fill= BOTH, expand= YES, padx=10, pady=10)
        
        table_layout = ("Currency", "Rate")
        self.rates_table = tb.Treeview(table_frame, columns=table_layout, show="headings")
        self.rates_table.heading("Currency", text="Currency")
        self.rates_table.heading("Rate", text="Today's Exchange Rate", anchor="center")

        self.rates_table.column("Currency", anchor="center", width=150)
        self.rates_table.column("Rate", anchor="center", width=150)

        self.rates_table.pack(fill=BOTH, expand=YES)

        style = tb.Style()
        style.configure("Treeview.Heading", font=("Helvetica", 14, "bold"),
                         background=style.colors.primary, foreground= "white")
        style.configure("Treeview", font=("Helvetica", 12, "bold"), rowheight=35,
                        foreground="#000000")

        self.load_table_data()


    def load_table_data(self):
        #clears data so that it can be freshed
        for row in self.rates_table.get_children():
            self.rates_table.delete(row)

        try: 
            rates = cr()
        except Exception as e:
            print(f"Failed to Fetch rates: {e}") 
            rates = {}
        
        currency_names = {
            "USD": "US Dollar",
            "JPY": "Japanese Yen",
            "EUR": "EURO",
            "GDP": "British Pound",
            "AUD": "Australian Dollar",
            "CAD": "Canadian Dollar",
            "CNY": "Chinese Yan",
            "KRW": "South Korean Won"
        }


        for currency_code, full_name in currency_names.items():
            if currency_code in rates:
                rate_value = rates[currency_code]
                twd_exchange_rate = 1 / rate_value
                formatted_rate_string = f"1 {currency_code} = {twd_exchange_rate:.2f} TWD"
                self.rates_table.insert("", "end" , values=(full_name, formatted_rate_string))



#main window
class Expense_Tracker_Main:
    def __init__(self) -> None:
        #window initialization and theme selection
        self.root = tb.Window(themename="morph")
        self.root.title("Expense Tracker")
        self.root.geometry("1200x850")
        self.current_pages = None
        self.transaction_type = "Expense"
        self.current_parsed_data = None
        self.selected_type = None
        self.right_side()
        self.left_side()       
        self.load_transactions()
    

    #Right side Frame
    def right_side(self):
        #sets the workspace
        self.rightside = tb.Frame(self.root, width=350, bootstyle="secondary")
        self.rightside.pack(side="right", fill="y", expand= False)
        self.rightside.pack_propagate(False)
        
        #right side contents
            #Notebook Creation Frame
        self.notebook = tb.Notebook(self.rightside, bootstyle="dark")
        self.notebook.pack(side = "right", expand=True, fill=BOTH)
            #TAB design section
        style=tb.Style()
        style.configure('TNotebook.Tab',
                         width=100, anchor="center",
                           font = ("Helvetica", 10, "bold"),
                           padding= (0,25))
            #Creating the different Tabs
        tab2= tb.Frame(self.notebook) #AI Tab
        tab1= tb.Frame(self.notebook, height= 50) #Settings TAB

            #Packing Tabs 
        self.notebook.add(tab2, text="Add Transaction")
        self.notebook.add(tab1, text="Settings")
        
            #Container within the TABS
        #Add Transactions Tabs SetUp
        self.AI_container = tb.Frame(tab2)
        self.AI_container.pack(fill=BOTH, expand=YES, side=TOP)
        self.setup_ai_input_section(self.AI_container)
        self.setup_ai_review_section(self.AI_container)
        #Settings Tab Setup
        self.settings_container = tb.Frame(tab1)
        self.settings_container.pack(fill= BOTH, expand= YES, side= TOP)
        self.settings_panel(self.settings_container)



    def settings_panel(self, parent_frame):
        header_frame = tb.Frame(parent_frame)
        header_frame.pack(fill=X, pady= (15,10), padx= 30)

            #container buttons rollover layout
        time_selec_container = tb.Frame(parent_frame)
        time_selec_container.pack(fill= BOTH, pady= 10) 

        screen_text_1 = tb.Label(time_selec_container, text= "Budgeting Timeframe:", font= ("helvetica", 12, "bold"),
                                 foreground= "#000000")
        screen_text_1.pack(side =  TOP, padx= (0,15), anchor= W)

        screen_text_2 = tb.Label(time_selec_container, text= "Enter Budget Rollover Date (1st-28th)",
                                  font= ("helvetica", 10), foreground= "#000000")
        screen_text_2.pack(side= TOP,)
        rollover_date = tb.StringVar()
        budget_rollover = tb.Entry(time_selec_container, textvariable= rollover_date)
        budget_rollover.pack(side= TOP, padx= 50, anchor= CENTER, pady= 5)

        confirm_rollover = tb.Button(time_selec_container, text= "Confirm", command= lambda: self.confirm_date(rollover_date), bootstyle="primary")
        confirm_rollover.pack(side= TOP, fill= X, padx= 10)
      

        #continer for database layout
        button_container = tb.Frame(parent_frame)
        button_container.pack(fill=BOTH, pady= 40)
        screen_text_3 = tb.Label(button_container, text = "Delete all data in the Databse:",
                                  font= ("helvetica", 12, "bold"), foreground= "#000000")
        screen_text_3.pack(side= TOP, anchor= "w")
        delete_all_button = tb.Button(button_container, text="Delete All", bootstyle= DANGER, command=self.confirm_deletion)
        delete_all_button.pack(side= TOP, fill= X, padx= 10)
    
    def confirm_date(self, date):
        apply_cycle_day(self._ledger_ref, date)
        day = self._ledger_ref._cycle_start_day
        #to take the current date that is currently set

    def confirm_deletion(self):
        alert_message = "Delete all transactions permanentely? \n\n This action cannot be undone."
        answer = Messagebox.yesno(
        title = "Confirm Deletion",
        message= alert_message,
        parent = self.root,
        alert=True)

        if answer == "Yes":
            delete_all_data()
            if hasattr(self,"_ledger_ref") and self._ledger_ref:
                self._ledger_ref._refresh()

    def setup_ai_input_section(self, parent_frame):
        """Creates the natural language text entry area using a large text box."""
        input_frame = tb.Frame(parent_frame)
        input_frame.pack(fill=X, pady=(15, 10), padx=30)

        # Section Header
        lbl_section1 = tb.Label(input_frame, text="AI Transaction Parsing Agent",
                                 font=("Helvetica", 10, "bold"), foreground= "#000000")
        lbl_section1.pack(anchor=W, pady=(0, 5), padx=10)

        # Instructions
        lbl = tb.Label(
            input_frame, 
            text="Enter transaction in plain English:\n(e.g., 'Bought a sofa last week tuesday $400')", 
            font=("Helvetica", 10),
            justify=LEFT,
            wraplength=320,
            foreground= "#000000"  
        )
        lbl.pack(anchor=W, pady=(5, 5), padx=10)

        # ScrolledText to make it vertically larger (height=3 lines)
        self.user_input_entry = ScrolledText(
            input_frame, 
            font=("Helvetica", 10), 
            height=3, 
            autohide=True, 
            wrap="word"
        )
        self.user_input_entry.pack(fill=X, pady=5, padx=10)
        
        # Bind enter key to execute when pressing Enter.
        self.user_input_entry.bind("<Return>", lambda event: self.trigger_parsing_from_entry())

        # Action Buttons Wrapper
        btn_wrapper = tb.Frame(input_frame)
        btn_wrapper.pack(fill=X, pady=5, padx=10)

        self.parse_btn = tb.Button(btn_wrapper, text="Parse Statement", bootstyle=PRIMARY, command=self.start_parsing_thread)
        self.parse_btn.pack(side=RIGHT)

        # Loading Progress Bar
        self.progress_bar = tb.Progressbar(input_frame, bootstyle=INFO, mode='indeterminate')

    def setup_ai_review_section(self, parent_frame):
        """Creates data review fields styled flat, matching the Manual tab."""
        self.review_frame = tb.Frame(parent_frame)
        self.review_frame.pack(fill=X, pady=(10, 15), padx=30)

        # Section Header
        lbl_section2 = tb.Label(self.review_frame, text="Review & Confirm Extracted Data",
                                 font=("Helvetica", 10, "bold"), foreground= "#000000")
        lbl_section2.pack(anchor=W, pady=(0, 10), padx=10)

        # 1. Date Field
        lbl_date = tb.Label(self.review_frame, text="Date:", font=("Helvetica", 9, "bold"), foreground= "#000000")
        lbl_date.pack(anchor=W, padx=10, pady=(5, 0))
        self.ai_selected_date = tb.DateEntry(self.review_frame, dateformat="%Y-%m-%d")
        self.ai_selected_date.pack(fill=X, pady=5, padx=10)
        
        # 2. Amount Field
        lbl_amt = tb.Label(self.review_frame, text="Amount ($):", font=("Helvetica", 9, "bold"), foreground= "#000000")
        lbl_amt.pack(anchor=W, padx=10, pady=(5, 0))
        self.ai_enter_amount = tb.Entry(self.review_frame)
        self.ai_enter_amount.insert(0, "$0.00")
        self.ai_enter_amount.pack(fill=X, pady=5, padx=10)

        # 3. Streamlined Description Field
        lbl_desc = tb.Label(self.review_frame, text="Description:", font=("Helvetica", 9, "bold"), foreground= "#000000")
        lbl_desc.pack(anchor=W, padx=10, pady=(5, 0))
        
        # 4 line description box
        self.ai_enter_description = ScrolledText(
            self.review_frame, 
            font=("Helvetica", 10), 
            height=4, 
            autohide=True, 
            wrap="word"
        )
        self.ai_enter_description.pack(fill=X, pady=5, padx=10)

        # 4. Transaction type Selection Buttons
        lbl_type = tb.Label(self.review_frame, text="Transaction Type:", font=("Helvetica", 9, "bold"), foreground= "#000000")
        lbl_type.pack(anchor=W, padx=10, pady=(5, 0))
        
        button_frame = tb.Frame(self.review_frame)
        button_frame.pack(fill=X, pady=5, padx=10)
        
        self.ai_income_btn = tb.Button(button_frame, text="Income", bootstyle="secondary",
                                       command=lambda: self.set_review_type("Income"))
        self.ai_income_btn.pack(side=LEFT, expand=True, padx=(0, 5), fill=X)
        
        self.ai_expense_btn = tb.Button(button_frame, text="Expense", bootstyle="secondary", 
                                        command=lambda: self.set_review_type("Expense"))
        self.ai_expense_btn.pack(side=LEFT, expand=True, padx=(5, 0), fill=X)   

        # 5. Category Selection Dropdown
        self.expense_categories = ["Food", "Rent","Phone","Utilies","Commute","Leasuire","Other"]
        self.income_categories = ["Salary", "Bonus", "Freelance/Side-gig", "Investments/Interest", "Other"]
        lbl_cat = tb.Label(self.review_frame, text="Category:", font=("Helvetica", 9, "bold"), foreground= "#000000")
        lbl_cat.pack(anchor=W, padx=10, pady=(5, 0))
        
        self.ai_category_selc = tb.Combobox(self.review_frame, values=self.expense_categories, state="readonly")
        self.ai_category_selc.pack(fill=X, pady=5, padx=10)
        self.ai_category_selc.set("Select a category")

        # Core Action Buttons Block
        action_frame = tb.Frame(self.review_frame)
        action_frame.pack(fill=X, pady=15, padx=10)

        self.ai_save_btn = tb.Button(action_frame, text="Add Transaction", bootstyle=SUCCESS, state=DISABLED, command=self.save_to_database)
        self.ai_save_btn.pack(side=RIGHT, padx=(5, 0))

        self.ai_clear_btn = tb.Button(action_frame, text="Clear", bootstyle=SECONDARY, command=self.clear_form)
        self.ai_clear_btn.pack(side=RIGHT, padx=(0, 5))

        #validation function input bindings
        self.ai_selected_date.bind("<FocusOut>", lambda e: self.validate_form())
        self.ai_enter_amount.bind("<KeyRelease>", lambda e: self.validate_form())
        self.ai_enter_description.bind("<KeyRelease>", lambda e: self.validate_form())
        self.ai_category_selc.bind("<<ComboboxSelected>>", lambda e: self.validate_form())
            #AI CORE LOGIC HANDLERS

    def set_review_type(self, trans_type):
        self.selected_type = trans_type
        if trans_type == "Income":
            self.ai_income_btn.config(bootstyle="success")
            self.ai_expense_btn.config(bootstyle="secondary")
            self.ai_category_selc.config(values=self.income_categories)
        else:
            self.ai_income_btn.config(bootstyle="secondary")
            self.ai_expense_btn.config(bootstyle="danger")
            self.ai_category_selc.config(values=self.expense_categories)
        self.validate_form()

    def trigger_parsing_from_entry(self):
        self.start_parsing_thread()
        return "break"  

    def start_parsing_thread(self):
        text = self.user_input_entry.get("1.0", END).strip()
        if not text:
            return
        
        self.parse_btn.config(state=DISABLED)
        self.ai_save_btn.config(state=DISABLED)
        self.progress_bar.pack(fill=X, pady=5, padx=10)
        self.progress_bar.start()

        threading.Thread(target=self.async_parse_worker, args=(text,), daemon=True).start()

    def async_parse_worker(self, text):
        try:
            parsed_json = parse_natural_language_expense(text)
            self.root.after(0, self.on_parsing_success, parsed_json)
        except Exception as e:
            self.root.after(0, self.on_parsing_failure, str(e))

    def on_parsing_success(self, data):
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.parse_btn.config(state=NORMAL)

        self.current_parsed_data = data

        # Update Date Entry Widget
        target_date = data.get("transaction_date", "")
        if target_date:
            self.ai_selected_date.entry.delete(0, END)
            self.ai_selected_date.entry.insert(0, target_date)

        # Update Amount Field
        self.ai_enter_amount.delete(0, END)
        self.ai_enter_amount.insert(0, f"${float(data.get('amount', 0)):.2f}")

        # Update Description Entry Field
        self.ai_enter_description.delete("1.0", END)
        self.ai_enter_description.insert("1.0", data.get("description", ""))

        # Set Type & Categories
        parsed_type = data.get("transaction_type", "Expense")
        self.set_review_type(parsed_type)

        parsed_cat = data.get("category", "Other")
        self.ai_category_selc.set(parsed_cat)

        self.validate_form()

    def on_parsing_failure(self, error_msg):
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.parse_btn.config(state=NORMAL)
        Messagebox.show_error(f"Failed to process statement:\n{error_msg}", title="AI Parser Error")

    def save_to_database(self):
        raw_amount = self.ai_enter_amount.get().replace("$", "")
        
        input_status=tx.add_transaction(self.ai_selected_date.entry.get(),
                                float(raw_amount or 0.0),
                                self.ai_enter_description.get("1.0", END).strip(),
                                self.selected_type,
                                self.ai_category_selc.get())
        if input_status:
            Messagebox.show_info(message="Transaction successfully saved to database!", title="Success")
            if hasattr(self,"_ledger_ref") and self._ledger_ref:
                self._ledger_ref._refresh()
        else:
            Messagebox.show_error(message="Database insertion error! Transaction not added.", title="Error")

        self.clear_form()

    def validate_form(self):
        try:
            date_val = self.ai_selected_date.entry.get()
            datetime.strptime(date_val, "%Y-%m-%d")
            date_ok= True
        except ValueError:
            date_ok = False

        try:
            amount_val = float(self.ai_enter_amount.get().replace("$",""))
            amt_ok = amount_val > 0
        except ValueError:
            amt_ok = False

        type_ok = getattr(self, "selected_type", None) is not None
        category_val = self.ai_category_selc.get()
        cat_ok = category_val and category_val != "Select a category"

        valid = date_ok and amt_ok and type_ok and cat_ok
        self.ai_save_btn.config(state=NORMAL if valid else DISABLED)

    def clear_form(self):
        self.user_input_entry.delete("1.0", END)
        self.ai_selected_date.entry.delete(0, END)
        self.ai_enter_amount.delete(0, END)
        self.ai_enter_amount.insert(0, "$0.00")
        self.ai_enter_description.delete("1.0", END)
        self.ai_category_selc.set("Select a category")
        self.ai_income_btn.config(bootstyle="secondary")
        self.ai_expense_btn.config(bootstyle="secondary")
        self.ai_save_btn.config(state=DISABLED)
        self.current_parsed_data = None
        self.selected_type = None

    #Cleans and changes display for the left side of the main window
    def clean_pages(self):
        if self.current_pages is not None:
            self.current_pages.destroy()

    def load_graph(self):
        self.clean_pages()
        self.current_pages = graph_page(self.display_container)
        self.current_pages.pack(fill= BOTH, expand= YES)
        
 
    def load_transactions(self):
        self.clean_pages()
        self.current_pages = transaction_page(self.display_container)
        self.current_pages.pack(fill= BOTH, expand= YES)
        self._ledger_ref = self.current_pages.ledger
        
    def load_currencies(self):
        self.clean_pages()
        self.current_pages = currency_page(self.display_container)
        self.current_pages.pack(fill= BOTH, expand= YES)


    #Left side Frame
    def left_side(self):
        #sets the workspace
        self.leftside = tb.Frame(self.root, bootstyle="primary")
        self.leftside.pack(side='left', fill= BOTH, expand=YES)

        #Left side content
        #NAV BAR FRAME
        self.nav_bar= tb.Frame(self.leftside, bootstyle="dark", height=50) 
        self.nav_bar.pack(side = "top", fill="x")
        self.nav_bar.pack_propagate(False)

        #BUTTONS IN NAV BAR
        self.graph_btn = tb.Button(self.nav_bar, text="Graphs",command= self.load_graph, bootstyle="dark-flat")
        self.graph_btn.pack(side="left",fill= "y", padx=10 )

        self.transactions_button = tb.Button(self.nav_bar, text="Transactions", command= self.load_transactions, bootstyle="dark-flat")
        self.transactions_button.pack(side="left", fill="y", padx=10)

        self.currency_button = tb.Button(self.nav_bar, text="Curriences", command= self.load_currencies, bootstyle="dark-flat")
        self.currency_button.pack(side="left", fill="y", padx=10)
        
        self.display_container = tb.Frame(self.leftside, bootstyle="primary")
        self.display_container.pack(fill="both", expand= YES, padx= 25, pady=25) 

    def set_cat_type(self, mode, inc_btn, exp_btn): 
        self.transaction_type = mode

        if mode == "Income":
            inc_btn.configure(bootstyle = "success")
            exp_btn.configure(bootstyle = "secondary")
            self.category_selc['values'] = self.income_categories
        else: 
            inc_btn.configure(bootstyle ="secondary")
            exp_btn.configure(bootstyle = "danger")
            self.category_selc['values'] = self.expense_categories
        
        self.category_selc.set("select a category...")


    def run(self):
        self.root.mainloop()

if  __name__ == "__main__":
    import ctypes
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(0)
    except Exception:
        pass 

    app = Expense_Tracker_Main()
    app.run()

