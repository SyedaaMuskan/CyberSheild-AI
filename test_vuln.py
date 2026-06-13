import requests
import json
code = "query = 'SELECT * FROM users WHERE username = ' + user_input"
res = requests.post('http://localhost:8000/api/analyze', json={'code': code})
data = res.json()
print('RAG:', data.get('rag_report'))
print('MEM:', data.get('memory_report'))
