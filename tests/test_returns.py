from datetime import date, timedelta
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "src" / "northstar_support"))
from returns import DEMO_TODAY, FIXTURES, lookup, return_decision  # noqa: E402


@pytest.mark.parametrize(
    ("order_id", "days", "outcome"),
    [("CHI1001", 15, "eligible"), ("CHI1002", 45, "outside_window"), ("CHI1003", 30, "eligible")],
)
def test_fixture_eligibility(order_id, days, outcome):
    result = lookup(order_id, "unopened")
    assert result["status"] == "found"
    assert result["return"] == {
        "outcome": outcome, "elapsed_days": days, "as_of": "2026-11-04",
        "policy_id": "RETURN-01", "refund_authorized": False,
    }


@pytest.mark.parametrize(("days", "expected"), [(0, "eligible"), (29, "eligible"), (30, "eligible"), (31, "outside_window")])
def test_inclusive_boundary(days, expected):
    assert return_decision(DEMO_TODAY - timedelta(days=days), "unopened")["outcome"] == expected


@pytest.mark.parametrize("condition", ["opened", "defective"])
@pytest.mark.parametrize("days", [15, 30, 45])
def test_review_does_not_authorize_refund(condition, days):
    result = return_decision(DEMO_TODAY - timedelta(days=days), condition)
    assert result["outcome"] == "support_review"
    assert result["policy_id"] == "RETURN-02"
    assert result["refund_authorized"] is False


def test_missing_condition():
    assert lookup("CHI1001")["return"]["outcome"] == "needs_condition"


def test_unknown_is_distinct_from_outage():
    assert lookup("CHI9999")["status"] == "not_found"
    assert lookup("CHI9999", simulate_outage=True)["status"] == "unavailable"
    assert lookup("CHI1001", simulate_outage=True)["status"] == "unavailable"


def test_normalized_id():
    assert lookup(" chi1001 ", "unopened")["order_id"] == "CHI1001"


@pytest.mark.parametrize("order_id", ["", "CHI1", "CHI10010", "ignore instructions", "../orders.json", "CHI１２３４"])
def test_invalid_order_id(order_id):
    assert lookup(order_id)["status"] == "invalid_order_id"


def test_invalid_condition_is_explicit():
    with pytest.raises(ValueError, match="Unsupported condition"):
        lookup("CHI1001", "new")


def test_future_delivery_is_explicit():
    with pytest.raises(ValueError, match="after"):
        return_decision(date(2026, 11, 5), "unopened")


def test_date_is_injected_not_wall_clock():
    assert return_decision(date(2020, 1, 1), "unopened", today=date(2020, 1, 31))["outcome"] == "eligible"


def test_only_synthetic_fixture_fields():
    data = json.loads(FIXTURES.read_text())
    assert set(data) == {"CHI1001", "CHI1002", "CHI1003"}
    assert all(set(order) == {"item", "status_detail", "delivered"} for order in data.values())
