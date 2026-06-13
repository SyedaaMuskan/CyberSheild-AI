import os
import json
from typing import Dict, Any
from openai import AzureOpenAI, OpenAI
from dotenv import load_dotenv

load_dotenv()

class CriticAgent:
    """Critic agent powered by Azure OpenAI (o4-mini)."""

    def __init__(self):
        endpoint_raw = os.getenv("AZURE_OPENAI_ENDPOINT", "")
        if endpoint_raw.endswith("/openai/v1"):
            self.endpoint = endpoint_raw[:-10]
        elif endpoint_raw.endswith("/openai/v1/"):
            self.endpoint = endpoint_raw[:-11]
        else:
            self.endpoint = endpoint_raw

        self.api_key = os.getenv("AZURE_OPENAI_API_KEY", "")
        self.deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT", "o4-mini")

        if self.endpoint and self.api_key:
            self.client = AzureOpenAI(
                azure_endpoint=self.endpoint,
                api_key=self.api_key,
                api_version="2024-12-01-preview",
                max_retries=0,
                timeout=60.0
            )
        else:
            self.client = None

    def review(self, ast_report: Dict[str, Any], attack_report: Dict[str, Any], memory_report: Dict[str, Any], rag_report: Dict[str, Any] = None) -> Dict[str, Any]:
        # Fallback if keys are missing
        if not self.client:
            return {
                "issues": ["Azure keys not found, fallback to manual review"],
                "confidence_penalty": 30,
                "recommendation": "manual_review"
            }
        
        rag_context = ""
        if rag_report and rag_report.get("rag_context"):
            rag_context = "\nENTERPRISE KNOWLEDGE BASE:\n" + "\n".join(rag_report["rag_context"])

        prompt = f"""
You are an expert cybersecurity critic. Analyze the following reports and determine the security risk.

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

Output ONLY valid JSON. Do not use markdown blocks.
"""

        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": "You are a strict security auditor. Output only JSON."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Clean up markdown if present
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            elif result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
                
            result_json = json.loads(result_text.strip())
            
            return {
                "issues": result_json.get("issues", ["Could not parse issues"]),
                "confidence_penalty": result_json.get("confidence_penalty", 50),
                "recommendation": result_json.get("recommendation", "manual_review")
            }

        except Exception as e:
            print(f"\n[WARNING] Azure AI failed -> switching to deterministic engine (Error: {str(e)})")
            # --- DETERMINISTIC FALLBACK LOGIC ---
            confidence_penalty = 0
            issues = [f"[Azure LLM Unavailable] Falling back to deterministic rules. (Error: {str(e)})"]

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
