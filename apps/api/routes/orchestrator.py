from fastapi import APIRouter, HTTPException
import json
import os

# This line MUST exist for main.py to work
router = APIRouter()

STATE_FILE = "outputs/state/current_run.json"

@router.get("/orchestrator/current_state")
async def get_current_state():
    """Reads the local JSON artifact for the UI."""
    if not os.path.exists(STATE_FILE):
        return {"status": "idle", "message": "No pending application state."}
    
    with open(STATE_FILE, "r") as f:
        return json.load(f)

@router.post("/orchestrator/approve")
async def approve_match(payload: dict):
    """Updates the 'is_approved' flag in the state file."""
    if not os.path.exists(STATE_FILE):
        raise HTTPException(status_code=404, detail="State file missing")

    with open(STATE_FILE, "r") as f:
        data = json.load(f)
    
    # Flip the gate status
    data["is_approved"] = True
    data["user_feedback"] = payload.get("user_feedback", "")

    with open(STATE_FILE, "w") as f:
        json.dump(data, f, indent=4)

    return {"status": "approved"}

@router.post("/orchestrator/reject")
async def reject_match(payload: dict):
    """Marks current state as rejected so reranking can continue."""
    if not os.path.exists(STATE_FILE):
        raise HTTPException(status_code=404, detail="State file missing")

    with open(STATE_FILE, "r") as f:
        data = json.load(f)

    data["is_approved"] = False
    data["is_rejected"] = True
    data["rejection_feedback"] = payload.get("feedback", "")

    with open(STATE_FILE, "w") as f:
        json.dump(data, f, indent=4)

    return {"status": "rejected"}
