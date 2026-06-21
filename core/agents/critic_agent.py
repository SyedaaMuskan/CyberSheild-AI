import os
import json
from typing import Dict, Any
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

class CriticAgent:
    """Critic agent powered by Google Gemini."""

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        self.model_name = "gemini-2.5-flash"
        
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None

    def review(self, ast_report: Dict[str, Any], attack_report: Dict[str, Any], memory_report: Dict[str, Any], rag_report: Dict[str, Any] = None) -> Dict[str, Any]:
        # Fallback if keys are missing
        if not self.client:
            return {
                "issues": ["Gemini key not found, fallback to manual review"],
                "confidence_penalty": 30,
                "recommendation": "manual_review"
            }
        
        rag_context = ""
        if rag_report and rag_report.get("rag_context"):
            rag_context = "\nENTERPRISE KNOWLEDGE BASE:\n" + "\n".join(rag_report["rag_context"])

        prompt = f"""
You are an expert cybersecurity critic. Analyze the following RAW CODE and reports to determine the security risk.

RAW CODE:
{ast_report.get("code_snippet", "Code not provided (analyze reports)")}

AST REPORT:
{json.dumps(ast_report)}

ATTACK REPORT:
{json.dumps(attack_report)}

MEMORY REPORT:
{json.dumps(memory_report)}
{rag_context}

Based on these reports, output a JSON object with exactly these three keys:
1. "issues": an array of strings describing the problems found.
2. "confidence_penalty": an integer from 0 to 100 representing the severity of the flaws.
3. "recommendation": a string, exactly one of "approved", "review", or "manual_review".
"""

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    system_instruction="You are a strict security auditor. Output only JSON."
                ),
            )
            
            result_text = response.text.strip()
            result_json = json.loads(result_text)
            
            return {
                "issues": result_json.get("issues", ["Could not parse issues"]),
                "confidence_penalty": result_json.get("confidence_penalty", 50),
                "recommendation": result_json.get("recommendation", "manual_review")
            }

        except Exception as e:
            print(f"\n[WARNING] Gemini AI failed -> switching to deterministic engine (Error: {str(e)})")
            # --- DETERMINISTIC FALLBACK LOGIC ---
            confidence_penalty = 0
            issues = [f"[Gemini LLM Unavailable] Falling back to deterministic rules. (Error: {str(e)})"]

            findings = ast_report.get("findings", [])
            for f in findings:
                if f.get("severity", "").upper() == "CRITICAL":
                    confidence_penalty += 20
                    issues.append("Critical AST finding detected")

            recommendation = "approved"
            if confidence_penalty >= 25:
                recommendation = "manual_review"
            elif confidence_penalty >= 10:
                recommendation = "review"

            return {
                "issues": issues,
                "confidence_penalty": confidence_penalty,
                "recommendation": recommendation
            }

