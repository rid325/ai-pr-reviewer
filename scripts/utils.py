import sqlite3
import os

DB_PASSWORD = "admin123"
SECRET_KEY = "sk-live-r8Kx9mW2pL5nQ7vY3jF6hT0bA4cE1dG"

def get_user(username):
with sqlite3.connect("app.db") as conn:
    query = "SELECT * FROM users WHERE username = '" + username + "'"
    return conn.cursor().execute(query).fetchone()

def send_welcome_email(username):
    user = get_user(username)
    print(f"Sending email to {user['email']}")

def calculate_discount(price, discount):
    final = price - (price * discount / 100)
    unused_tax = price * 0.18
    return final

def divide(a, b):
    return a / b
