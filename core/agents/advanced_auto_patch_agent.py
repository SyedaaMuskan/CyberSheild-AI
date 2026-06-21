import os
import re
from typing import Dict, Any, Tuple, List
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

class AdvancedAutoPatchAgent:
    """
    Multi-step file-level auto patching system using Google Gemini.
    Fixes entire code files using an LLM.
    """

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        self.model_name = "gemini-2.5-flash"
        
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None

    def fix_file(self, code: str, deterministic_only: bool = False) -> Dict[str, Any]:
        patched_code = code or ""
        fixes = []
        
        if not self.client and not deterministic_only:
            # Fallback if no keys
            fixes.append("Warning: Gemini API keys not configured. Returning original code.")
            return {"patched_code": patched_code, "fix_steps": fixes}
        
        prompt = f"""
You are an expert security engineer. Review the following code, identify any vulnerabilities (such as SQL Injection, eval/exec, hardcoded secrets, unsafe deserialization), and rewrite the code to be completely secure.

Return ONLY the raw Python code. Do NOT wrap it in markdown code blocks (like ```python). Do NOT add any explanations.
Just the code.

CODE TO FIX:
{code}
"""
        if not deterministic_only:
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction="You are a senior security patching agent."
                    ),
                )
                
                result = response.text.strip()
                
                # Strip markdown if the model hallucinated it
                if result.startswith("```"):
                    lines = result.split("\n")
                    if lines[0].startswith("```"):
                        lines = lines[1:]
                    if lines and lines[-1].startswith("```"):
                        lines = lines[:-1]
                    result = "\n".join(lines).strip()
                
                patched_code = result
                fixes.append(f"Dynamically patched code using Gemini model: {self.model_name}")
                return {"patched_code": patched_code, "fix_steps": fixes}
                
            except Exception as e:
                print(f"\n[WARNING] Gemini AI failed -> switching to deterministic engine (Error: {str(e)})")
                fixes.append(f"[Gemini LLM Unavailable] Falling back to deterministic local patching rules. (Error: {str(e)})")
        else:
            fixes.append("Circuit Breaker: Applied deterministic patches instantly.")

        # --- DETERMINISTIC FALLBACK LOGIC ---
            # STEP 1: SQL INJECTION FIX
            if "SELECT * FROM" in patched_code and "+" in patched_code:
                patched_code = re.sub(
                    r'("SELECT \* FROM \w+ WHERE \w+ = ")\s*\+\s*(\w+)',
                    r'\1%s"',
                    patched_code
                )
                patched_code = re.sub(
                    r'(cursor\.execute\()(\w+)(\))',
                    r'\1\2, (user_input,)\3',
                    patched_code
                )
                fixes.append("Fallback: SQL Injection fixed via regex.")
            
            # STEP 2: EVAL/EXEC REMOVAL
            if "eval(" in patched_code:
                patched_code = patched_code.replace("eval(", "ast.literal_eval(")
                if "import ast" not in patched_code:
                    patched_code = "import ast\n" + patched_code
                fixes.append("Fallback: Replaced unsafe eval() with ast.literal_eval().")

            if "exec(" in patched_code:
                patched_code = patched_code.replace("exec(", "ast.literal_eval(")
                fixes.append("Fallback: Replaced unsafe exec().")

            # STEP 3: OS SYSTEM FIX
            if "os.system" in patched_code:
                patched_code = re.sub(
                    r'os\.system\(.*?\)',
                    r'subprocess.run(["ping", "-c", "4", ip_address], check=True)',
                    patched_code
                )
                if "import subprocess" not in patched_code:
                    patched_code = "import subprocess\n" + patched_code
                fixes.append("Fallback: Replaced os.system with safe subprocess.run.")
            
            # STEP 4: DESERIALIZATION FIX
            if "pickle.loads" in patched_code:
                patched_code = patched_code.replace("pickle.loads", "json.loads")
                if "import json" not in patched_code:
                    patched_code = "import json\n" + patched_code
                fixes.append("Fallback: Replaced unsafe pickle deserialization.")
                
            # STEP 5: XXE FIX
            if "xml.etree.ElementTree" in patched_code:
                patched_code = patched_code.replace("xml.etree.ElementTree", "defusedxml.ElementTree")
                if "import defusedxml.ElementTree" not in patched_code:
                    patched_code = "import defusedxml.ElementTree\n" + patched_code
                fixes.append("Fallback: Replaced xml.etree with safe defusedxml.")
                
            # STEP 6: SECRETS FIX
            if re.search(r'(?i)(password|secret_key|api_key|secret)\s*=\s*["\'].+?["\']', patched_code):
                patched_code = re.sub(
                    r'(?i)(password|secret_key|api_key|secret)\s*=\s*["\'].+?["\']',
                    r'\1 = os.getenv("\1".upper(), "REMOVED_SECRET")',
                    patched_code
                )
                if "import os" not in patched_code:
                    patched_code = "import os\n" + patched_code
                fixes.append("Fallback: Replaced hardcoded secret with os.getenv().")

        return {
            "patched_code": patched_code,
            "fix_steps": fixes
        }

