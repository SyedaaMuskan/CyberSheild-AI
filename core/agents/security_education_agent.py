import os
from openai import AzureOpenAI

class SecurityEducationAgent:
    """
    Explains WHY a fix is safer in simple human terms using Azure OpenAI.
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

    def explain(self, original_code: str, patched_code: str, fixes: list):
        if self.client and patched_code and original_code and patched_code != original_code:
            try:
                prompt = f"Original Code:\n{original_code}\n\nPatched Code:\n{patched_code}"
                response = self.client.chat.completions.create(
                    model=self.deployment_name,
                    messages=[
                        {"role": "system", "content": "You are a security educator. Explain concisely in 1-2 bullet points why the new code is safer than the original code. Output just the raw text explanations without markdown formatting."},
                        {"role": "user", "content": prompt}
                    ]
                )
                content = response.choices[0].message.content.strip()
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