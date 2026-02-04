from __future__ import annotations

import json
import logging
import sys
import traceback
from datetime import datetime
from pathlib import Path
from uuid import uuid4


def new_run_id() -> str:
    return uuid4().hex


class JsonLineFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        # If caller passed a dict payload, log it as JSON; otherwise log message text.
        payload = getattr(record, "payload", None)
        if payload is None:
            payload = {"message": record.getMessage()}

        base = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
        }
        base.update(payload)
        return json.dumps(base, ensure_ascii=False)


def get_logger(name: str = "careeros") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # already configured

    logger.setLevel(logging.INFO)
    fmt = JsonLineFormatter()

    # 1) Console logs (dev)
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    # 2) File logs (persistent)
    logs_dir = Path("logs")
    logs_dir.mkdir(parents=True, exist_ok=True)
    fh = logging.FileHandler(logs_dir / "careeros.jsonl", encoding="utf-8")
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    logger.propagate = False
    return logger


def log_event(logger: logging.Logger, event: str, run_id: str, **kwargs) -> None:
    record = logging.LogRecord(
        name=logger.name,
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="",
        args=(),
        exc_info=None,
    )
    record.payload = {"event": event, "run_id": run_id, **kwargs}
    logger.handle(record)


def log_exception(logger: logging.Logger, event: str, run_id: str, exc: Exception, **kwargs) -> None:
    tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    record = logging.LogRecord(
        name=logger.name,
        level=logging.ERROR,
        pathname="",
        lineno=0,
        msg="",
        args=(),
        exc_info=None,
    )
    record.payload = {
        "event": event,
        "run_id": run_id,
        "error_type": type(exc).__name__,
        "error_message": str(exc),
        "traceback": tb,
        **kwargs,
    }
    logger.handle(record)
