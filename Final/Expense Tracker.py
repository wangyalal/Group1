import threading
import matplotlib
matplotlib.use('Agg')
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

#Displays Graphs
class graph_page(tb.Frame):
    def __init__(self, parent): 
        super().__init__(parent)
        title = tb.Label(self, text="Analytics")
        title.pack(anchor= "center", pady= 10)
        self._ledger_ref = None
        self.generate_analytics_chart()  

    def generate_analytics_chart(self):
            try:
                tx_data = tx.get_all_transactions()
            except Exception as e:
                print(f"Error fetching chart data: {e}")
                return

            df = pd.DataFrame(tx_data, columns=['Date', 'Description', 'Category', 'Amount', 'Type', 'Method'])
            df['Amount'] = df['Amount'].apply(lambda x: abs(float(x)))
            expenses_df = df[df['Type'] == 'Expense']
            final_data = expenses_df.groupby('Category')['Amount'].sum().sort_values(ascending=False)
            
            if final_data.empty:
                return

            fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
            modern_colors = ['#2962FF', '#00C853', '#FFAB40', '#4DD0E1', '#FDD835', '#AA00FF']
            
            ax.pie(
                final_data, 
                labels=final_data.index, 
                colors=modern_colors, 
                autopct='%1.1f%%', 
                startangle=90, 
                wedgeprops={'linewidth': 1.5, 'edgecolor': 'white'},
                textprops={'color': 'black', 'fontweight': 'bold', 'fontsize': 10},
                pctdistance=0.8
            )
            
            ax.set_title("Expenditure Breakdown by Category", fontsize=12, fontweight='bold', pad=15)
            ax.axis('equal') 
            ax.legend(title="Categories", labels=final_data.index, loc="best", fontsize=9)
            fig.tight_layout()

            for widget in self.winfo_children():
                widget.destroy()

            canvas = FigureCanvasTkAgg(fig, master=self)
            canvas_widget = canvas.get_tk_widget()
            canvas_widget.pack(fill="both", expand=True, padx=10, pady=10)
            canvas.draw()    
            self.generate_analytics_chart()     

