from datetime import date
from decimal import Decimal, InvalidOperation
from database import insert_transaction, get_db_connection


def validate_amount(amount):
    """
    Checks if the amount is a valid positive number.
    """

    try:
        amount = Decimal(str(amount))
    except InvalidOperation:
        raise ValueError("Amount must be a valid number.")

    if amount <= 0:
        raise ValueError("Amount must be greater than 0.")

    return amount


def add_transaction(transaction_date, amount, description, tx_type, entry_method, category):
    """
    Adds a transaction of either type Income or Expense, along with respective category of trans type
    """

    if transaction_date == "" or transaction_date is None:
        transaction_date = date.today()

    amount = validate_amount(amount)

    if description is None or description.strip() == "":
        raise ValueError("Description cannot be empty.")

    if entry_method is None or entry_method.strip() == "":
        raise ValueError("Entry method cannot be empty.")

    insert_transaction(
        transaction_date,
        amount,
        description.strip(),
        tx_type,
        category
    )

    return "Transaction added successfully."


def get_all_transactions():
    """
    Gets all transactions from the database.
    Used to display transactions in the GUI table.
    """

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            t.transaction_date,
            t.description,
            c.name AS category,
            CASE
                WHEN t.transaction_type = 'Expense' THEN -ABS(t.amount)
                ELSE ABS(t.amount)
            END AS display_amount,
            t.transaction_type,
            t.entry_method
        FROM transactions t
        LEFT JOIN categories c ON t.category_id = c.id
        ORDER BY t.transaction_date DESC, t.id DESC;
    """)

    transactions = cursor.fetchall()

    cursor.close()
    conn.close()

    return transactions


def get_total_income():
    """
    Calculates total income from the database.
    """

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COALESCE(SUM(ABS(amount)), 0)
        FROM transactions
        WHERE transaction_type = 'Income';
    """)

    total_income = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return total_income


def get_total_expenses():
    """
    Calculates total expenses from the database.
    """

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COALESCE(SUM(ABS(amount)), 0)
        FROM transactions
        WHERE transaction_type = 'Expense';
    """)

    total_expenses = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return total_expenses


def get_balance():
    """
    Calculates remaining balance.
    Balance = total income - total expenses.
    """

    return get_total_income() - get_total_expenses()


def get_financial_summary():
    """
    Returns total income, total expenses, balance, and budget status.
    """

    total_income = get_total_income()
    total_expenses = get_total_expenses()
    balance = get_balance()

    if total_expenses > total_income:
        status = "Overspending"
    else:
        status = "Under control"

    return {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "balance": balance,
        "status": status
    }


def get_expense_report_by_category():
    """
    Groups expenses by category.
    """

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            c.name,
            COALESCE(SUM(ABS(t.amount)), 0) AS total_spent
        FROM transactions t
        LEFT JOIN categories c ON t.category_id = c.id
        WHERE t.transaction_type = 'Expense'
        GROUP BY c.name
        ORDER BY total_spent DESC;
    """)

    report = cursor.fetchall()

    cursor.close()
    conn.close()

    return report

def delete_all_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        query = "TRUNCATE TABLE transactions, categories RESTART IDENTITY CASCADE;"
        
        cursor.execute(query)
        conn.commit()
        print("Database wiped successfully.")
        return True
    except Exception as e:
        conn.rollback() 
        print(f"Error wiping database: {e}")
        return False
    finally:
        cursor.close()
        conn.close()