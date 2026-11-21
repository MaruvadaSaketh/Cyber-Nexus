import time
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.experiments.experiment_engine import record_experiment
from app.services.strategy_router import execute_decision

router = APIRouter(prefix="/api/decisions", tags=["Decisions"])


class DecisionRecord(BaseModel):
    """One shipment, with every field the strategies and the model need."""

    shipment_id: str
    inventory: float = Field(ge=0)
    demand: float = Field(ge=0)
    delivery_days: float = Field(ge=0)
    shipping_cost: float = Field(ge=0)
    supplier_reliability: float = Field(ge=0.0, le=1.0)
    weather_risk: float = Field(ge=0.0, le=1.0)
    actual_delay: int = Field(ge=0, le=1)


@router.post("/execute")
def execute(record: DecisionRecord) -> dict[str, Any]:
    payload = record.model_dump()
    started = time.perf_counter()

    try:
        result = execute_decision(payload)
    except FileNotFoundError as error:
        raise HTTPException(
            status_code=503,
            detail=f"prediction model unavailable: {error}",
        ) from error
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error)) from error

    result["response_time"] = round(time.perf_counter() - started, 4)
    result["experiment"] = record_experiment(payload, result)
    return result
