"""Deterministic approval routing for benchmark recommendations.

This module assigns an approval route only. It never executes an action.
Routes are conservative defaults and must be reconciled with the challenge's
supplied bank policy before any production use.
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
    """Return a conservative approval route for a proposed action."""
    normalized = str(action or "").strip().upper()

    if normalized in AUTO_APPROVED_ACTIONS:
        return "auto"

    # Declines, card blocks, regulatory reports and analyst escalations can
    # materially affect customers or require regulated review.
    if normalized in {
        "DECLINE_TRANSACTION",
        "BLOCK_CARD",
        "FILE_REPORT",
        "ESCALATE_TO_ANALYST",
    }:
        return "L2"

    # Unknown actions must never be auto-approved.
    return "L2"


def allowed(action: str, exposure: float = 0.0) -> dict[str, Any]:
    normalized = str(action or "").strip().upper()
    return {
        "action": normalized,
        "supported": normalized in SUPPORTED_ACTIONS,
        "route": route(normalized, exposure),
    }
