import sqlite3

API_KEY = "sk-live-abc123secretkey456"

def get_user(name):
    conn = sqlite3.connect("app.db")
    query = "SELECT * FROM users WHERE name = '" + name + "'"
    result = conn.cursor().execute(query).fetchone()
    conn.close()
    return result

def greet_user(name):
    user = get_user(name)
    print("Hello, " + user[1])
