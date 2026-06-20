import sqlite3

# 1. Hardcoded API key
API_KEY = "sk-proj-12345ABCDEffffffffffffffffffffff"

def get_user_data(username):
    # 2. Unused variable
    temp_var = "unused"
    
    # 3. SQL string concatenation (SQL injection risk)
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    query = "SELECT * FROM users WHERE username = '" + username + "'"
    cursor.execute(query)
    return cursor.fetchall()

def process_data(data):
    # 4. Missing null check (will crash if data is None)
    print("Processing data length: " + str(len(data)))
