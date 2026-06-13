import os
import json
from typing import List, Dict, Any
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

class AttackPathGenerator:
    """
    Converts AST findings into meaningful attack scenarios using Azure OpenAI.
    This is the reasoning layer above static detection.
    """
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

    def generate_paths(self, ast_report: Dict[str, Any], code: str) -> Dict[str, Any]:
        """
        Build attack scenarios from AST findings using LLM reasoning.
        """
        paths = []
        findings = ast_report.get("findings", [])
        
        if not findings:
            return {"success": True, "attack_paths": [], "path_count": 0}

        # If LLM is disabled or fails, fallback to rules
        fallback_paths = self._fallback_generate_paths(findings)

        if not self.client:
            return {"success": True, "attack_paths": fallback_paths, "path_count": len(fallback_paths)}

        prompt = f"""
You are an expert offensive security researcher. Given the following vulnerable code and static analysis findings, generate realistic step-by-step attack chains.

CODE:
{code[:1000]}

FINDINGS:
{json.dumps(findings)}

Output exactly valid JSON in this structure:
{{
  "attack_paths": [
    {{
      "attack_type": "Short name (e.g. SQL Injection)",
      "severity": "CRITICAL / HIGH / MEDIUM / LOW",
      "description": "1 sentence description of impact",
      "attack_flow": [
        "Step 1: Attacker action",
        "Step 2: System response",
        "Step 3: Exploit payload execution",
        "Step 4: Final consequence"
      ],
      "mitigation": "1 sentence fix recommendation"
    }}
  ]
}}
Do NOT output markdown code blocks. Output ONLY JSON.
"""
        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": "You are a strict JSON-only API. You build attack chains."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            result_text = response.choices[0].message.content.strip()
            
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            elif result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]
                
            result_json = json.loads(result_text.strip())
            
            # Ensure proper merging of generated paths with line numbers
            generated_paths = result_json.get("attack_paths", [])
            for i, p in enumerate(generated_paths):
                # Just take the line number from the finding heuristically
                if i < len(findings):
                    p["line"] = findings[i].get("line", -1)
                else:
                    p["line"] = -1
                paths.append(p)

        except Exception as e:
            print(f"\n[WARNING] LLM Attack Path failed -> fallback to rules (Error: {str(e)})")
            paths = fallback_paths

        return {
            "success": True,
            "attack_paths": paths,
            "path_count": len(paths)
        }

    def _fallback_generate_paths(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        paths = []
        for finding in findings:
            issue = finding.get("issue", "")
            severity = finding.get("severity", "LOW")
            line = finding.get("line", -1)

            if "eval" in issue or "exec" in issue:
                paths.append({
                    "attack_type": "Code Injection",
                    "severity": severity,
                    "description": "Untrusted input may be executed as Python code.",
                    "attack_flow": ["User input is accepted", "Input is passed into eval/exec", "Python executes injected code", "Attacker gains code execution control"],
                    "line": line,
                    "mitigation": "Avoid eval/exec. Use safe parsing."
                })
            elif "subprocess" in issue or "os.system" in issue:
                paths.append({
                    "attack_type": "Command Injection",
                    "severity": "CRITICAL",
                    "description": "External system commands may be executed with user input.",
                    "attack_flow": ["User input is passed to shell", "Command executes", "System compromised"],
                    "line": line,
                    "mitigation": "Avoid shell=True."
                })
            elif "pickle" in issue:
                paths.append({
                    "attack_type": "Deserialization Attack",
                    "severity": severity,
                    "description": "Unsafe deserialization leads to execution of malicious payloads.",
                    "attack_flow": ["Untrusted data is loaded using pickle", "Payload contains malicious object graph", "Object executes during deserialization", "Remote code execution occurs"],
                    "line": line,
                    "mitigation": "Use JSON instead of pickle for untrusted data."
                })
            elif "SQL injection" in issue:
                paths.append({
                    "attack_type": "SQL Injection",
                    "severity": "CRITICAL",
                    "description": "Database queries use string concatenation.",
                    "attack_flow": ["User provides malicious input", "Input is concatenated directly into SQL query", "Database executes modified query", "Data is exposed or modified"],
                    "line": line,
                    "mitigation": "Use parameterized queries."
                })
            elif "XXE" in issue or "XML" in issue:
                paths.append({
                    "attack_type": "XML External Entity (XXE)",
                    "severity": severity,
                    "description": "Unsafe XML parsing allows reading local files.",
                    "attack_flow": ["Attacker sends crafted XML", "Parser resolves external entity", "Local files or network accessed", "Data exposed"],
                    "line": line,
                    "mitigation": "Use defusedxml or disable entity resolution."
                })
            elif "XSS" in issue:
                paths.append({
                    "attack_type": "Cross-Site Scripting (XSS)",
                    "severity": severity,
                    "description": "Unescaped output allows Javascript injection.",
                    "attack_flow": ["Attacker injects payload", "Payload saved or reflected", "Victim views page", "Payload executes in browser"],
                    "line": line,
                    "mitigation": "Escape all user input before rendering HTML."
                })
            elif "secret" in issue.lower() or "credential" in issue.lower():
                paths.append({
                    "attack_type": "Hardcoded Secret",
                    "severity": severity,
                    "description": "Credentials stored directly in source code.",
                    "attack_flow": ["Developer hardcodes secret", "Code is committed or leaked", "Attacker extracts secret", "Attacker uses secret to compromise system"],
                    "line": line,
                    "mitigation": "Use environment variables or a secret manager."
                })
            elif "Path Traversal" in issue:
                paths.append({
                    "attack_type": "Path Traversal",
                    "severity": severity,
                    "description": "Unsanitized path inputs allow accessing arbitrary files.",
                    "attack_flow": ["Attacker inputs ../ path", "Path concatenated unsafely", "System reads outside target directory", "Sensitive files exposed"],
                    "line": line,
                    "mitigation": "Validate path boundaries or use secure file APIs."
                })
            else:
                paths.append({
                    "attack_type": "Unknown Risk",
                    "severity": severity,
                    "description": issue,
                    "attack_flow": ["Code pattern detected", "Potential misuse identified", "Manual review required"],
                    "line": line,
                    "mitigation": "Review manually."
                })
        return paths