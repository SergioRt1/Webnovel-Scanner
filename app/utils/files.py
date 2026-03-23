from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def sanitize_filename(filename: str, suffix: str = ".txt", max_bytes: int = 255) -> str:
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1F]+', '_', filename).strip(" .")
    if not sanitized:
        sanitized = "untitled"

    suffix_bytes = len(suffix.encode("utf-8"))
    allowed = max_bytes - suffix_bytes
    data = sanitized.encode("utf-8")
    if len(data) > allowed:
        data = data[:allowed]
        sanitized = data.decode("utf-8", errors="ignore").rstrip(" ._")

    return sanitized or "untitled"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))
