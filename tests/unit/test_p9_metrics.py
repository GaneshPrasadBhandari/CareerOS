import json
from pathlib import Path

from careeros.analytics.service import compute_metrics

def test_metrics_computation(tmp_path: Path):
    p = tmp_path / "applications_v1.jsonl"
    rows = [
        {"application_id":"a1","status":"exported","created_at_utc":"2026-02-04T00:00:00Z","updated_at_utc":"2026-02-04T00:00:00Z","package_path":"p","validation_report_path":"v"},
        {"application_id":"a2","status":"submitted","created_at_utc":"2026-02-04T00:00:01Z","updated_at_utc":"2026-02-04T00:00:01Z","package_path":"p","validation_report_path":"v"},
        {"application_id":"a3","status":"interview","created_at_utc":"2026-02-04T00:00:02Z","updated_at_utc":"2026-02-04T00:00:02Z","package_path":"p","validation_report_path":"v"},
    ]
    with p.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")

    m = compute_metrics(str(p))
    assert m.total == 3
    assert m.funnel["exported"] == 1
    assert m.funnel["submitted"] == 1
    assert m.funnel["interview"] == 1
