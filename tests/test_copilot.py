"""
Unit tests for copilot orchestration and structured response parsing.
"""

from src.copilot import FinTechCopilot
from src.schemas import CustomerContext, SOPPassage


def test_copilot_json_parser_valid():
    copilot = FinTechCopilot()
    raw_json = '''{
        "agent_script": "Mr. Sharma, your IMPS transaction of ₹15,000 will be auto-reversed within T+1 working day.",
        "sop_policy_id": "SOP-IMPS-001",
        "next_action": "Check CBS core switch log and register tracking reference.",
        "confidence_score": 0.88,
        "source_passages": ["Reversal to source account takes place within T+1 working day."],
        "escalation_required": false,
        "escalation_reason": null
    }'''
    parsed = copilot._parse_json_response(raw_json, "SOP-IMPS-001", [])
    assert parsed["agent_script"].startswith("Mr. Sharma")
    assert parsed["sop_policy_id"] == "SOP-IMPS-001"
    assert parsed["confidence_score"] == 0.88
    assert parsed["escalation_required"] is False


def test_copilot_json_parser_malformed_fallback():
    copilot = FinTechCopilot()
    raw_text = "I apologize, but this transaction is undergoing review and should be settled shortly."
    parsed = copilot._parse_json_response(raw_text, "SOP-IMPS-001", [])
    assert "agent_script" in parsed
    assert parsed["sop_policy_id"] == "SOP-IMPS-001"
    assert parsed["next_action"] is not None
