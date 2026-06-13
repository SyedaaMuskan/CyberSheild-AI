from typing import List, Dict, Any


class RecommendationEngine:
    """
    Converts attack paths into actionable secure coding recommendations.
    """

    def __init__(self):
        self.recommendations = []

    def generate_recommendations(self, attack_report: Dict[str, Any]) -> Dict[str, Any]:
        attack_paths = attack_report.get("attack_paths", [])

        for path in attack_paths:
            attack_type = path.get("attack_type", "")
            severity = path.get("severity", "LOW")
            line = path.get("line", -1)

            # 🔴 Code Injection (eval/exec)
            if attack_type == "Code Injection":
                self.recommendations.append({
                    "issue": "Avoid eval/exec usage",
                    "severity": severity,
                    "line": line,
                    "fix": (
                        "Replace eval() with safe parsing methods. "
                        "If evaluating expressions, use ast.literal_eval() instead."
                    ),
                    "secure_example": (
                        "import ast\n"
                        "data = ast.literal_eval(user_input)"
                    )
                })

            # 🔴 Command Injection
            elif attack_type == "Command Injection":
                self.recommendations.append({
                    "issue": "Unsafe system command execution",
                    "severity": severity,
                    "line": line,
                    "fix": (
                        "Avoid shell=True in subprocess. "
                        "Use argument list instead of string commands."
                    ),
                    "secure_example": (
                        "import subprocess\n"
                        "subprocess.run(['ls', '-la'], shell=False)"
                    )
                })

            # 🔴 Deserialization attack
            elif attack_type == "Deserialization Attack":
                self.recommendations.append({
                    "issue": "Unsafe deserialization with pickle",
                    "severity": severity,
                    "line": line,
                    "fix": (
                        "Do not use pickle for untrusted input. "
                        "Use JSON or safe serialization formats."
                    ),
                    "secure_example": (
                        "import json\n"
                        "data = json.loads(user_input)"
                    )
                })

            # 🟡 Generic case
            else:
                self.recommendations.append({
                    "issue": "Manual review required",
                    "severity": severity,
                    "line": line,
                    "fix": "Review code logic and validate input sources.",
                    "secure_example": "N/A"
                })

        return {
            "success": True,
            "recommendations": self.recommendations,
            "recommendation_count": len(self.recommendations)
        }