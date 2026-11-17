"""Deterministic approval routing for supported investigation actions.

This module assigns an approval route; it does not execute financial actions.
"""
from typing import Any

AUTO_APPROVED_ACTIONS = {
    "ALLOW_TRANSACTION",
    "MONITOR_CARD",
    "MONITOR_CONNECTED_CARDS",
    "WARN_CUSTOMER",
    "VERIFY_WITH_CUSTOMER",
    "STEP_UP_AUTH",
    "GENERATE_REPORT",
    "CREATE_CASE",
    "CLOSE_NO_FRAUD",
}

SUPPORTED_ACTIONS = AUTO_APPROVED_ACTIONS | {
    "DECLINE_TRANSACTION",
    "BLOCK_CARD",
    "FILE_REPORT",
    "ESCALATE_TO_ANALYST",
}


def route(action: str, exposure: float = 0.0) -> str:
    """Return the approval route for an action.

    High-exposure card blocks require L2 review. Analyst escalation and
    regulatory filing are never silently classified as auto-approved.
    """
    normalized = str(action or "").strip().upper()
    try:
        amount = max(0.0, float(exposure or 0.0))
    except (TypeError, ValueError):
        amount = 0.0

    if normalized in AUTO_APPROVED_ACTIONS:
        return "auto"
    if normalized == "DECLINE_TRANSACTION":
        return "L1"
    if normalized == "BLOCK_CARD":
        return "L1" if amount <= 2500 else "L2"
    if normalized in {"FILE_REPORT", "ESCALATE_TO_ANALYST"}:
        return "L2"
    return "L2"


def allowed(action: str, exposure: float = 0.0) -> dict[str, Any]:
    normalized = str(action or "").strip().upper()
    return {
        "action": normalized,
        "supported": normalized in SUPPORTED_ACTIONS,
        "route": route(normalized, exposure),
    }
