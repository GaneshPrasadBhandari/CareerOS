import json
from pathlib import Path
from careeros.followups.service import generate_next_actions


def test_generate_next_actions_creates_followup(tmp_path: Path):
    p = tmp_path / "applications_v1.jsonl"
    p.write_text(
        json.dumps({
            "application_id": "a1",
            "status": "submitted",
            "created_at_utc": "2026-02-01T00:00:00Z",
            "updated_at_utc": "2026-02-01T00:00:00Z",
            "package_path": "p",
            "validation_report_path": "v"
        }) + "\n",
        encoding="utf-8",
    )

    q = generate_next_actions(str(p), followup_days=3, stale_days=14)
    assert q.total >= 1
    assert any(i.action_type == "follow_up" for i in q.items)
