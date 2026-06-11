from datetime import date
from enum import Enum
from typing import Optional
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

    weekday_mentioned: Optional[str] = Field(
        default=None,
        description=("The day of the week mentioned (e.g., 'Tuesday', 'Friday', 'Yesterday', 'Today'). Capitalized. "
        "Leave null if absolute date provided") 
        )
    weeks_ago_modifier: Optional[int] = Field(
        default=None,
        description=("How many weeks ago. 'this week' or 'today'=0, 'last week'=1, '2 weeks ago'=2, etc. "
        "Leave null if absolute date provided")
        )
    absolute_date_mentioned: Optional[str] = Field(
        default=None,
        description=("Any explicit calendar date string mentioned in the text(e.g., '22nd may', 'May 22', '12/25', '27-03'). "
        "Leave null if relative day like 'last week tuesday' is used instead")
    )
    transaction_type: TranType = Field(description="Must be 'Income' if money was earned, or 'Expense' if money was spent.")
    category: Category = Field(description="The closest matching subcategory from the allowed Enum list.")
    amount: float = Field(description="The numeric cost or earnings. Always return as a positive float number.")
    description: str = Field(description="A clean, concise 3-5 word summary of the transaction item (e.g., 'Chipotle dinner', 'Bi-weekly paycheck').")