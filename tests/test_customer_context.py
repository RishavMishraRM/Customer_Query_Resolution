"""
Unit tests for customer context service and synthetic data loading.
"""

from src.customer_context import CustomerContextService


def test_customer_context_loads():
    service = CustomerContextService()
    calls = service.get_all_calls()
    assert len(calls) >= 3, "Should have at least 3 customer records loaded."


def test_customer_scenario_fields():
    service = CustomerContextService()
    call = service.get_all_calls()[0]
    assert call.call_id.startswith("CALL-")
    assert call.customer_name
    assert call.transaction_id.startswith("TXN-")
    assert call.transaction_status in ["FAILED", "PENDING", "DISPUTED"]


def test_customer_lookup():
    service = CustomerContextService()
    call = service.get_call_by_id("CALL-2026-8801")
    assert call is not None
    assert call.customer_name == "Aarav Sharma"
