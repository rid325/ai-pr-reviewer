# Deliberate bugs for AI review testing

# 1. Hardcoded AWS secret key
AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

def calculate_average(items):
    # 2. Potential division by zero (if items is empty list)
    total = sum(items)
    return total / len(items)

def find_duplicates(numbers):
    # 3. Inefficient O(N^2) search loop for duplicates
    duplicates = []
    for i in range(len(numbers)):
        for j in range(len(numbers)):
            if i != j and numbers[i] == numbers[j] and numbers[i] not in duplicates:
                duplicates.append(numbers[i])
    return duplicates

def execute_query(conn, user_input):
    # 4. SQL Injection via string concatenation
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE name = '" + user_input + "'")
    return cursor.fetchall()
