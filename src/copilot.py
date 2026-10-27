"""
LLM Answer Generation & Copilot Orchestration module.
Constructs grounded prompts combining customer context, retrieved SOP passages,
and transcribed queries. Calls local Ollama model and validates structured JSON output.
"""

import os
import time
import json
import re
from typing import List, Optional, Tuple
import requests

from src.schemas import CustomerContext, SOPPassage, CopilotAnswer
from src.safety import run_pre_inference_safety_check, verify_answer_safety


SYSTEM_PROMPT = """You are an expert FinTech Call-Center Copilot assisting a banking customer-support agent on a live call.
Your role is to formulate a professional, clear, empathetic response that the agent can read aloud directly to the customer, and provide concrete, numbered operational procedure steps for the agent.

STRICT GROUNDING RULES:
1. ONLY state facts present in the provided Customer Context and Bank SOP Passages.
2. In the "agent_script", you MUST clearly explain the exact failure logs and resolution to the customer:
   - Greet customer by name, and confirm their transaction type, amount, and Transaction ID.
   - Explicitly cite the core failure reason and switch log code (e.g., "NPCI settlement sync pending (U69)" or "Beneficiary bank switch timeout (M4)").
   - State whether the funds were debited, and reassure the customer that their debited funds are safe in the settlement pool.
   - Quote the exact auto-reversal turnaround SLA (e.g., "Pending confirmation from NPCI gateway (window: 24 to 48 hours)" or "T+1 working day") and Bank Policy ID.
   - NEVER use generic placeholders like "We are reviewing your transaction details in our system. Let me check the latest status." or "<Support Team Email>".
3. NEVER invent account numbers, transaction IDs, balances, dates, or policy details.
4. NEVER promise instant refunds, compensation, or fee waivers unless explicitly authorized by the provided SOP.
5. For "next_action": NEVER write generic phrases like "verify logs and reassure customer".
   Instead, you MUST provide concrete, numbered operational steps based on the SOP (e.g., Step 1: ..., Step 2: ..., Step 3: ...).
6. If the question cannot be answered by the provided SOP excerpts or if evidence is insufficient, set "escalation_required": true and specify the reason.
7. You MUST return ONLY valid JSON matching this exact structure:
{
  "agent_script": "<A detailed, empathetic, customer-ready script explaining the failure, switch log, and reversal SLA>",
  "sop_policy_id": "<The exact policy identifier from the SOP excerpt, e.g. SOP-IMPS-001 or SOP-UPI-002>",
  "next_action": "<Numbered, concrete operational procedure steps: Step 1: ..., Step 2: ..., Step 3: ..., Step 4: ...>",
  "confidence_score": <A number between 0.0 and 1.0 representing confidence based on policy match>,
  "source_passages": ["<Short direct quote from the policy supporting this script>"],
  "escalation_required": <true or false>,
  "escalation_reason": "<Explanation if escalation is needed, or null>"
}
"""


