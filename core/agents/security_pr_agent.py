import difflib
import os
from google import genai
from google.genai import types

class SecurityPRAgent:
    """
    Converts fixes into GitHub-style security pull request using Google Gemini.
    """
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        self.model_name = "gemini-2.5-flash"
        
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None

    def generate_pr(self, original_code: str, fixed_code: str, fixes: list):

        diff = self._generate_diff(original_code, fixed_code)
        summary = self._generate_summary(fixes, diff)

        return {
            "title": "🔐 Auto Security Fix PR",
            "summary": summary,
            "diff": diff,
            "fixes": fixes
        }

    # -------------------------
    # DIFF GENERATOR
    # -------------------------

    def _generate_diff(self, original: str, fixed: str):

        original_lines = original.splitlines()
        fixed_lines = fixed.splitlines()

        diff = difflib.unified_diff(
            original_lines,
            fixed_lines,
            fromfile="vulnerable_code.py",
            tofile="secure_code.py",
            lineterm=""
        )

        return "\n".join(diff)

    # -------------------------
    # SUMMARY GENERATOR
    # -------------------------

    def _generate_summary(self, fixes: list, diff: str):

        if not fixes:
            return "No security issues detected."
            
        if self.client:
            try:
                prompt = f"Fixes Applied:\n{fixes}\n\nCode Diff:\n{diff}"
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction="You are a security engineer writing a GitHub PR summary. Write a concise 2-3 paragraph summary of what was fixed and why. Format it in clean Markdown."
                    ),
                )
                return response.text.strip()
            except Exception as e:
                print(f"[WARNING] PR Agent AI Failed: {e}")

        # Fallback
        summary = "The following security improvements were applied:\n"
        for fix in fixes:
            summary += f"- {fix}\n"
        summary += "\nThis PR improves security posture and removes exploit risks."

        return summary