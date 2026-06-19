import sqlite3
import requests

# Bug 1: Hardcoded API key (security vulnerability)
API_KEY = "sk-proj-abc123def456ghi789jkl012mno345pqr678"
DATABASE_URL = "postgresql://admin:password123@prod-db.company.com:5432/users"


def get_user(username):
    """Fetch user from database."""
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    
    # Bug 2: SQL Injection — string concatenation instead of parameterized query
    query = "SELECT * FROM users WHERE username = '" + username + "'"
    cursor.execute(query)
    
    result = cursor.fetchone()
    conn.close()
    return result


def process_payment(user_id, amount):
    """Process a payment for a user."""
    # Bug 3: Unused variable — calculated but never used
    tax_rate = 0.15
    total_with_tax = amount * (1 + tax_rate)
    
    # Bug 4: Missing null check — user could be None
    user = get_user(user_id)
    print(f"Processing payment of ${amount} for {user[1]}")
    
    headers = {"Authorization": f"Bearer {API_KEY}"}
    response = requests.post(
        "https://api.payments.com/charge",
        headers=headers,
        json={"user": user[1], "amount": amount}
    )
    
    return response.json()


def divide_numbers(a, b):
    """Divide two numbers."""
    # Bug 5: No zero division check
    return a / b
