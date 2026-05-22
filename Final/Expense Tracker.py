
import ttkbootstrap as tb
from ttkbootstrap.constants import YES, BOTH
from datetime import datetime
from ttkbootstrap.scrolled import ScrolledText


#Displays Graphs
class graph_page(tb.Frame):
    def __init__(self, parent): 
        super().__init__(parent)
        title = tb.Label(self, text="Analytics")
        title.pack(anchor= "center", pady= 10)

        placeholder = tb.Label(self, text="[ Graph visualization will render here ]", font = ("helvetica", 16, "bold")  )
        placeholder.pack(pady=50)       

#displays Transtion history
class transaction_page(tb.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        title = tb.Label(self, text="Transactions")
        title.pack(anchor="center", pady=10)

        placeholder = tb.Label(self, text="[ Graph visualization will render here ]", font=("helvetica", 16, "bold"))
        placeholder.pack(pady=50)
      
        
#display settings page
class settings_page(tb.Frame): 
    def __init__(self, parent):
        super().__init__(parent)
        title = tb.Label(self, text="Settings")
        title.pack(anchor="center", pady=10)

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
        self.right_side()
        self.left_side() 
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

        #TODO make the buttons here:
        self.Tab2=tb.Label(tab1, text ="Date", font=("helvetica", 12))
        self.Tab2.pack()#I'm still working on the heading. ignore it

        self.selecte_date=tb.DateEntry(tab1, dateformat= "%Y-%m-%d") #Date entry field
        self.selecte_date.pack(fill="x", pady=10, padx= 30,)
        
        self.enter_amount = tb.Entry(tab1) #Amount entry field
        self.enter_amount.insert(0, "$0.00")
        self.enter_amount.pack(fill="x", pady= 10, padx = 30)

        self.description_box = tb.Text(tab1, height = 8 ) #description entry field
        self.description_box.pack (fill="both", pady=0, padx= 30,)

        income_btn = tb.Button(tab1, text= "Income", bootstyle="secondary") #Set Income as type
        income_btn.pack(side="left", pady=5, padx= 30, fill="x")

        expense_btn = tb.Button(tab1, text="Expense",bootstyle= "danger") #set Expense as type 
        expense_btn.pack(side="left", pady=5, padx= 30, fill="x")
        
        add_transaction = tb.Button(tab1, text="Add Transaction", bootstyle="primary") #Add Transaction
        add_transaction.pack()



        tab2= tb.Frame(self.notebook)#tab two content
        #TODO make the layouts buttons here:
        self.Tab2=tb.Label(tab2, text = "Chat Box play holder", font=("helvetica", 12))
        self.Tab2.pack(expand=True)


        #This would have to be set to lock rewrite when you start working on it
        self.text_display = ScrolledText(tab2, 
            padding= 10,
            height = 10, 
            autohide= True, 
            wrap = "word"
        ) 

        
        self.text_display.pack(fill=BOTH, expand=True, padx=10, pady=10)
        self.text_input = tb.Entry(tab2, textvariable="Type something...")
        self.text_input.pack(fill=BOTH, expand= True, padx=5, pady=5  )


        #calling both tabs to run
        self.notebook.add(tab1, text="Manual")
        self.notebook.add(tab2, text="Chat Box")
    

    #Cleans and changes display for the left side display
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
        #NAV BAR
        self.nav_bar= tb.Frame(self.leftside) 
        self.nav_bar.pack(side = "top", fill="x", pady=(0))

        self.graph_btn = tb.Button(self.nav_bar, text="Graphs",command= self.load_graph)
        self.graph_btn.pack(side="left", anchor= "center")

        self.transactions_button = tb.Button(self.nav_bar, text="Transactions", command= self.load_transactions)
        self.transactions_button.pack(side="left", anchor= "center")

        self.settings_button = tb.Button(self.nav_bar, text="Settings", command= self.load_settings)
        self.settings_button.pack(side="left", anchor= "center")
        
        self.display_container = tb.Frame(self.leftside, bootstyle="primary")
        self.display_container.pack(fill="both", expand= YES) 


    def run(self):
        self.root.mainloop()

if  __name__ == "__main__":
    app = Expense_Tracker_Main()
    app.run()