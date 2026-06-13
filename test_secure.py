import requests
import json

code = """
import sqlite3
def get_user(username):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    query = 'SELECT * FROM users WHERE username = ?'
    cursor.execute(query, (username,))
    return cursor.fetchone()
"""

res = requests.post('http://localhost:8000/api/analyze', json={'code': code})
print(res.json()['reasoning'])
