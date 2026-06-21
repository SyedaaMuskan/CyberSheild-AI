from core.agents.orchestrator import SecurityOrchestrator
import sys

sys.stdout.reconfigure(encoding='utf-8')

test_code = """
import os

def authenticate(username, password):
    if username == "admin" and password == "SuperSecret123!":
        return True
    return False

def ping_host(ip):
    os.system(f"ping -c 4 {ip}")
"""

if __name__ == "__main__":
    print("Testing SecurityOrchestrator...")
    orchestrator = SecurityOrchestrator()
    result = orchestrator.analyze(test_code)
    
    print("\n--- RESULTS ---")
    print(f"Success: {result.get('success')}")
    print(f"Risk Score: {result.get('risk_score')}")
    print(f"Verdict: {result.get('verdict')}")
    
    print("\n--- REASONING ---")
    print(result.get("reasoning", "No reasoning provided."))
    
    print("\n--- PATCHED CODE ---")
    print(result.get("patch_report", {}).get("patched_code", "No patched code generated."))
    
    print("\nTest Complete.")
