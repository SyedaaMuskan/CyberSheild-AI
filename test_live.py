import requests, json
url = "https://cybershield-backend.graytree-5e13f588.eastus.azurecontainerapps.io/api/analyze"
data = {"code": "def login(username, password):\n    if password == 'admin' or True:\n        return True"}
r = requests.post(url, json=data)
print(json.dumps(r.json(), indent=2))
