"""
Unit tests for SOP ingestion, chunking, and policy retrieval.
"""

from src.knowledge_base import SOPKnowledgeBase


def test_sop_ingestion_and_chunking():
    kb = SOPKnowledgeBase()
    assert len(kb.passages) > 0, "Knowledge base should have indexed passages from data/sops/."


def test_sop_policy_retrieval_imps():
    kb = SOPKnowledgeBase()
    results = kb.retrieve("IMPS transaction failed money deducted reversal TAT", top_k=2)
    assert len(results) > 0
    top = results[0]
    assert top.policy_id == "SOP-IMPS-001"
    assert top.similarity_score > 0.65


def test_sop_policy_retrieval_card_dispute():
    kb = SOPKnowledgeBase()
    results = kb.retrieve("Customer charged twice duplicate swipe chargeback dispute", top_k=2)
    assert len(results) > 0
    top = results[0]
    assert top.policy_id == "SOP-CARD-003"
    assert top.similarity_score > 0.65
