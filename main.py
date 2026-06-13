import os
import sys
import argparse

# Fix terminal encoding for emojis
sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv
from core.agents.orchestrator import SecurityOrchestrator

# Load environmental variables
load_dotenv()

class CyberShieldAIEngine:
    def __init__(self):
        print("[Initialization] Booting CyberShield AI Hybrid Architecture...\n")
        self.orchestrator = SecurityOrchestrator()

    def analyze_vulnerability(self, cve_id: str, code_diff: str):
        print(f"[Pipeline Activated] Evaluating security risk for issue: {cve_id}...\n")
        
        result = self.orchestrator.analyze(code_diff)
        
        print("\n=== CYBERSHIELD AI CLOUD VERDICT ===")
        print(f"Risk Score: {result['risk_score']}")
        print(f"Verdict: {result['verdict']}")
        print("\n=== REASONING ===")
        print(result["reasoning"])
        print("\n=== PATCH ===")
        print(result["patch_report"].get("patched_code", "No patch available"))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CyberShield AI Command Line Engine")
    parser.add_argument("--cve", type=str, default="CVE-2026-8812", help="The CVE ID to analyze")
    parser.add_argument("--code", type=str, help="Code snippet to analyze")
    
    args = parser.parse_args()

    sample_malicious_diff = """
def execute_payload(user_input):
    import importlib
    action_handler = getattr(sys.modules[__name__], f"handle_{user_input}")
    return eval(action_handler())
"""

    code_to_analyze = args.code if args.code else sample_malicious_diff
    
    engine = CyberShieldAIEngine()
    engine.analyze_vulnerability(args.cve, code_to_analyze)