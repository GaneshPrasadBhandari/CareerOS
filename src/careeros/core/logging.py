from __future__ import annotations

import json
import logging
import sys
from datetime import datetime
from uuid import uuid4


def new_run_id() -> str:
    return uuid4().hex


def get_logger(name: str = "careeros") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # already configured

    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter("%(message)s")
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.propagate = False
    return logger


def log_event(logger: logging.Logger, event: str, run_id: str, **kwargs) -> None:
    payload = {
        "ts": datetime.utcnow().isoformat() + "Z",
        "event": event,
        "run_id": run_id,
        **kwargs,
    }
    logger.info(json.dumps(payload, ensure_ascii=False))
