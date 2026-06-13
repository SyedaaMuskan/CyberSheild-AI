from typing import Dict, Any


class SystemIntegrityAgent:
    def analyze(self, code: str) -> Dict[str, Any]:
        # Basic heuristic: ensure code is not empty and report completeness
        completeness = 100 if code and code.strip() else 50
        return {"completeness_score": completeness, "issues": []}
class SystemIntegrityAgent:

    def analyze(self, code: str):

        issues = []
        score = 100

        # missing DB or external objects
        if "db.execute" in code and "db =" not in code:
            issues.append("Undefined database object 'db'")
            score -= 25

        # eval / os without imports (context issue)
        if "os." in code and "import os" not in code:
            issues.append("Missing import for os module")
            score -= 15

        # incomplete functions
        if "def " in code:
            if ":" in code and "return" not in code:
                issues.append("Function may be incomplete (no return detected)")
                score -= 10

        # no structure
        if "def " not in code:
            issues.append("No function-level structure detected")
            score -= 40

        status = "COMPLETE" if score >= 70 else "INCOMPLETE"

        return {
            "completeness_score": max(score, 0),
            "status": status,
            "issues": issues
        }