import urllib.request
import json

URL = "https://cybershield-backend.graytree-5e13f588.eastus.azurecontainerapps.io/api/analyze"

vuln_code = """
import sqlite3

def get_user(username):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    query = "SELECT * FROM users WHERE username = '" + username + "'"
    cursor.execute(query)
    return cursor.fetchall()
"""

req1 = urllib.request.Request(URL, method="POST", headers={"Content-Type": "application/json"}, data=json.dumps({"code": vuln_code}).encode("utf-8"))
with urllib.request.urlopen(req1) as f:
    res1 = json.loads(f.read().decode("utf-8"))

print("=== VULNERABLE CODE RESULT ===")
print("Verdict:", res1.get("verdict"))
print("Risk Score:", res1.get("risk_score"))

patched_code = res1.get("patch_report", {}).get("patched_code", "")
print("\n=== AUTO-HEALED CODE ===")
print(patched_code)

req2 = urllib.request.Request(URL, method="POST", headers={"Content-Type": "application/json"}, data=json.dumps({"code": patched_code}).encode("utf-8"))
with urllib.request.urlopen(req2) as f:
    res2 = json.loads(f.read().decode("utf-8"))

print("\n=== RE-ANALYZED PATCHED CODE RESULT ===")
print("Verdict:", res2.get("verdict"))
print("Risk Score:", res2.get("risk_score"))
