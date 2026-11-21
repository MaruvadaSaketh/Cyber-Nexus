
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.experiments.approval.approval_engine import (
    create_approval_request,
    review_approval,
    APPROVAL_REQUESTS
)

router = APIRouter(prefix="/api/approval", tags=["Approval"])


class ApprovalRequest(BaseModel):
    current_strategy: str
    proposed_strategy: str
    reason: str


class ApprovalReview(BaseModel):
    approved: bool


@router.post("/request")
def request_change(data: ApprovalRequest):
    return create_approval_request(
        data.current_strategy,
        data.proposed_strategy,
        data.reason
    )


@router.get("/pending")
def pending_requests():
    return [
        request for request in APPROVAL_REQUESTS.values()
        if request["status"] == "PENDING"
    ]


@router.post("/{request_id}/review")
def approve_change(request_id: str, data: ApprovalReview):

    result = review_approval(request_id, data.approved)

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    return result
