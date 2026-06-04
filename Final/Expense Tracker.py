import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import defaultdict
import transactions as tx
import pandas as pd
import ttkbootstrap as tb
from ttkbootstrap.constants import YES, BOTH
from datetime import datetime
from ttkbootstrap.scrolled import ScrolledText
from ledger import LedgerFrame


#Displays Graphs
class graph_page(tb.Frame):
    def __init__(self, parent): 
        super().__init__(parent)
        title = tb.Label(self, text="Analytics")
        title.pack(anchor= "center", pady= 10)

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
        LedgerFrame(self).pack(fill=BOTH, expand=YES)
      
        
#display settings page
class settings_page(tb.Frame): 
    def __init__(self, parent):
        super().__init__(parent)
        title = tb.Label(self, text="Settings")
        title.pack(anchor="center", pady=10)

        #TODO Please remove this and add settings functions
        placeholder = tb.Label(self, text="[ Settings Page ]", font=("helvetica", 16, "bold"))
        placeholder.pack(pady= 50 )

#main window
class Expense_Tracker_Main:
    def __init__(self) -> None:
        #window initialization and theme selection
        self.root = tb.Window(themename="morph")
        self.root.title("Expense Tracker")
        self.root.geometry("1200x600")
        self.current_pages = None
        self.transaction_type = "Expense"
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
            #tab section
        self.notebook = tb.Notebook(self.rightside, bootstyle="dark") #entire space
        self.notebook.pack(expand=True, fill=BOTH)
        self.notebook.configure(width=400)

        style=tb.Style()#Top Tabs
        style.configure('TNotebook')
        style.configure('TNotebook.Tab', width=1000, anchor="center")

   
        tab1= tb.Frame(self.notebook)#tab one content

        #Date entry section
        self.selecte_date=tb.DateEntry(tab1, dateformat= "%Y-%m-%d")
        self.selecte_date.pack(fill="x", pady=10, padx= 30,)
        
        #amount entry section
        self.enter_amount = tb.Entry(tab1) #Amount entry field
        self.enter_amount.insert(0, "$0.00")
        self.enter_amount.pack(fill="x", pady= 10, padx = 30)

        #description sections  
        self.description_box = ScrolledText(tab1, height = 8) #description entry field
        self.description_box.insert("1.0", "Enter Description")
        self.description_box.pack (fill="both", pady=0, padx= 30,)

        #income and expsense type selcetion
        button_frame = tb.Frame(tab1)
        button_frame.pack(fill="x", pady= 10, padx= 30)
        income_btn = tb.Button(button_frame, text= "Income", bootstyle="secondary",
                            command= lambda: self.set_cat_type("Income", income_btn, expense_btn)) #Set Income as type
        income_btn.pack(side="left", expand= True, pady=5, padx= (5,0), fill="x")
        expense_btn = tb.Button(button_frame, text="Expense",bootstyle= "danger", 
                            command= lambda: self.set_cat_type("Expense", income_btn, expense_btn)) #set Expense as type 
        expense_btn.pack(side="left", expand= True, pady=5, padx= (5,0), fill="x")   

        #category drop down box
        self.expense_categories = ["Food", "Rent","Phone","Utilies","Commute","Leasuire","Other"]
        self.income_categories = ["Salary", "Bonus", "Other"]
        cat_input_frame= tb.Frame(tab1)
        cat_input_frame.pack(fill="x", pady=5, padx= 30)
        self.category_selc=tb.Combobox(cat_input_frame, values=self.expense_categories)
        self.category_selc.pack(side="left", expand=True, fill= "x")
        self.category_selc.set("Select a category")

        add_transaction = tb.Button(tab1, text="Add Transaction", bootstyle="primary") #Add Transaction
        add_transaction.pack(fill= "x",padx= (30, 25), pady=(15,0) )

        tab2= tb.Frame(self.notebook)#tab two content
        #TODO make the layouts buttons here:
        self.Tab2=tb.Label(tab2, text = "Chat Box place holder", font=("helvetica", 12))
        self.Tab2.pack(expand=True)


        #This would have to be set to lock. rewrite when you start working on it
        self.text_display = ScrolledText(tab2, 
            padding= 10,
            height = 10, 
            autohide= True, 
            wrap = "word"
        ) 

        
        self.text_display.pack(fill=BOTH, expand=True, padx=10, pady=10)
        self.text_input = tb.Entry(tab2, textvariable="Type Something...")
        self.text_input.pack(fill="x", expand= False, padx=5, pady=5  )


        #calling both tabs to run
        self.notebook.add(tab1, text="Manual")
        self.notebook.add(tab2, text="Chat Box")
    

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
         
    def load_settings(self):
        self.clean_pages()
        self.current_pages = settings_page(self.display_container)
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

        self.settings_button = tb.Button(self.nav_bar, text="Settings", command= self.load_settings, bootstyle="dark-flat")
        self.settings_button.pack(side="left", fill="y", padx=10)
        
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
