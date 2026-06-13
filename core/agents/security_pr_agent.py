import difflib

class SecurityPRAgent:
    """
    Converts fixes into GitHub-style security pull request.
    """

    def generate_pr(self, original_code: str, fixed_code: str, fixes: list):

        diff = self._generate_diff(original_code, fixed_code)

        return {
            "title": "🔐 Auto Security Fix PR",
            "summary": self._generate_summary(fixes),
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

    def _generate_summary(self, fixes: list):

        if not fixes:
            return "No security issues detected."

        summary = "The following security improvements were applied:\n"

        for fix in fixes:
            summary += f"- {fix}\n"

        summary += "\nThis PR improves security posture and removes exploit risks."

        return summary