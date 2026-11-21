"""Rule-based supply-chain risk scoring.

Produces a 0-100 risk score plus the individual factors that drove it, so the
API can explain a decision instead of returning a bare number.
"""

from __future__ import annotations

from typing import Any

# (field, weight, direction) - "high" means a large value is risky.
FACTORS: tuple[tuple[str, float, str], ...] = (
    ("inventory", 0.25, "low"),
    ("demand", 0.15, "high"),
    ("supplier_reliability", 0.25, "low"),
    ("weather_risk", 0.20, "high"),
    ("delivery_days", 0.15, "high"),
)

SEVERITY_BANDS: tuple[tuple[float, str], ...] = (
    (25.0, "LOW"),
    (50.0, "MEDIUM"),
    (75.0, "HIGH"),
    (100.0, "CRITICAL"),
)


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _normalize(field: str, value: float, direction: str) -> float:
    """Map a raw field onto 0-1 where 1 is the riskiest."""
    if field == "inventory":
        # Below demand is risky; 3x demand is comfortable.
        return _clamp(1.0 - value / 3000.0)
    if field == "demand":
        return _clamp(value / 20.0)
    if field == "supplier_reliability":
        return _clamp(1.0 - value)
    if field == "weather_risk":
        return _clamp(value)
    if field == "delivery_days":
        return _clamp(value / 10.0)
    return _clamp(value) if direction == "high" else _clamp(1.0 - value)


def analyze_supply_chain(record: dict[str, Any]) -> dict[str, Any]:
    """Score one shipment record and explain the result."""
    contributions: list[dict[str, Any]] = []
    total = 0.0

    for field, weight, direction in FACTORS:
        raw = record.get(field)
        if raw is None:
            continue
        normalized = _normalize(field, float(raw), direction)
        contribution = normalized * weight * 100.0
        total += contribution
        contributions.append(
            {
                "factor": field,
                "value": raw,
                "normalized": round(normalized, 4),
                "weight": weight,
                "contribution": round(contribution, 2),
            }
        )

    score = round(_clamp(total, 0.0, 100.0), 2)

    severity = "LOW"
    for threshold, label in SEVERITY_BANDS:
        if score <= threshold:
            severity = label
            break

    contributions.sort(key=lambda item: item["contribution"], reverse=True)

    return {
        "risk_score": score,
        "severity": severity,
        "top_factors": contributions[:3],
        "factors": contributions,
        "recommendation": _recommend(severity, contributions),
    }


def _recommend(severity: str, contributions: list[dict[str, Any]]) -> str:
    if severity in ("LOW",):
        return "Continue normal operations"
    if not contributions:
        return "Insufficient data for a recommendation"

    driver = contributions[0]["factor"]
    advice = {
        "inventory": "Replenish inventory or transfer stock between warehouses",
        "demand": "Review demand forecast and reserve capacity",
        "supplier_reliability": "Qualify an alternative supplier",
        "weather_risk": "Evaluate an alternative route",
        "delivery_days": "Escalate to a faster shipping mode",
    }.get(driver, "Review the shipment manually")

    return advice if severity in ("HIGH", "CRITICAL") else f"Monitor: {advice.lower()}"
