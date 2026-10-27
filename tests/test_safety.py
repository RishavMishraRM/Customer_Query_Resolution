"""
Unit tests for banking safety guardrails:
- PII masking (PAN, Aadhaar, Card Number, Mobile, CVV, PIN)
- Credential leak blocking in agent responses
- Missing customer record mandatory escalation
- Low confidence / insufficient evidence escalation
"""

import pytest
from src.schemas import CustomerContext, SOPPassage
from src.safety import mask_pii, run_pre_inference_safety_check, verify_answer_safety


def test_pii_masking_pan():
    query = "My PAN card is ABCDE1234F, please check my transaction status."
    masked, detected = mask_pii(query)
    assert "[MASKED_PAN]" in masked
    assert "ABCDE1234F" not in masked
    assert "PAN Card" in detected


def test_pii_masking_aadhaar():
    query = "My Aadhaar is 1234 5678 9012, why did my transfer fail?"
    masked, detected = mask_pii(query)
    assert "[MASKED_AADHAAR]" in masked
    assert "1234 5678 9012" not in masked
    assert "Aadhaar Number" in detected


def test_pii_masking_card_and_cvv():
    query = "Card number 4111 2222 3333 4444 and CVV: 789 were entered."
    masked, detected = mask_pii(query)
    assert "[MASKED_CARD_NUMBER]" in masked
    assert "[MASKED_CVV]" in masked
    assert "789" not in masked


def test_pre_inference_missing_customer():
    query = "Where is my money?"
    result = run_pre_inference_safety_check(query, customer=None)
    assert result.escalate_mandatory is True
    assert "Customer record is missing" in result.escalation_reason


def test_verify_answer_safety_blocks_cvv_leak():
    script = "Please provide your CVV 456 so that I can process the refund."
    passages = [
        SOPPassage(
            doc_name="test.md", policy_id="SOP-IMPS-001", policy_title="Test",
            section="Sec 1", content="Policy details", similarity_score=0.9
        )
    ]
    is_safe, warnings, esc_needed, esc_reason = verify_answer_safety(
        agent_script=script,
        retrieved_passages=passages,
        customer=None,
        confidence_score=0.9,
        confidence_threshold=0.75
    )
    assert is_safe is False
    assert esc_needed is True
    assert "CVV" in esc_reason


def test_verify_answer_safety_low_confidence_escalation():
    script = "Your transfer will be reversed in 24 hours."
    passages = [
        SOPPassage(
            doc_name="test.md", policy_id="SOP-IMPS-001", policy_title="Test",
            section="Sec 1", content="Policy details", similarity_score=0.4
        )
    ]
    is_safe, warnings, esc_needed, esc_reason = verify_answer_safety(
        agent_script=script,
        retrieved_passages=passages,
        customer=None,
        confidence_score=0.45,
        confidence_threshold=0.75
    )
    assert is_safe is False
    assert esc_needed is True
    assert "Insufficient policy evidence" in esc_reason


def test_verify_answer_safety_unauthorized_guarantee():
    script = "I guarantee an instant refund of your full balance right now."
    passages = [
        SOPPassage(
            doc_name="test.md", policy_id="SOP-IMPS-001", policy_title="Test",
            section="Sec 1", content="Policy details", similarity_score=0.95
        )
    ]
    is_safe, warnings, esc_needed, esc_reason = verify_answer_safety(
        agent_script=script,
        retrieved_passages=passages,
        customer=None,
        confidence_score=0.95,
        confidence_threshold=0.75
    )
    assert is_safe is False
    assert esc_needed is True
    assert "unverified financial commitment" in esc_reason
