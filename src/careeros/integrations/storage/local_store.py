from __future__ import annotations

import shutil
from pathlib import Path


UPLOAD_DIR = Path("outputs/uploads")


def save_upload(filename: str, content: bytes) -> str:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    target = UPLOAD_DIR / filename
    target.write_bytes(content)
    return str(target)


def save_file_from_path(source_path: str, dest_name: str | None = None) -> str:
    src = Path(source_path)
    if not src.exists():
        raise FileNotFoundError(source_path)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    dst = UPLOAD_DIR / (dest_name or src.name)
    shutil.copy2(src, dst)
    return str(dst)
