"""Pure, deterministic business rules over synthetic data; no Azure dependency."""

import json
import re
from datetime import date
from pathlib import Path
from typing import Literal

DEMO_TODAY = date(2026, 11, 4)
Condition = Literal["unknown", "unopened", "opened", "defective"]
CONDITIONS = {"unknown", "unopened", "opened", "defective"}
FIXTURES = Path(__file__).with_name("orders.json")


def return_decision(
    delivered: date, condition: Condition, *, today: date = DEMO_TODAY
) -> dict:
    if condition not in CONDITIONS:
        raise ValueError(f"Unsupported condition: {condition}")
    elapsed_days = (today - delivered).days
    if elapsed_days < 0:
        raise ValueError("Delivery date cannot be after the evaluation date.")
    if condition == "unknown":
        outcome = "needs_condition"
    elif condition in {"opened", "defective"}:
        outcome = "support_review"
    elif elapsed_days <= 30:
        outcome = "eligible"
    else:
        outcome = "outside_window"
    return {
        "outcome": outcome,
        "elapsed_days": elapsed_days,
        "as_of": today.isoformat(),
        "policy_id": "RETURN-02"
        if condition in {"opened", "defective"}
        else "RETURN-01",
        "refund_authorized": False,
    }


def lookup(
    order_id: str, condition: Condition = "unknown", *, simulate_outage: bool = False
) -> dict:
    normalized = order_id.strip().upper()
    if not re.fullmatch(r"CHI[0-9]{4}", normalized):
        return {
            "status": "invalid_order_id",
            "message": "Use an order number like CHI1001.",
        }
    if condition not in CONDITIONS:
        raise ValueError(f"Unsupported condition: {condition}")
    if simulate_outage:
        return {
            "status": "unavailable",
            "message": "Order lookup is temporarily unavailable.",
        }
    orders = json.loads(FIXTURES.read_text())
    order = orders.get(normalized)
    if order is None:
        return {"status": "not_found", "order_id": normalized}
    return {
        "status": "found",
        "order_id": normalized,
        **order,
        "return": return_decision(date.fromisoformat(order["delivered"]), condition),
    }
