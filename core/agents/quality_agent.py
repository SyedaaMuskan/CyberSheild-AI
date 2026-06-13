class CodeQualityAgent:

    def analyze(self, code: str):

        issues = []
        score = 100

        # unsafe eval usage
        if "eval(" in code:
            issues.append("Dangerous use of eval()")
            score -= 30

        # string concatenation in SQL
        if "+" in code and "SELECT" in code:
            issues.append("Possible SQL injection via string concatenation")
            score -= 30

        # no error handling
        if "try" not in code:
            issues.append("Missing error handling (try/except)")
            score -= 10

        # repeated patterns (very basic heuristic)
        if code.count("def ") > 5:
            issues.append("High function fragmentation (possible poor design)")
            score -= 10

        status = "GOOD" if score > 70 else "POOR"

        return {
            "quality_score": max(score, 0),
            "status": status,
            "issues": issues
        }