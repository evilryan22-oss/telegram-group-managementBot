"""/tagall — mention all known members, admin-only, cooldown-protected."""
from __future__ import annotations

import asyncio
import logging

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

import database as db
from config import settings as cfg
from utils.helpers import (
    build_mentions,
    chunk_mentions,
    cooldown,
    ensure_admin_or_reply,
    safe_call,
    safe_html,
)

log = logging.getLogger(__name__)


async def cmd_tagall(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message
    if chat.type not in ("group", "supergroup"):
        await msg.reply_text("This command only works in groups.")
        return

    if not await ensure_admin_or_reply(update, context):
        return

    cd = cfg.tagall_cooldown_seconds if cfg else 60
    if not cooldown.check(chat.id, 0, "tagall", cd):
        await msg.reply_text(f"⏳ /tagall is on cooldown. Try again in a moment.")
        return

    members = await asyncio.to_thread(db.list_members, chat.id)
    # filter the requester out — optional, keeps things clean
    members = [m for m in members if m[0] != user.id]
    if not members:
        await msg.reply_text(
            "I don't know any members of this chat yet. "
            "I'll learn them as they speak."
        )
        return

    extra = " ".join(context.args) if context.args else ""
    header = f"📣 <b>{safe_html(extra)}</b>\n\n" if extra else ""

    mentions = build_mentions(members)
    per = cfg.tagall_chunk_size if cfg else 5
    chunks = chunk_mentions(mentions, per_message=per)

    for i, body in enumerate(chunks):
        text = (header if i == 0 else "") + body
        await safe_call(
            context.bot.send_message(
                chat.id, text, parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
            )
        )
        await asyncio.sleep(0.6)  # be gentle with the API
