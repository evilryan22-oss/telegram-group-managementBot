"""Reusable helpers: admin checks, mentions, cooldowns, flood control."""
from __future__ import annotations

import asyncio
import html
import logging
import time
from collections import defaultdict, deque
from typing import Deque, Dict, Iterable, List, Optional, Tuple

from telegram import Chat, ChatMember, Update, User
from telegram.error import TelegramError
from telegram.ext import ContextTypes

log = logging.getLogger(__name__)


# ---------- HTML escaping & mentions ----------

def safe_html(text: Optional[str]) -> str:
    return html.escape(text or "", quote=False)


def mention_html(user_id: int, name: Optional[str]) -> str:
    display = safe_html(name) if name else f"user{user_id}"
    return f'<a href="tg://user?id={user_id}">{display}</a>'


def build_mentions(members: Iterable[Tuple[int, Optional[str], Optional[str]]]) -> List[str]:
    """Return a list of HTML mention strings for the given members."""
    out: List[str] = []
    for user_id, username, first_name in members:
        if username:
            # Plain @username works even without HTML — but escape just in case.
            out.append(f"@{safe_html(username)}")
        else:
            out.append(mention_html(user_id, first_name))
    return out


# ---------- admin checks ----------

async def is_user_admin(update: Update, context: ContextTypes.DEFAULT_TYPE,
                        user_id: Optional[int] = None) -> bool:
    chat = update.effective_chat
    user = update.effective_user
    if chat is None or (user is None and user_id is None):
        return False
    uid = user_id or user.id  # type: ignore[union-attr]

    # Bot owner override (from ADMIN_IDS in .env)
    from config import settings as cfg
    if cfg and uid in cfg.admin_ids:
        return True

    if chat.type == Chat.PRIVATE:
        return True  # in DM the user is always "admin" of their own chat

    try:
        member: ChatMember = await context.bot.get_chat_member(chat.id, uid)
    except TelegramError as e:
        log.warning("get_chat_member failed: %s", e)
        return False
    return member.status in (ChatMember.ADMINISTRATOR, ChatMember.OWNER)


async def ensure_admin_or_reply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if await is_user_admin(update, context):
        return True
    if update.effective_message:
        try:
            await update.effective_message.reply_text(
                "🚫 This command is restricted to group administrators."
            )
        except TelegramError:
            pass
    return False


# ---------- cooldown / rate-limit ----------

class Cooldown:
    """Per-(chat,user,key) cooldown tracker."""

    def __init__(self) -> None:
        self._last: Dict[Tuple[int, int, str], float] = {}

    def check(self, chat_id: int, user_id: int, key: str, seconds: int) -> bool:
        now = time.monotonic()
        k = (chat_id, user_id, key)
        prev = self._last.get(k, 0.0)
        if now - prev < seconds:
            return False
        self._last[k] = now
        return True


cooldown = Cooldown()


# ---------- flood / spam detector ----------

class FloodTracker:
    """Sliding-window flood detector per (chat,user)."""

    def __init__(self, window_seconds: int, max_messages: int) -> None:
        self.window = window_seconds
        self.max = max_messages
        self._events: Dict[Tuple[int, int], Deque[float]] = defaultdict(deque)
        self._last_text: Dict[Tuple[int, int], str] = {}

    def record(self, chat_id: int, user_id: int, text: str) -> bool:
        """Return True if the message looks like flood/spam."""
        now = time.monotonic()
        key = (chat_id, user_id)
        dq = self._events[key]
        dq.append(now)
        while dq and now - dq[0] > self.window:
            dq.popleft()
        flooding = len(dq) > self.max
        # repeated identical message
        repeated = self._last_text.get(key) == text and text.strip() != ""
        self._last_text[key] = text
        return flooding or repeated


# ---------- safe execution ----------

async def safe_call(coro):
    """Await a coroutine, swallow TelegramError, log it, never crash the bot."""
    try:
        return await coro
    except TelegramError as e:
        log.warning("Telegram API call failed: %s", e)
    except asyncio.CancelledError:
        raise
    except Exception:  # noqa: BLE001
        log.exception("Unexpected error in safe_call")
    return None


# ---------- chunking for /tagall ----------

def chunk_mentions(mentions: List[str], per_message: int = 5,
                   max_chars: int = 3500) -> List[str]:
    """Split mention list into Telegram-safe message bodies."""
    out: List[str] = []
    buf: List[str] = []
    length = 0
    for m in mentions:
        # +1 for the separating space
        if len(buf) >= per_message or length + len(m) + 1 > max_chars:
            if buf:
                out.append(" ".join(buf))
            buf = [m]
            length = len(m)
        else:
            buf.append(m)
            length += len(m) + 1
    if buf:
        out.append(" ".join(buf))
    return out
