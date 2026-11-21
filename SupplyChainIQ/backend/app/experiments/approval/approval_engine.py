
import uuid
from datetime import datetime, timezone

APPROVAL_REQUESTS = {}

def create_approval_request(current_strategy, proposed_strategy, reason):

    request_id = str(uuid.uuid4())

    request = {
        "request_id": request_id,
        "current_strategy": current_strategy,
        "proposed_strategy": proposed_strategy,
        "reason": reason,
        "status": "PENDING",
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    APPROVAL_REQUESTS[request_id] = request

    return request


def review_approval(request_id, approved):

    request = APPROVAL_REQUESTS.get(request_id)

    if not request:
        return {"error": "Approval request not found"}

    if request["status"] != "PENDING":
        return {"error": "Request already reviewed"}

    request["status"] = "APPROVED" if approved else "REJECTED"

    request["reviewed_at"] = datetime.now(
        timezone.utc
    ).isoformat()

    return request
