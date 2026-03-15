from __future__ import annotations

import secrets
from datetime import datetime, timezone


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_now_compact() -> str:
    return utc_now().strftime("%Y%m%dT%H%M%SZ")


def new_batch_id(prefix: str) -> str:
    token = secrets.token_hex(4)
    return f"{prefix}_{utc_now_compact()}_{token}"


def gcs_prefix(*parts: str) -> str:
    cleaned = [p.strip("/").strip() for p in parts if p and p.strip("/").strip()]
    return "/".join(cleaned)
