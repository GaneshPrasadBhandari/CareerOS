from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime

class JobApplicationState(BaseModel):
    run_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    
    # Layer 3/4 Data
    top_match_id: Optional[str] = None
    match_score: float = 0.0
    
    # --- P15: THE HUMAN GATE ---
    is_approved: bool = False 
    user_feedback: Optional[str] = None

    def can_proceed(self) -> bool:
        """Helper for the UI and Orchestrator"""
        return self.is_approved and self.top_match_id is not None