import json
from pathlib import Path

from careeros.followups.service import generate_next_actions, write_action_queue
from careeros.notifications.service import generate_drafts_from_followups


def test_generate_drafts_from_followups(tmp_path: Path):
    # create a fake ledger jsonl
    ledger = tmp_path / "applications_v1.jsonl"
    ledger.write_text(
        json.dumps({
            "application_id": "a1",
            "status": "exported",
            "created_at_utc": "2026-02-01T00:00:00Z",
            "updated_at_utc": "2026-02-01T00:00:00Z",
            "package_path": "p",
            "validation_report_path": "v"
        }) + "\n",
        encoding="utf-8",
    )

    q = generate_next_actions(str(ledger), followup_days=3, stale_days=14)
    followups_path = tmp_path / "followups_v1.json"
    write_action_queue(q, out_path=followups_path)

    bundle = generate_drafts_from_followups(str(followups_path))
    assert bundle.total >= 1
    assert bundle.items[0].messages, "Expected at least one draft message"
