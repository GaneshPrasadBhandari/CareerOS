from fastapi import APIRouter, HTTPException
import json
import os

router = APIRouter()

STATE_FILE = "outputs/state/current_run.json"

@router.get("/orchestrator/current_state")
async def get_current_state():
    if not os.path.exists(STATE_FILE):
        return {"status": "idle", "message": "No pending application state."}
    with open(STATE_FILE, "r") as f:
        return json.load(f)

@router.post("/orchestrator/approve")
async def approve_match(payload: dict):
    if not os.path.exists(STATE_FILE):
        raise HTTPException(status_code=404, detail="State file missing")
    with open(STATE_FILE, "r") as f:
        data = json.load(f)
    
    data["is_approved"] = True
    data["user_feedback"] = payload.get("user_feedback", "")
    
    with open(STATE_FILE, "w") as f:
        json.dump(data, f, indent=4)
    return {"status": "approved"}
