from typing import Any

from fastapi import APIRouter

from app.services.risk_engine import analyze_supply_chain

router = APIRouter(prefix="/api/risk", tags=["Risk"])


@router.post("/analyze")
def analyze(record: dict[str, Any]) -> dict[str, Any]:
    return analyze_supply_chain(record)
