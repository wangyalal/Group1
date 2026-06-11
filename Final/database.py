import psycopg2
from decimal import Decimal

def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        database="finance_app",
        user="finance_user",
        password="secure_password",
        port="5432"
    )

def insert_transaction(date, amount, description, tx_type, category):
    category = category.strip() if category else "Other"
    if not category:
        print("Database insertion error: Category cannot be empty!")
        return False
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:

        query = """
            INSERT INTO transactions (transaction_date, amount, description, transaction_type, category)
            VALUES (%s, %s, %s, %s, %s);
        """
        cursor.execute(query, (date, Decimal(str(amount)), description, tx_type, category))
        conn.commit()
        print("Transaction safely added to database!")
        return True
    except Exception as e:
        conn.rollback()
        print(f"Database insertion error: {e}")
        return False
    finally:
        cursor.close()
        conn.close()