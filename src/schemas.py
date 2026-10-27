"""
Data schemas for FinTech Agent-Assist Copilot.
Defines strongly-typed models for customer context, policy passages,
and copilot structured outputs.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class CustomerContext(BaseModel):
    """Synthetic customer account and transaction details."""
    call_id: str
    customer_id: str
    customer_name: str
    masked_account: str
    masked_phone: str
    customer_tier: str
    transaction_id: str
    transaction_type: str
    transaction_amount: str
    transaction_status: str
    transaction_time: Optional[str] = None
    beneficiary_name: Optional[str] = None
    beneficiary_bank: Optional[str] = None
    failure_reason: Optional[str] = None
    debit_status: Optional[str] = None
    auto_reversal_status: Optional[str] = None
    notes: Optional[str] = None


class SOPPassage(BaseModel):
    """A retrieved knowledge passage from bank SOP documents."""
    doc_name: str
    policy_id: str
    policy_title: str
    section: str
    content: str
    similarity_score: float = Field(default=0.0, ge=0.0, le=1.0)


class SafetyCheckResult(BaseModel):
    """Outcome of safety guardrails and evidence checks."""
    is_safe: bool = True
    masked_query: str
    warnings: List[str] = Field(default_factory=list)
    escalate_mandatory: bool = False
    escalation_reason: Optional[str] = None
    evidence_sufficient: bool = True
    detected_pii: List[str] = Field(default_factory=list)


class CopilotAnswer(BaseModel):
    """Structured response delivered to the banking call-center agent."""
    agent_script: str = Field(description="Concise response the agent can read aloud to the customer.")
    sop_policy_id: Optional[str] = Field(default=None, description="Identifier of the supporting SOP (e.g., SOP-IMPS-001).")
    next_action: str = Field(description="Recommended concrete next operational step for the agent.")
    confidence_score: float = Field(default=0.85, ge=0.0, le=1.0, description="Confidence estimate based on evidence match.")
    source_passages: List[str] = Field(default_factory=list, description="Supporting excerpt lines from bank SOP.")
    escalation_required: bool = Field(default=False, description="Flag indicating if Tier-2 escalation is necessary.")
    escalation_reason: Optional[str] = Field(default=None, description="Detailed reason for human escalation.")
    latency_seconds: Optional[float] = Field(default=None, description="End-to-end processing latency in seconds.")
