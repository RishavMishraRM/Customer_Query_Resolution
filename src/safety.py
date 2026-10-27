"""
Banking Safety Guardrails module.
Implements pre-inference PII masking, post-generation policy grounding verification,
sensitive credential blocking (CVV, PIN, full cards), and mandatory escalation rules.
"""

import re
from typing import List, Tuple, Optional
from src.schemas import SafetyCheckResult, SOPPassage, CustomerContext

# Regex patterns for Indian banking PII
PAN_REGEX = re.compile(r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b', re.IGNORECASE)
AADHAAR_REGEX = re.compile(r'\b\d{4}\s?\d{4}\s?\d{4}\b')
CARD_NUMBER_REGEX = re.compile(r'\b(?:\d{4}[ -]?){3}\d{4}\b')
PHONE_REGEX = re.compile(r'(?:\+?91[\-\s]?)?[6-9]\d{9}\b')
CVV_REGEX = re.compile(r'\b(?:cvv|cvv2|security code)[:\s]*([0-9]{3,4})\b', re.IGNORECASE)
PIN_REGEX = re.compile(r'\b(?:pin|mpin|atm pin)[:\s]*([0-9]{4,6})\b', re.IGNORECASE)


def mask_pii(text: str) -> Tuple[str, List[str]]:
    """
    Mask sensitive financial PII from text before passing it to LLM or displaying.
    Returns (masked_text, detected_pii_types).
    """
    detected = []
    masked = text

    # Mask PAN
    if PAN_REGEX.search(masked):
        detected.append("PAN Card")
        masked = PAN_REGEX.sub("[MASKED_PAN]", masked)

    # Mask Full Card Numbers (16 digits) first to prevent 12-digit Aadhaar overlap
    if CARD_NUMBER_REGEX.search(masked):
        detected.append("Credit/Debit Card Number")
        masked = CARD_NUMBER_REGEX.sub("[MASKED_CARD_NUMBER]", masked)

    # Mask Aadhaar (12 digits)
    if AADHAAR_REGEX.search(masked):
        detected.append("Aadhaar Number")
        masked = AADHAAR_REGEX.sub("[MASKED_AADHAAR]", masked)

    # Mask Phone Numbers
    if PHONE_REGEX.search(masked):
        detected.append("Mobile Number")
        masked = PHONE_REGEX.sub("[MASKED_MOBILE]", masked)

    # Mask explicit CVV
    if CVV_REGEX.search(masked):
        detected.append("Card CVV")
        masked = CVV_REGEX.sub("CVV: [MASKED_CVV]", masked)

    # Mask explicit PIN
    if PIN_REGEX.search(masked):
        detected.append("Security PIN")
        masked = PIN_REGEX.sub("PIN: [MASKED_PIN]", masked)

    return masked, detected


def run_pre_inference_safety_check(
    query: str,
    customer: Optional[CustomerContext],
    confidence_threshold: float = 0.75
) -> SafetyCheckResult:
    """
    Validates input query and customer record before invoking LLM.
    """
    warnings = []
    escalate = False
    escalation_reason = None

    # Step 1: Mask PII
    masked_query, detected_pii = mask_pii(query)
    if detected_pii:
        warnings.append(f"PII detected and masked before processing: {', '.join(detected_pii)}.")

    # Step 2: Validate customer record
    if customer is None:
        escalate = True
        escalation_reason = "Customer record is missing or not selected. Human verification required."
        warnings.append(escalation_reason)

    # Step 3: Check for empty or gibberish input
    if len(query.strip()) < 3:
        warnings.append("Input query is too short to extract a valid banking question.")

    return SafetyCheckResult(
        is_safe=not escalate,
        masked_query=masked_query,
        warnings=warnings,
        escalate_mandatory=escalate,
        escalation_reason=escalation_reason,
        evidence_sufficient=customer is not None,
        detected_pii=detected_pii
    )


def verify_answer_safety(
    agent_script: str,
    retrieved_passages: List[SOPPassage],
    customer: Optional[CustomerContext],
    confidence_score: float,
    confidence_threshold: float = 0.75
) -> Tuple[bool, List[str], bool, Optional[str]]:
    """
    Post-generation safety verification.
    Ensures:
    1. No leakage of raw credentials (CVV, PIN, full cards).
    2. Minimum retrieval confidence met (>= threshold).
    3. Mandatory escalation if evidence is insufficient or question unsupported.
    4. Guard against unauthorized refund/waiver promises.
    
    Returns: (is_safe, safety_warnings, escalation_required, escalation_reason)
    """
    warnings = []
    escalation_required = False
    escalation_reason = None

    # Rule 1: Check for forbidden credential leakage in script
    lower_script = agent_script.lower()
    if CVV_REGEX.search(agent_script) or "cvv" in lower_script and any(char.isdigit() for char in lower_script):
        warnings.append("BLOCKED: Proposed script contains references to CVV numbers.")
        escalation_required = True
        escalation_reason = "Compliance violation: Agent response attempted to reference or request CVV."

    if PIN_REGEX.search(agent_script):
        warnings.append("BLOCKED: Proposed script contains references to private PIN numbers.")
        escalation_required = True
        escalation_reason = "Compliance violation: Agent response referenced customer PIN."

    if CARD_NUMBER_REGEX.search(agent_script):
        warnings.append("BLOCKED: Proposed script contains unmasked 16-digit card number.")
        escalation_required = True
        escalation_reason = "Compliance violation: Unmasked payment card number found in response."

    # Rule 2: Minimum retrieval confidence check
    if confidence_score < confidence_threshold or not retrieved_passages:
        warnings.append(
            f"Retrieval confidence ({confidence_score:.2f}) is below standard threshold ({confidence_threshold:.2f}) "
            "or no matching bank SOP was found."
        )
        escalation_required = True
        escalation_reason = (
            f"Insufficient policy evidence (confidence: {confidence_score:.2f} < {confidence_threshold:.2f}). "
            "Requires human supervisor review."
        )

    # Rule 3: Guard against unauthorized financial promises
    forbidden_promises = [
        "guarantee an instant refund",
        "i have refunded your money right now",
        "waived all charges permanently",
        "100% compensation guaranteed"
    ]
    for promise in forbidden_promises:
        if promise in lower_script:
            warnings.append(f"Caution: Script contains speculative financial commitment ('{promise}').")
            escalation_required = True
            escalation_reason = "Script made unverified financial commitment without supervisor sign-off."

    is_safe = (len(warnings) == 0) and not escalation_required
    return is_safe, warnings, escalation_required, escalation_reason
