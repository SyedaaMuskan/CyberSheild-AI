import sys
import json
from core.orchestrator import SecurityOrchestrator

def evaluate():
    orchestrator = SecurityOrchestrator()
    print("="*50)
    print(" CYBERSHIELD AI AGENT EVALUATION SUITE ")
    print("="*50)

    test_cases = [
        {
            "name": "1. SQL Injection (Pattern based)",
            "code": "def query_db(user_input):\n    query = 'SELECT * FROM users WHERE username = ' + user_input\n    cursor.execute(query)",
            "expected_verdict": "BLOCK"
        },
        {
            "name": "2. Authentication Bypass (Logic/Pattern based)",
            "code": "def login(username, password):\n    if password == 'admin' or True:\n        return True\n    return False",
            "expected_verdict": "BLOCK"
        },
        {
            "name": "3. Command Injection (AST based)",
            "code": "import subprocess\ndef run_ping(ip):\n    subprocess.call(['ping', '-c', '4', ip])",
            "expected_verdict": "BLOCK"
        },
        {
            "name": "4. Safe Arithmetic (Should Pass)",
            "code": "def add(a, b):\n    return a + b",
            "expected_verdict": "SAFE"
        }
    ]

    passed = 0
    for idx, tc in enumerate(test_cases):
        print(f"\nRunning Test {tc['name']}...")
        result = orchestrator.analyze(tc['code'])
        verdict = result['verdict']
        score = result['risk_score']
        
        if verdict == tc['expected_verdict']:
            print(f" PASS: Expected {tc['expected_verdict']}, Got {verdict} (Risk Score: {score})")
            passed += 1
        else:
            print(f" FAIL: Expected {tc['expected_verdict']}, Got {verdict} (Risk Score: {score})")
            print("Reasoning snippet:")
            safe_reasoning = result['reasoning'][:200].encode('ascii', 'ignore').decode('ascii')
            print(safe_reasoning + "...")

    print("="*50)
    print(f"RESULTS: {passed}/{len(test_cases)} tests passed.")
    print("="*50)

if __name__ == "__main__":
    evaluate()
