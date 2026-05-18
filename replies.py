"""Intelligent group auto-replies, keyword replies and management commands."""
from __future__ import annotations

import asyncio
import logging
import re
from typing import Dict, List, Tuple

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

import database as db
from config import settings as cfg
from utils.helpers import (
    FloodTracker,
    cooldown,
    ensure_admin_or_reply,
    safe_call,
    safe_html,
)

log = logging.getLogger(__name__)

GREETING_PATTERNS = [
    (re.compile(r"\b(hi|hello|hey|yo|hola|howdy|sup)\b", re.I),
     ["Hello! 👋", "Hi there!", "Hey 👋", "Welcome!"]),
    (re.compile(r"\b(good\s*morning|gm)\b", re.I),
     ["Good morning! ☀️", "Morning! 🌅"]),
    (re.compile(r"\b(good\s*night|gn)\b", re.I),
     ["Good night! 🌙", "Sleep well 😴"]),
    (re.compile(r"\b(thanks?|thank\s*you|thx|ty)\b", re.I),
     ["You're welcome! 🙌", "Anytime!", "No problem 😊"]),
    (re.compile(r"\b(bye|goodbye|cya|see\s*ya)\b", re.I),
     ["Bye! 👋", "See you later!", "Take care!"]),
]


flood = FloodTracker(
    window_seconds=cfg.flood_window_seconds if cfg else 7,
    max_messages=cfg.flood_max_messages if cfg else 6,
)


async def handle_group_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    if not msg or not chat or not user:
        return
    if user.is_bot:
        return
    if not msg.text:
        return
    if chat.type not in ("group", "supergroup"):
        return

    text = msg.text.strip()
    if not text or text.startswith("/"):
        return

    # flood / repeat detection
    if flood.record(chat.id, user.id, text):
        log.debug("Flood/spam suppressed for user %s in chat %s", user.id, chat.id)
        return

    # 1) per-chat keyword auto replies
    auto_replies: List[Tuple[str, str]] = await asyncio.to_thread(
        db.list_auto_replies, chat.id
    )
    lowered = text.lower()
    for keyword, reply in auto_replies:
        if keyword and keyword in lowered:
            if cooldown.check(chat.id, user.id, f"kw:{keyword}",
                              cfg.reply_cooldown_seconds if cfg else 5):
                await safe_call(msg.reply_text(reply))
            return

    # 2) built-in greeting detection — only when bot mentioned or replied to
    me = context.bot.username
    mentioned = (me and f"@{me.lower()}" in lowered)
    replied_to_bot = (
        msg.reply_to_message is not None
        and msg.reply_to_message.from_user is not None
        and msg.reply_to_message.from_user.id == context.bot.id
    )
    if not (mentioned or replied_to_bot):
        return

    for pattern, responses in GREETING_PATTERNS:
        if pattern.search(text):
            if cooldown.check(chat.id, user.id, "greet",
                              cfg.reply_cooldown_seconds if cfg else 5):
                import random
                await safe_call(msg.reply_text(random.choice(responses)))
            return


# ---------- auto-reply admin commands ----------

async def cmd_addreply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_admin_or_reply(update, context):
        return
    raw = " ".join(context.args) if context.args else ""
    if "|" not in raw:
        await update.effective_message.reply_text(
            "Usage: /addreply keyword | reply text",
        )
        return
    kw, _, reply = raw.partition("|")
    kw = kw.strip().lower()
    reply = reply.strip()
    if not kw or not reply:
        await update.effective_message.reply_text("Both keyword and reply are required.")
        return
    await asyncio.to_thread(db.set_auto_reply, update.effective_chat.id, kw, reply)
    await update.effective_message.reply_text(
        f"✅ Added auto-reply for <code>{safe_html(kw)}</code>",
        parse_mode=ParseMode.HTML,
    )


async def cmd_delreply(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_admin_or_reply(update, context):
        return
    if not context.args:
        await update.effective_message.reply_text("Usage: /delreply keyword")
        return
    kw = " ".join(context.args).strip().lower()
    await asyncio.to_thread(db.delete_auto_reply, update.effective_chat.id, kw)
    await update.effective_message.reply_text(
        f"🗑 Removed auto-reply <code>{safe_html(kw)}</code>",
        parse_mode=ParseMode.HTML,
    )


async def cmd_listreplies(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    rows = await asyncio.to_thread(db.list_auto_replies, update.effective_chat.id)
    if not rows:
        await update.effective_message.reply_text("No auto-replies configured.")
        return
    body = "\n".join(f"• <code>{safe_html(k)}</code> → {safe_html(v)}" for k, v in rows)
    await update.effective_message.reply_text(
        f"<b>Auto-replies</b>\n{body}", parse_mode=ParseMode.HTML
    )
