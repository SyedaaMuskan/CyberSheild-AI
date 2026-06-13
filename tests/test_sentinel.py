# tests/test_sentinel.py
import pytest
from core.tools.verifier_tool import evaluate_dynamic_risk

def test_completely_safe_diff():
    safe_code = "def append_user_data(username, database):\n    return True"
    result = evaluate_dynamic_risk(safe_code)
    assert result["is_safe"] is True
    assert result["verdict"] == "PROCEED_CLEAR"

def test_single_dynamic_indicator_warning():
    warning_code = "return getattr(ConfigClass, setting_name, None)"
    result = evaluate_dynamic_risk(warning_code)
    assert result["is_safe"] is True
    assert result["verdict"] == "PROCEED_WITH_MONITORING"

def test_critical_exploit_injection_block():
    malicious_code = "import importlib\nreturn eval(payload_str)"
    result = evaluate_dynamic_risk(malicious_code)
    assert result["is_safe"] is False
    assert result["verdict"] == "HALT_AND_ESCALATE"