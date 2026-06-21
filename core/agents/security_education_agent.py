import os
from google import genai
from google.genai import types

class SecurityEducationAgent:
    """
    Explains WHY a fix is safer in simple human terms using Google Gemini.
    """

    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        self.model_name = "gemini-2.5-flash"
        
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None

    def explain(self, original_code: str, patched_code: str, fixes: list):
        if self.client and patched_code and original_code and patched_code != original_code:
            try:
                prompt = f"Original Code:\n{original_code}\n\nPatched Code:\n{patched_code}"
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction="You are a security educator. Explain concisely in 1-2 bullet points why the new code is safer than the original code. Output just the raw text explanations without markdown formatting."
                    ),
                )
                content = response.text.strip()
                # Split lines and strip bullets
                explanations = [line.lstrip("•- *").strip() for line in content.split("\n") if line.strip()]
                return {"education_mode": True, "explanations": explanations}
            except Exception as e:
                print(f"[WARNING] Education Agent AI Failed: {e}")

        # Fallback to deterministic rules if AI fails or isn't configured
        explanations = []
        for fix in fixes:
            if "SQL Injection" in fix or "SELECT" in original_code.upper():
                explanations.append(
                    "SQL Injection is dangerous because attackers can modify database queries. "
                    "Parameterized queries prevent direct injection of malicious input."
                )
            elif "eval" in fix or "eval(" in original_code:
                explanations.append(
                    "eval() executes raw code from users, which can run malicious commands. "
                    "Removing it prevents remote code execution attacks."
                )
            elif "os.system" in fix or "os.system" in original_code:
                explanations.append(
                    "os.system executes shell commands directly. "
                    "This can be exploited for command injection attacks."
                )

        if not explanations and fixes:
             explanations.append("The code was refactored to adhere to secure coding standards and prevent execution of unvalidated input.")

        # Deduplicate list
        explanations = list(dict.fromkeys(explanations))

        return {
            "education_mode": True,
            "explanations": explanations
        }