#displays Transtion history
class transaction_page(tb.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        title = tb.Label(self, text="Transactions")
        title.pack(anchor="center", pady=10)
        self.ledger = LedgerFrame(self)
        self.ledger.pack(fill=BOTH, expand=YES)


      
        
#display currency page

#TODO make make a display where there is a connection error
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

        self.rates_table.column("Currency", anchor="center", width= 250)
        self.rates_table.column("Rate", anchor="center", width=250)

        self.rates_table.pack(fill=BOTH,expand= YES)

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
        self.left_side()
        self.right_side() 
        self.load_graph()
    

    #Right side Frame
    def right_side(self):
        #sets the workspace
        self.rightside = tb.Frame(self.root, width=400, bootstyle="secondary")
        self.rightside.configure(width= 400)
        self.rightside.pack(side="right", fill="y")
        self.rightside.pack_propagate(False)
        
        #right side contents
            #Notebook Creation Frame
        self.notebook = tb.Notebook(self.rightside, bootstyle="dark")
        self.notebook.pack(expand=True, fill=BOTH)
        self.notebook.configure(width=400)
            #TAB design section
        style=tb.Style()
        style.configure('TNotebook')
        style.configure('TNotebook.Tab', width=1000, anchor="center")
            #Creating the different Tabs
        tab2= tb.Frame(self.notebook)#AI Tab
        tab1= tb.Frame(self.notebook, height= 50)#Settings TAB

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
        frame_title = tb.Label (header_frame, text="Settings Panel", font=("helvetica", 16, "bold"))
        frame_title.pack()

        time_selec_container = tb.Frame(parent_frame)
        time_selec_container.pack(fill= BOTH, pady= 10) 

        screen_text_1 = tb.Label(time_selec_container, text= "Budgeting Timeframe:", font= ("helvetica", 10, "bold" ))
        screen_text_1.pack()
        self.from_date = tb.DateEntry(time_selec_container, dateformat="%Y-%m-%d")
        self.from_date.pack(side=LEFT)
        screen_text_2 = tb.Label(time_selec_container, text="TO", font=("helvetica", 8, "bold"))
        screen_text_2.pack(side=LEFT)
        self.to_date = tb.DateEntry(time_selec_container, dateformat="%Y-%m-%d")
        self.to_date.pack(side=LEFT)
        tb.Button(time_selec_container, text="Apply", bootstyle="primary", command=lambda: apply_custom_range(self._ledger_ref, self.from_date, self.to_date)).pack(side=LEFT, padx=(8, 0))

        


    
        button_container = tb.Frame(parent_frame)
        button_container.pack()
        delete_all_button = tb.Button(button_container, text="Delete Database", bootstyle= DANGER, command= "")
        delete_all_button.pack()
    


    
    def setup_ai_input_section(self, parent_frame):
        """Creates the natural language text entry area using a large text box."""
        input_frame = tb.Frame(parent_frame)
        input_frame.pack(fill=X, pady=(15, 10), padx=30)

        # Section Header
        lbl_section1 = tb.Label(input_frame, text="AI Transaction Parsing Agent", font=("Helvetica", 10, "bold"))
        lbl_section1.pack(anchor=W, pady=(0, 5), padx=10)

        # Instructions
        lbl = tb.Label(
            input_frame, 
            text="Enter transaction in plain English:\n(e.g., 'Bought a sofa last week tuesday $400')", 
            font=("Helvetica", 10),
            justify=LEFT,
            wraplength=320  
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
        lbl_section2 = tb.Label(self.review_frame, text="Review & Confirm Extracted Data", font=("Helvetica", 10, "bold"))
        lbl_section2.pack(anchor=W, pady=(0, 10), padx=10)

        # 1. Date Field
        lbl_date = tb.Label(self.review_frame, text="Date:", font=("Helvetica", 9, "bold"))
        lbl_date.pack(anchor=W, padx=10, pady=(5, 0))
        self.ai_selected_date = tb.DateEntry(self.review_frame, dateformat="%Y-%m-%d")
        self.ai_selected_date.pack(fill=X, pady=5, padx=10)
        
        # 2. Amount Field
        lbl_amt = tb.Label(self.review_frame, text="Amount ($):", font=("Helvetica", 9, "bold"))
        lbl_amt.pack(anchor=W, padx=10, pady=(5, 0))
        self.ai_enter_amount = tb.Entry(self.review_frame)
        self.ai_enter_amount.insert(0, "$0.00")
        self.ai_enter_amount.pack(fill=X, pady=5, padx=10)

        # 3. Streamlined Description Field
        lbl_desc = tb.Label(self.review_frame, text="Description:", font=("Helvetica", 9, "bold"))
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
        lbl_type = tb.Label(self.review_frame, text="Transaction Type:", font=("Helvetica", 9, "bold"))
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
        self.expense_categories = ["f", "Rent","Phone","Utilies","Commute","Leasuire","Other"]
        self.income_categories = ["Salary", "Bonus", "Other"]
        lbl_cat = tb.Label(self.review_frame, text="Category:", font=("Helvetica", 9, "bold"))
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

    # --- AI CORE LOGIC HANDLERS ---

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

        self.ai_save_btn.config(state=NORMAL)

    def on_parsing_failure(self, error_msg):
        self.progress_bar.stop()
        self.progress_bar.pack_forget()
        self.parse_btn.config(state=NORMAL)
        Messagebox.show_error(f"Failed to process statement:\n{error_msg}", title="AI Parser Error")

    def save_to_database(self):
        raw_amount = self.ai_enter_amount.get().replace("$", "")
        
        final_data = {
            "transaction_date": self.ai_selected_date.entry.get(),
            "transaction_type": self.selected_type,
            "category": self.ai_category_selc.get(),
            "amount": float(raw_amount or 0.0),
            "description": self.ai_enter_description.get("1.0", END).strip(),
            "entry_method": "Chat Box"
        }

        print("Saving record verified by user to database:", final_data)
        Messagebox.show_info("Transaction successfully saved to database!", title="Success")
        self.clear_form()

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
    app = Expense_Tracker_Main()
    app.run()

    
def generate_analytics_chart(self):
        try:
            tx_data = tx.get_all_transactions()
        except Exception as e:
            print(f"Error fetching chart data: {e}")
            return

        df = pd.DataFrame(tx_data, columns=['Date', 'Description', 'Category', 'Amount', 'Type', 'Method'])
        df['Amount'] = df['Amount'].apply(lambda x: abs(float(x)))
        expenses_df = df[df['Type'] == 'Expense']
        final_data = expenses_df.groupby('Category')['Amount'].sum().sort_values(ascending=False)
        
        if final_data.empty:
            return

        fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
        modern_colors = ['#2962FF', '#00C853', '#FFAB40', '#4DD0E1', '#FDD835', '#AA00FF']
        
        ax.pie(
            final_data, 
            labels=final_data.index, 
            colors=modern_colors, 
            autopct='%1.1f%%', 
            startangle=90, 
            wedgeprops={'linewidth': 1.5, 'edgecolor': 'white'},
            textprops={'color': 'black', 'fontweight': 'bold', 'fontsize': 10},
            pctdistance=0.8
        )
        
        ax.set_title("Expenditure Breakdown by Category", fontsize=12, fontweight='bold', pad=15)
        ax.axis('equal') 
        ax.legend(title="Categories", labels=final_data.index, loc="best", fontsize=9)
        fig.tight_layout()

        for widget in self.winfo_children():
            widget.destroy()

        canvas = FigureCanvasTkAgg(fig, master=self)
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(fill="both", expand=True, padx=10, pady=10)
        canvas.draw()
