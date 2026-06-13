# core/agents/critic_agent.py

from typing import Dict, Any


class CriticAgent:
    """
    Reviews outputs from all agents and checks:

    1. Agent disagreements
    2. Unsupported conclusions
    3. Memory contradictions
    4. Confidence reliability

    Produces a final critique report.
    """

    def review(
        self,
        ast_result: Dict[str, Any],
        verifier_result: Dict[str, Any],
        memory_result: Dict[str, Any]
    ) -> Dict[str, Any]:

        issues = []
        confidence_penalty = 0

        ast_risk = ast_result.get("risk", "unknown")
        verifier_risk = verifier_result.get("risk", "unknown")

        ast_findings = ast_result.get("findings", [])
        verifier_findings = verifier_result.get("findings", [])

        memory_patterns = memory_result.get("matched_patterns", [])

        # -------------------------
        # Rule 1: Agent disagreement
        # -------------------------

        if ast_risk != verifier_risk:
            issues.append(
                f"Conflict detected: AST={ast_risk}, Verifier={verifier_risk}"
            )
            confidence_penalty += 15

        # -------------------------
        # Rule 2: High risk but no evidence
        # -------------------------

        if ast_risk in ["high", "critical"] and not ast_findings:
            issues.append(
                "AST assigned high risk without findings"
            )
            confidence_penalty += 10

        if verifier_risk in ["high", "critical"] and not verifier_findings:
            issues.append(
                "Verifier assigned high risk without findings"
            )
            confidence_penalty += 10

        # -------------------------
        # Rule 3: Memory contradiction
        # -------------------------

        for pattern in memory_patterns:

            historical_risk = pattern.get("risk")

            if (
                historical_risk == "critical"
                and ast_risk == "low"
                and verifier_risk == "low"
            ):
                issues.append(
                    "Historical memory indicates critical pattern"
                )

                confidence_penalty += 20

        # -------------------------
        # Rule 4: Confidence sanity
        # -------------------------

        ast_conf = ast_result.get("confidence", 50)
        ver_conf = verifier_result.get("confidence", 50)

        if ast_conf > 95 and len(ast_findings) <= 1:
            issues.append(
                "AST confidence unusually high"
            )
            confidence_penalty += 5

        if ver_conf > 95 and len(verifier_findings) <= 1:
            issues.append(
                "Verifier confidence unusually high"
            )
            confidence_penalty += 5

        # -------------------------
        # Final recommendation
        # -------------------------

        if confidence_penalty >= 25:
            recommendation = "manual_review"

        elif confidence_penalty >= 10:
            recommendation = "review"

        else:
            recommendation = "approved"

        return {
            "issues": issues,
            "confidence_penalty": confidence_penalty,
            "recommendation": recommendation
        }