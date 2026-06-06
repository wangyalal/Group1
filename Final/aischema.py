from datetime import date
from enum import Enum
from pydantic import BaseModel, Field

class TranType(str, Enum):
    INCOME = "Income"
    EXPENSE = "Expense"

class Category(str, Enum):
    # Expense Categories
    FOOD = "Food"
    RENT = "Rent"
    PHONE = "Phone"
    COMMUTE = "Commute"
    UTILITIES = "Utilities"
    LEISURE = "Leisure"
    
    # Income Categories
    SALARY = "Salary"
    BONUS = "Bonus"
    FREELANCE = "Freelance/Side-gig"
    INVESTMENT = "Investments/Interest"
    
    # Fallback
    OTHER = "Other"

class TransactionData(BaseModel):
    weekday_mentioned: str = Field(default="Today", description="The day of the week mentioned (e.g., 'Tuesday', 'Friday', 'Yesterday', 'Today'). Capitalized.")
    weeks_ago_modifier: int = Field(default=0, description="How many weeks ago. 'this week' or 'today'=0, 'last week'=1, '2 weeks ago'=2, etc.")
    transaction_type: TranType = Field(description="Must be 'Income' if money was earned, or 'Expense' if money was spent.")
    category: Category = Field(description="The closest matching subcategory from the allowed Enum list.")
    amount: float = Field(description="The numeric cost or earnings. Always return as a positive float number.")
    description: str = Field(description="A clean, concise 3-5 word summary of the transaction item (e.g., 'Chipotle dinner', 'Bi-weekly paycheck').")
    entry_method: str = Field(default="Chat Box", description="The transaction data input method.")