def build_grounded_agent_script(
    customer: Optional[CustomerContext] = None,
    sop_id: Optional[str] = None,
    passages: Optional[List[SOPPassage]] = None
) -> str:
    """Build a detailed, grounded banking agent response script directly communicating switch failure logs and SLA."""
    if not customer:
        return "Dear customer, I am reviewing your account and transaction records in our system. Please give me a moment while I pull up the latest status."

    name = customer.customer_name
    txn_id = customer.transaction_id
    amt = customer.transaction_amount
    txn_type = customer.transaction_type or "Transaction"
    status = customer.transaction_status or "PENDING"
    reason = customer.failure_reason or "Network switch communication timeout"
    debit_stat = customer.debit_status or "debited from your account"
    sla = customer.auto_reversal_status or "T+1 working day"
    bene_name = customer.beneficiary_name or "the recipient"
    bene_bank = f" ({customer.beneficiary_bank})" if customer.beneficiary_bank else ""
    bene_str = f"to {bene_name}{bene_bank}"

    # Determine transaction channel from customer context first, then policy
    type_upper = (txn_type + " " + txn_id).upper()

    if "UPI" in type_upper or (sop_id and "002" in sop_id):
        sop_label = sop_id if (sop_id and "002" in sop_id) else "SOP-UPI-002"
        return (
            f"Hello {name}, I have checked our core network switch records for your {txn_type} of {amt} "
            f"(Transaction ID: {txn_id}) {bene_str}. "
            f"Our switch logs confirm that the transaction is currently in a {status} state with error code: {reason}. "
            f"Although the amount was {debit_stat.lower()}, please rest assured that your funds are completely safe in our settlement reconciliation pool. "
            f"Reconciliation SLA with the NPCI gateway is: {sla}. "
            f"If you are at the merchant counter, we advise waiting 15 minutes or using an alternate payment method. "
            f"If the transaction fails or duplicate charges occur, your account will be automatically refunded as governed by Bank Policy {sop_label}."
        )
    elif "IMPS" in type_upper or (sop_id and "001" in sop_id):
        sop_label = sop_id if (sop_id and "001" in sop_id) else "SOP-IMPS-001"
        return (
            f"Dear {name}, I have checked our core banking switch logs for your {txn_type} of {amt} "
            f"(Transaction ID: {txn_id}) {bene_str}. "
            f"Our system logs show that this transaction failed due to: {reason}. "
            f"Although the funds were {debit_stat.lower()}, please be assured that your money is safe in our reconciliation pool. "
            f"As per Bank Standard Operating Procedure {sop_label}, the full amount is: {sla}. "
            f"I have registered this inquiry under Service Request {customer.call_id} for your tracking."
        )
    elif "CARD" in type_upper or "POS" in type_upper or (sop_id and ("003" in sop_id or "005" in sop_id)):
        sop_label = sop_id if (sop_id and ("003" in sop_id or "005" in sop_id)) else "SOP-CARD-003"
        return (
            f"Good afternoon {name}, I have reviewed your {txn_type} of {amt} "
            f"(Transaction ID: {txn_id}) at {bene_name}{bene_bank}. "
            f"Our switch records show a dispute reference: {reason}. "
            f"The transaction status is '{status}' with debit record: {debit_stat.lower()}. "
            f"Under Bank Policy {sop_label}, we have initiated a formal dispute case ({customer.call_id}). "
            f"A provisional shadow credit will be placed on your card within 7 business days while our disputes desk reconciles with the merchant acquiring bank."
        )
    elif "ATM" in type_upper or (sop_id and "004" in sop_id):
        sop_label = sop_id if (sop_id and "004" in sop_id) else "SOP-ATM-004"
        return (
            f"Dear {name}, regarding your {txn_type} of {amt} "
            f"(Transaction ID: {txn_id}) at {bene_name}{bene_bank}, "
            f"our electronic journal logs confirm: {reason}. "
            f"Although {debit_stat.lower()}, under RBI guidelines and Bank SOP {sop_label}, "
            f"the failed cash withdrawal is under {sla}. "
            f"If the automated credit exceeds 5 calendar days, statutory delay compensation of ₹100 per day will be credited automatically. Reference ID: {customer.call_id}."
        )
    else:
        sop_label = sop_id or "SOP-GENERAL"
        return (
            f"Hello {name}, I have reviewed your {txn_type} of {amt} (Reference ID: {txn_id}). "
            f"Our core switch logs show status '{status}' with error reason: {reason}. "
            f"Debit Status: {debit_stat}. Reconciliation Timeline: {sla}. Reference ID: {customer.call_id}."
        )


def get_default_operational_steps(sop_id: Optional[str] = None, customer: Optional[CustomerContext] = None) -> str:
    """Return concrete, numbered operational steps based on bank SOP."""
    sop_upper = (sop_id or "").upper()
    txn_ref = customer.transaction_id if customer else "TXN-REF"
    acct = customer.masked_account if customer else "account"
    type_upper = ((customer.transaction_type or "") + " " + txn_ref).upper() if customer else ""

    if "UPI" in type_upper or "002" in sop_upper or "UPI" in sop_upper:
        return (
            f"Step 1: Verify transaction reference ({txn_ref}) and registered VPA/mobile in CBS ledger.\n"
            "Step 2: Check NPCI gateway settlement cycle (24 to 48-hour reconciliation window).\n"
            "Step 3: If customer is at retail merchant counter, advise waiting 15 mins before re-paying or use alternate payment.\n"
            "Step 4: Confirm that duplicate debits undergo automated refund within T+1 business day.\n"
            "Step 5: Escalate to Digital Payments Resolution Cell (Queue: UPI-REV-Q2) if status remains PENDING after 48 hours."
        )
    elif "IMPS" in type_upper or "001" in sop_upper or "IMPS" in sop_upper:
        return (
            f"Step 1: Verify last 4 digits of Transaction Ref ({txn_ref}) and account ({acct}).\n"
            "Step 2: Confirm CBS core switch reconciliation status (Error M4 switch timeout deemed reversed).\n"
            "Step 3: Advise customer that automated reversal is scheduled within T+1 working day.\n"
            "Step 4: Issue Service Request (SR) reference tracking number for call records.\n"
            "Step 5: Escalate to Tier-2 Operations Desk (Desk: OPS-IMPS-ESC) only if reversal exceeds T+2 days."
        )
    elif "CARD" in type_upper or "POS" in type_upper or "003" in sop_upper or "005" in sop_upper or "CARD" in sop_upper:
        return (
            "Step 1: Verify cardholder identity using non-sensitive security questions (never ask for CVV or PIN).\n"
            "Step 2: Check card transaction ledger to confirm if charge is settled/posted or on authorization hold.\n"
            "Step 3: Log Chargeback Dispute Form CB-01 with Acquiring Switch within 60 days of statement.\n"
            "Step 4: Route case to Tier-2 Card Disputes Desk (Queue: CRD-DISPUTE-L2) and advise 7-day shadow credit timeline."
        )
    elif "ATM" in type_upper or "004" in sop_upper or "ATM" in sop_upper:
        return (
            "Step 1: Record ATM Terminal ID, Date/Time, and debited cash withdrawal amount.\n"
            "Step 2: Inform customer of mandated T+5 calendar days automated auto-reversal SLA.\n"
            "Step 3: Log tracking ticket in Queue ATM-OPS-SLA.\n"
            "Step 4: Apply statutory delay compensation of ₹100/day if bank reversal exceeds T+5 days."
        )
    else:
        return (
            "Step 1: Verify caller identity and registered account details.\n"
            "Step 2: Review core transaction ledger for debit and settlement status.\n"
            "Step 3: Log inquiry in CRM and provide Service Request (SR) reference number.\n"
            "Step 4: Escalate to Senior Operations Supervisor if policy evidence is insufficient."
        )


