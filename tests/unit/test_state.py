import pytest
from src.models.state import JobApplicationState

def test_initial_state_blocks_execution():
    """Verify that a new state defaults to is_approved=False and blocks progress."""
    state = JobApplicationState(
        run_id="run_001",
        top_match_id="job_id_123",
        match_score=0.85
    )
    assert state.is_approved is False
    # This logic ensures the P14 Orchestrator will pause
    assert state.can_proceed() is False

def test_approved_state_allows_execution():
    """Verify that setting is_approved=True allows the system to proceed."""
    state = JobApplicationState(
        run_id="run_002",
        top_match_id="job_id_456",
        match_score=0.92,
        is_approved=True 
    )
    assert state.can_proceed() is True