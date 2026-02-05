from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import uuid

from careeros.followups.service import load_action_queue
from careeros.followups.schema import ActionQueue, NextAction
from careeros.notifications.schema import DraftBundle, DraftItem, DraftMessage


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _write_json(path: str | Path, obj: Any) -> str:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2), encoding="utf-8")
    return str(p)


def _latest_file(pattern: str) -> Optional[str]:
    files = sorted(Path(".").glob(pattern))
    return str(files[-1]) if files else None


def draft_bundle_to_dict(b: DraftBundle) -> Dict[str, Any]:
    return {
        "version": b.version,
        "run_id": b.run_id,
        "created_at_utc": b.created_at_utc,
        "source_followups_path": b.source_followups_path,
        "total": b.total,
        "items": [
            {
                "draft_id": it.draft_id,
                "action_id": it.action_id,
                "application_id": it.application_id,
                "action_type": it.action_type,
                "title": it.title,
                "priority": it.priority,
                "due_at_utc": it.due_at_utc,
                "created_at_utc": it.created_at_utc,
                "messages": [
                    {"channel": m.channel, "subject": m.subject, "body": m.body}
                    for m in it.messages
                ],
            }
            for it in b.items
        ],
    }


def dict_to_draft_bundle(d: Dict[str, Any]) -> DraftBundle:
    items: List[DraftItem] = []
    for it in d.get("items", []):
        msgs = [DraftMessage(**m) for m in it.get("messages", [])]
        items.append(
            DraftItem(
                draft_id=it["draft_id"],
                action_id=it["action_id"],
                application_id=it["application_id"],
                action_type=it["action_type"],
                title=it["title"],
                priority=it["priority"],
                due_at_utc=it["due_at_utc"],
                created_at_utc=it["created_at_utc"],
                messages=msgs,
            )
        )
    return DraftBundle(
        version=d.get("version", "v1"),
        run_id=d.get("run_id", ""),
        created_at_utc=d.get("created_at_utc", ""),
        source_followups_path=d.get("source_followups_path", ""),
        total=int(d.get("total", len(items))),
        items=items,
    )


def _draft_for_action(a: NextAction) -> List[DraftMessage]:
    # Phase-0: deterministic templates. No hallucinated details.
    if a.action_type == "update_status":
        email_subject = "Quick status check on my application"
        email_body = (
            "Hi [Name],\n\n"
            "I wanted to quickly confirm the status of my application and whether any additional information would be helpful.\n"
            "I’m still very interested in the role and happy to share anything you need.\n\n"
            "Thanks,\n"
            "[Your Name]\n"
        )
        li_body = (
            "Hi [Name] — hope you’re doing well. I wanted to quickly check the status of my application for the role. "
            "If there’s any additional info I can share, I’m happy to send it. Thanks!"
        )
        return [
            DraftMessage(channel="email", subject=email_subject, body=email_body),
            DraftMessage(channel="linkedin", subject=None, body=li_body),
        ]

    if a.action_type == "follow_up":
        email_subject = "Following up on my application"
        email_body = (
            "Hi [Name],\n\n"
            "I’m following up on my application. I remain very interested in the role and would love to know next steps.\n\n"
            "Thanks,\n"
            "[Your Name]\n"
        )
        li_body = (
            "Hi [Name] — following up on my application. I’m still very interested and would love to hear about next steps. Thanks!"
        )
        return [
            DraftMessage(channel="email", subject=email_subject, body=email_body),
            DraftMessage(channel="linkedin", subject=None, body=li_body),
        ]

    if a.action_type == "close_loop":
        email_subject = "Closing the loop"
        email_body = (
            "Hi [Name],\n\n"
            "I wanted to close the loop on my application. If the role is no longer active or timing has shifted, no worries.\n"
            "Thank you for your time and consideration.\n\n"
            "Best,\n"
            "[Your Name]\n"
        )
        return [DraftMessage(channel="email", subject=email_subject, body=email_body)]

    if a.action_type == "prepare_interview":
        note_body = (
            "Interview prep checklist:\n"
            "- Review role requirements + company context\n"
            "- Prepare 3 STAR stories\n"
            "- Prepare 3 questions for interviewer\n"
            "- Rehearse 60-second intro\n"
        )
        return [DraftMessage(channel="note", subject="Interview prep", body=note_body)]

    # default
    return [DraftMessage(channel="note", subject="Action", body=a.notes or a.title)]


def generate_drafts_from_followups(
    followups_path: str | Path,
    *,
    run_id: Optional[str] = None,
) -> DraftBundle:
    rid = run_id or uuid.uuid4().hex
    now = _utc_now()

    q: ActionQueue = load_action_queue(followups_path)

    items: List[DraftItem] = []
    for a in q.items:
        items.append(
            DraftItem(
                draft_id=f"draft_{now.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}",
                action_id=a.action_id,
                application_id=a.application_id,
                action_type=a.action_type,
                title=a.title,
                priority=a.priority,
                due_at_utc=a.due_at_utc,
                created_at_utc=_iso(now),
                messages=_draft_for_action(a),
            )
        )

    return DraftBundle(
        version="v1",
        run_id=rid,
        created_at_utc=_iso(now),
        source_followups_path=str(followups_path),
        total=len(items),
        items=items,
    )


def write_drafts_bundle(
    bundle: DraftBundle,
    *,
    out_path: str | Path = "outputs/notifications/drafts_v1.json",
) -> str:
    return _write_json(out_path, draft_bundle_to_dict(bundle))


def load_drafts_bundle(path: str | Path) -> DraftBundle:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"drafts bundle not found: {p}")
    d = json.loads(p.read_text(encoding="utf-8"))
    return dict_to_draft_bundle(d)


def latest_drafts_path() -> Optional[str]:
    return _latest_file("outputs/notifications/drafts_v1*.json")
