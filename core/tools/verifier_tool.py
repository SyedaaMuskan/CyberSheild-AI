from typing import Dict, Any, List
import re

from core.tools.ast_analyzer import analyze_python_ast

def evaluate_dynamic_risk(code_diff: str) -> Dict[str, Any]:
    """Sentinel Risk Intelligence Engine

    Combines:
    1. Regex pattern detection
    2. AST structural analysis
    3. Weighted risk scoring
    4. Attack path generation
    5. Recommendations

    Returns a dict with risk metrics and reasoning.
    """

    risk_patterns = {
        "eval_execution": {
            "pattern": r"eval\s*\(",
            "score": 10,
            "category": "Execution",
            "recommendation": "Replace eval() with controlled logic."
        },

        "exec_execution": {
            "pattern": r"exec\s*\(",
            "score": 10,
            "category": "Execution",
            "recommendation": "Avoid exec() in production code."
        },

        "importlib_usage": {
            "pattern": r"importlib",
            "score": 4,
            "category": "Imports",
            "recommendation": "Restrict dynamic imports."
        },

        "getattr_usage": {
            "pattern": r"getattr\s*\(",
            "score": 5,
            "category": "Reflection",
            "recommendation": "Avoid reflection on untrusted input; validate attributes."
        },

        "pickle_usage": {
            "pattern": r"pickle\.loads",
            "score": 8,
            "category": "Serialization",
            "recommendation": "Avoid deserializing untrusted pickle data."
        },

        "os_system": {
            "pattern": r"os\.system",
            "score": 8,
            "category": "Execution",
            "recommendation": "Use subprocess safely instead."
        },

        "subprocess": {
            "pattern": r"subprocess",
            "score": 7,
            "category": "Execution",
            "recommendation": "Validate all shell commands."
        }
    }

    detected_indicators: List[str] = []
    recommendations: List[str] = []
    attack_path: List[str] = []
    categories = set()

    total_risk_score = 0

    # --------------------------
    # REGEX ANALYSIS
    # --------------------------

    for indicator, metadata in risk_patterns.items():

        if re.search(metadata["pattern"], code_diff or ""):

            detected_indicators.append(indicator)

            total_risk_score += metadata["score"]

            categories.add(metadata["category"])

            recommendations.append(metadata["recommendation"])

            attack_path.append(f"{metadata['category']} -> {indicator}")

    # --------------------------
    # AST ANALYSIS
    # --------------------------

    ast_result = analyze_python_ast(code_diff or "")

    if ast_result.get("success"):

        for finding in ast_result.get("findings", []):

            detected_indicators.append(finding.get("issue"))

            categories.add(finding.get("category"))

            attack_path.append(f"{finding.get('category')} -> {finding.get('issue')}")

            sev = finding.get("severity", "").upper()
            if sev == "CRITICAL":
                total_risk_score += 10
            elif sev == "HIGH":
                total_risk_score += 7
            elif sev == "MEDIUM":
                total_risk_score += 4
            else:
                total_risk_score += 2

    # --------------------------
    # RISK LEVEL
    # --------------------------

    if total_risk_score >= 20:
        risk_level = "CRITICAL"
        verdict = "HALT_AND_ESCALATE"
        is_safe = False
    elif total_risk_score >= 12:
        risk_level = "HIGH"
        verdict = "REVIEW_REQUIRED"
        is_safe = False
    elif total_risk_score >= 5:
        risk_level = "MEDIUM"
        verdict = "PROCEED_WITH_MONITORING"
        is_safe = True
    else:
        risk_level = "LOW"
        verdict = "PROCEED_CLEAR"
        is_safe = True

    # --------------------------
    # CONFIDENCE SCORE
    # --------------------------

    confidence_score = round(min(0.50 + (total_risk_score / 25), 0.99), 2)

    if total_risk_score == 0:
        confidence_score = 0.95

    # --------------------------
    # REASONING
    # --------------------------

    reasoning = (
        f"Detected {len(detected_indicators)} indicators "
        f"across {len(categories)} categories. "
        f"Total risk score: {total_risk_score}. "
        f"Risk level: {risk_level}."
    )

    return {
        "is_safe": is_safe,
        "verdict": verdict,
        "risk_level": risk_level,
        "risk_score": total_risk_score,
        "confidence_score": confidence_score,
        "detected_indicators": detected_indicators,
        "categories": list(categories),
        "attack_path": attack_path,
        "recommendations": recommendations,
        "reasoning": reasoning,
    }

