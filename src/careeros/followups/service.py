from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import json
import uuid

from careeros.followups.schema import ActionQueue, NextAction


# ---------------------------
# Helpers
# ---------------------------

def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_dt(dt_str: Optional[str]) -> Optional[datetime]:
    if not dt_str:
        return None
    s = dt_str.strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return None


def _read_jsonl(path: str | Path) -> List[Dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        return []
    rows: List[Dict[str, Any]] = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def _write_json(path: str | Path, obj: Any) -> str:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2), encoding="utf-8")
    return str(p)


def _latest_file(pattern: str) -> Optional[str]:
    files = sorted(Path(".").glob(pattern))
    return str(files[-1]) if files else None


# ---------------------------
# Serialization
# ---------------------------

def action_queue_to_dict(q: ActionQueue) -> Dict[str, Any]:
    return {
        "version": q.version,
        "run_id": q.run_id,
        "created_at_utc": q.created_at_utc,
        "source_tracking_path": q.source_tracking_path,
        "followup_days": q.followup_days,
        "stale_days": q.stale_days,
        "total": q.total,
        "actions": [
            {
                "action_id": a.action_id,
                "application_id": a.application_id,
                "action_type": a.action_type,
                "title": a.title,
                "priority": a.priority,
                "due_at_utc": a.due_at_utc,
                "created_at_utc": a.created_at_utc,
                "notes": a.notes,
            }
            for a in q.actions
        ],
    }


def dict_to_action_queue(d: Dict[str, Any]) -> ActionQueue:
    actions = [
        NextAction(
            action_id=x["action_id"],
            application_id=x["application_id"],
            action_type=x["action_type"],
            title=x["title"],
            priority=x["priority"],
            due_at_utc=x["due_at_utc"],
            created_at_utc=x["created_at_utc"],
            notes=x.get("notes", ""),
        )
        for x in d.get("actions", [])
    ]
    return ActionQueue(
        version=d.get("version", "v1"),
        run_id=d.get("run_id", ""),
        created_at_utc=d.get("created_at_utc", ""),
        source_tracking_path=d.get("source_tracking_path", ""),
        followup_days=int(d.get("followup_days", 3)),
        stale_days=int(d.get("stale_days", 14)),
        actions=actions,
    )


# ---------------------------
# Public API (what FastAPI imports)
# ---------------------------

def generate_next_actions(
    tracking_path: str | Path,
    *,
    # preferred names
    follow_up_after_days: int = 3,
    close_loop_after_days: int = 14,
    # backward-compatible aliases (used by tests)
    followup_days: Optional[int] = None,
    stale_days: Optional[int] = None,
    run_id: Optional[str] = None,
) -> ActionQueue:
    """
    Phase-0 deterministic follow-up/action generator.

    Backward compatibility:
      - followup_days overrides follow_up_after_days if provided
      - stale_days overrides close_loop_after_days if provided
    """
    if followup_days is not None:
        follow_up_after_days = int(followup_days)
    if stale_days is not None:
        close_loop_after_days = int(stale_days)

    rid = run_id or uuid.uuid4().hex
    now = _utc_now()

    applications = _read_jsonl(tracking_path)
    actions: List[NextAction] = []

    def add_action(application_id: str, action_type: str, title: str, due_in_days: int, priority: str, notes: str) -> None:
        actions.append(
            NextAction(
                action_id=f"act_{now.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}",
                application_id=application_id,
                action_type=action_type,
                title=title,
                priority=priority,
                due_at_utc=_iso(now + timedelta(days=due_in_days)),
                created_at_utc=_iso(now),
                notes=notes,
            )
        )

    for app in applications:
        application_id = str(app.get("application_id") or "").strip()
        if not application_id:
            continue

        status = (app.get("status") or "").lower().strip()
        created_at = _parse_dt(app.get("created_at_utc")) or now
        updated_at = _parse_dt(app.get("updated_at_utc")) or created_at
        age_days = (now - updated_at).days

        if status == "submitted":
            if age_days >= close_loop_after_days:
                add_action(
                    application_id,
                    "close_loop",
                    "Close the loop (no response)",
                    0,
                    "low",
                    f"Submitted but no response for {age_days} days. Consider a final close-loop message.",
                )
            elif age_days >= follow_up_after_days:
                add_action(
                    application_id,
                    "follow_up",
                    "Send recruiter follow-up",
                    0,
                    "high",
                    f"Submitted and idle for {age_days} days. Send a polite follow-up.",
                )

        elif status == "interview":
            add_action(
                application_id,
                "prepare_interview",
                "Prepare for interview",
                1,
                "high",
                "Prepare STAR stories, role-aligned projects, and questions for the interviewer.",
            )

        elif status == "exported":
            add_action(
                application_id,
                "update_status",
                "Update application status",
                2,
                "medium",
                "You exported the package—confirm if you submitted it and update status.",
            )

    return ActionQueue(
        version="v1",
        run_id=rid,
        created_at_utc=_iso(now),
        source_tracking_path=str(tracking_path),
        followup_days=int(follow_up_after_days),
        stale_days=int(close_loop_after_days),
        actions=actions,
    )


def write_action_queue(
    action_queue: Union[ActionQueue, Dict[str, Any]],
    *,
    out_path: str | Path = "outputs/followups/followups_v1.json",
) -> str:
    """
    Persist the generated action queue to disk.
    Accepts ActionQueue or dict (for backward compatibility).
    Returns written path.
    """
    if isinstance(action_queue, ActionQueue):
        payload = action_queue_to_dict(action_queue)
    else:
        payload = action_queue
    return _write_json(out_path, payload)


def load_action_queue(path: str | Path) -> ActionQueue:
    """
    Load an action queue JSON from disk into ActionQueue.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"action queue not found: {p}")
    d = json.loads(p.read_text(encoding="utf-8"))
    return dict_to_action_queue(d)


def latest_action_queue_path() -> Optional[str]:
    return _latest_file("outputs/followups/followups_v1*.json")