class FinTechCopilot:
    def __init__(
        self,
        ollama_url: Optional[str] = None,
        model_name: Optional[str] = None,
        confidence_threshold: float = 0.75
    ):
        self.ollama_url = ollama_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model_name = model_name or os.getenv("OLLAMA_MODEL", "dolphin-phi:2.7b")
        self.confidence_threshold = float(os.getenv("RETRIEVAL_CONFIDENCE_THRESHOLD", confidence_threshold))

    def generate_answer(
        self,
        customer_query: str,
        customer: Optional[CustomerContext],
        retrieved_passages: List[SOPPassage]
    ) -> Tuple[CopilotAnswer, List[str]]:
        """
        Execute end-to-end Copilot generation pipeline:
        1. Pre-inference safety check & PII masking.
        2. Prompt construction.
        3. Local LLM inference via Ollama.
        4. Structured JSON extraction & fallback recovery.
        5. Post-generation safety & escalation verification.
        
        Returns: (CopilotAnswer, safety_warnings)
        """
        start_time = time.time()
        all_warnings: List[str] = []

        # Step 1: Pre-inference safety check
        pre_check = run_pre_inference_safety_check(
            customer_query, customer, self.confidence_threshold
        )
        all_warnings.extend(pre_check.warnings)

        clean_query = pre_check.masked_query

        # Check if mandatory escalation triggered before LLM call
        if pre_check.escalate_mandatory:
            latency = round(time.time() - start_time, 2)
            answer = CopilotAnswer(
                agent_script="I am transferring your request to our senior operations supervisor for immediate verification.",
                sop_policy_id=retrieved_passages[0].policy_id if retrieved_passages else None,
                next_action="Transfer call to Senior Operations Supervisor.",
                confidence_score=0.0,
                source_passages=[],
                escalation_required=True,
                escalation_reason=pre_check.escalation_reason,
                latency_seconds=latency
            )
            return answer, all_warnings

        # Step 2: Build Context & Prompt
        customer_block = "CUSTOMER CONTEXT:\n"
        if customer:
            customer_block += f"- Name: {customer.customer_name} (Tier: {customer.customer_tier})\n"
            customer_block += f"- Account: {customer.masked_account}\n"
            customer_block += f"- Transaction ID: {customer.transaction_id}\n"
            customer_block += f"- Type: {customer.transaction_type}\n"
            customer_block += f"- Amount: {customer.transaction_amount}\n"
            customer_block += f"- Status: {customer.transaction_status}\n"
            if customer.transaction_time:
                customer_block += f"- Time: {customer.transaction_time}\n"
            if customer.failure_reason:
                customer_block += f"- Failure Reason: {customer.failure_reason}\n"
            if customer.auto_reversal_status:
                customer_block += f"- Auto-Reversal Status: {customer.auto_reversal_status}\n"

        sop_block = "RETRIEVED BANK SOP EXCERPTS:\n"
        highest_retrieval_score = 0.0
        primary_sop_id = None
        for i, p in enumerate(retrieved_passages, 1):
            sop_block += f"\n[Passage {i}] ({p.policy_id} - {p.policy_title}):\n{p.content}\n"
            if p.similarity_score > highest_retrieval_score:
                highest_retrieval_score = p.similarity_score
                primary_sop_id = p.policy_id

        user_prompt = f"""{customer_block}

{sop_block}

CUSTOMER QUESTION:
"{clean_query}"

Generate the structured JSON response for the banking agent now:"""

        # Step 3: Invoke Local Ollama Model
        raw_response = self._call_ollama(user_prompt)

        # Step 4: Parse Structured Response
        answer_data = self._parse_json_response(raw_response, primary_sop_id, retrieved_passages, customer=customer)
        
        # Ground confidence score in actual retrieval score
        effective_confidence = min(answer_data.get("confidence_score", 0.8), highest_retrieval_score) if highest_retrieval_score > 0 else 0.4
        answer_data["confidence_score"] = round(effective_confidence, 2)

        # Step 5: Post-generation Safety Verification
        is_safe, post_warnings, esc_needed, esc_reason = verify_answer_safety(
            agent_script=answer_data["agent_script"],
            retrieved_passages=retrieved_passages,
            customer=customer,
            confidence_score=answer_data["confidence_score"],
            confidence_threshold=self.confidence_threshold
        )
        all_warnings.extend(post_warnings)

        if esc_needed:
            answer_data["escalation_required"] = True
            answer_data["escalation_reason"] = esc_reason or answer_data.get("escalation_reason")

        latency = round(time.time() - start_time, 2)
        answer_data["latency_seconds"] = latency

        copilot_answer = CopilotAnswer(**answer_data)
        return copilot_answer, all_warnings

    def _call_ollama(self, prompt: str) -> str:
        """Execute HTTP request to local Ollama API."""
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "system": SYSTEM_PROMPT,
                "stream": False,
                "format": "json",
                "options": {
                    "temperature": 0.1,  # Low temperature for strict factual consistency
                    "num_predict": 512
                }
            }
            resp = requests.post(f"{self.ollama_url}/api/generate", json=payload, timeout=60)
            if resp.status_code == 200:
                return resp.json().get("response", "")
        except Exception as e:
            return f'{{"error": "{str(e)}"}}'
        return ""

    def _parse_json_response(
        self,
        raw_text: str,
        fallback_sop_id: Optional[str],
        passages: List[SOPPassage],
        customer: Optional[CustomerContext] = None
    ) -> dict:
        """Parse JSON from model output with regex fallback, grounded script, and procedural steps."""
        default_script = build_grounded_agent_script(customer, fallback_sop_id, passages)
        default_steps = get_default_operational_steps(fallback_sop_id, customer)
        default_obj = {
            "agent_script": default_script,
            "sop_policy_id": fallback_sop_id or "SOP-GENERAL",
            "next_action": default_steps,
            "confidence_score": 0.80,
            "source_passages": [p.content[:150] for p in passages[:1]] if passages else [],
            "escalation_required": False,
            "escalation_reason": None
        }

        data = None
        if raw_text:
            # Direct JSON parse attempt
            try:
                parsed = json.loads(raw_text)
                if isinstance(parsed, dict):
                    data = parsed
            except Exception:
                # Regex search for JSON object
                json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
                if json_match:
                    try:
                        parsed = json.loads(json_match.group(0))
                        if isinstance(parsed, dict):
                            data = parsed
                    except Exception:
                        pass

        if data is None:
            data = default_obj.copy()
            if raw_text and raw_text.strip():
                clean_text = raw_text.strip()
                data["agent_script"] = clean_text[:400]
        else:
            for k, v in default_obj.items():
                if k not in data or data[k] is None:
                    data[k] = v

        sop_id_to_use = data.get("sop_policy_id") or fallback_sop_id

        # Ensure agent_script is rich, grounded, and quotes failure details
        curr_script = str(data.get("agent_script", "")).strip()
        is_generic_script = (
            len(curr_script) < 60 or
            "reviewing your transaction details" in curr_script.lower() or
            "reviewing your account and transaction" in curr_script.lower() or
            "let me check the latest status" in curr_script.lower() or
            "<support" in curr_script.lower() or
            "<" in curr_script or
            (customer and customer.transaction_amount not in curr_script and customer.transaction_id not in curr_script) or
            (customer and customer.failure_reason and (
                customer.failure_reason.lower() not in curr_script.lower() and
                "u69" not in curr_script.lower() and
                "m4" not in curr_script.lower() and
                "timeout" not in curr_script.lower() and
                "dispute" not in curr_script.lower() and
                "duplicate" not in curr_script.lower() and
                "dispenser" not in curr_script.lower() and
                "shutter" not in curr_script.lower()
            ))
        )
        if is_generic_script:
            data["agent_script"] = build_grounded_agent_script(customer, sop_id_to_use, passages)

        # Ensure next_action contains numbered concrete operational steps
        curr_action = str(data.get("next_action", "")).strip()
        is_generic_action = (
            len(curr_action) < 25 or
            "verify core switch" in curr_action.lower() or
            "reassure customer" in curr_action.lower() or
            ("step" not in curr_action.lower() and "1." not in curr_action)
        )
        if is_generic_action:
            data["next_action"] = get_default_operational_steps(sop_id_to_use, customer)

        return data
