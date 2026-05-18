"""Configuration loader for the Telegram group management bot."""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import List

from dotenv import load_dotenv

load_dotenv()


def _parse_admin_ids(raw: str | None) -> List[int]:
    if not raw:
        return []
    ids: List[int] = []
    for part in raw.replace(";", ",").split(","):
        part = part.strip()
        if not part:
            continue
        try:
            ids.append(int(part))
        except ValueError:
            logging.warning("Ignoring invalid ADMIN_IDS entry: %r", part)
    return ids


@dataclass(frozen=True)
class Settings:
    bot_token: str
    admin_ids: List[int] = field(default_factory=list)
    database_url: str = "bot.db"
    log_level: str = "INFO"

    # Behavior tuning
    reply_cooldown_seconds: int = 5
    tagall_cooldown_seconds: int = 60
    tagall_chunk_size: int = 5            # mentions per message
    flood_window_seconds: int = 7
    flood_max_messages: int = 6           # >this in window => considered flood
    max_warnings: int = 3


def load_settings() -> Settings:
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError(
            "BOT_TOKEN is not set. Copy .env.example to .env and fill it in."
        )
    return Settings(
        bot_token=token,
        admin_ids=_parse_admin_ids(os.getenv("ADMIN_IDS")),
        database_url=os.getenv("DATABASE_URL", "bot.db").strip() or "bot.db",
        log_level=os.getenv("LOG_LEVEL", "INFO").strip().upper() or "INFO",
    )


settings = load_settings() if os.getenv("BOT_TOKEN") else None  # lazy-safe import
