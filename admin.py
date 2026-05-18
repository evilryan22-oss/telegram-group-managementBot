"""Moderation commands: /mute /unmute /ban /kick /warn."""
from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from telegram import ChatPermissions, Update
from telegram.constants import ParseMode
from telegram.error import TelegramError
from telegram.ext import ContextTypes

import database as db
from config import settings as cfg
from utils.helpers import (
    ensure_admin_or_reply,
    is_user_admin,
    mention_html,
    safe_call,
    safe_html,
)

log = logging.getLogger(__name__)


# ---------- target resolution ----------

async def _resolve_target(update: Update, context: ContextTypes.DEFAULT_TYPE
                          ) -> Tuple[Optional[int], Optional[str]]:
    """Return (user_id, display_name) of moderation target, or (None, None)."""
    msg = update.effective_message
    if msg.reply_to_message and msg.reply_to_message.from_user:
        u = msg.reply_to_message.from_user
        return u.id, u.first_name or u.username
    if context.args:
        arg = context.args[0]
        # numeric id?
        if arg.lstrip("-").isdigit():
            try:
                return int(arg), None
            except ValueError:
                return None, None
        # @username -> need to look it up via get_chat (best-effort)
        if arg.startswith("@"):
            try:
                chat = await context.bot.get_chat(arg)
                return chat.id, chat.first_name or chat.username
            except TelegramError:
                return None, None
    return None, None


_DURATION_RE = re.compile(r"^(\d+)([smhd])$", re.I)


def _parse_duration(s: str) -> Optional[timedelta]:
    m = _DURATION_RE.match(s.strip())
    if not m:
        return None
    n, unit = int(m.group(1)), m.group(2).lower()
    return {
        "s": timedelta(seconds=n),
        "m": timedelta(minutes=n),
        "h": timedelta(hours=n),
        "d": timedelta(days=n),
    }[unit]


async def _bot_can_restrict(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    chat = update.effective_chat
    try:
        me = await context.bot.get_chat_member(chat.id, context.bot.id)
    except TelegramError:
        return False
    return getattr(me, "can_restrict_members", False) or me.status in ("administrator", "creator")


# ---------- commands ----------

async def cmd_mute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_admin_or_reply(update, context):
        return
    if not await _bot_can_restrict(update, context):
        await update.effective_message.reply_text("I need 'Restrict members' permission.")
        return
    uid, name = await _resolve_target(update, context)
    if not uid:
        await update.effective_message.reply_text(
            "Reply to a user or pass @username / user_id. "
            "Optional duration: /mute @user 10m"
        )
        return
    if await is_user_admin(update, context, user_id=uid):
        await update.effective_message.reply_text("Cannot mute an administrator.")
        return

    duration = None
    for arg in context.args[1:] if context.args else []:
        duration = _parse_duration(arg)
        if duration:
            break

    until = (datetime.now(timezone.utc) + duration) if duration else None
    perms = ChatPermissions(can_send_messages=False)
    try:
        await context.bot.restrict_chat_member(
            update.effective_chat.id, uid, permissions=perms, until_date=until
        )
    except TelegramError as e:
        await update.effective_message.reply_text(f"⚠️ Could not mute: {e}")
        return

    suffix = f" for {duration}" if duration else ""
    await update.effective_message.reply_text(
        f"🔇 Muted {mention_html(uid, name)}{safe_html(suffix)}.",
        parse_mode=ParseMode.HTML,
    )


async def cmd_unmute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_admin_or_reply(update, context):
        return
    if not await _bot_can_restrict(update, context):
        await update.effective_message.reply_text("I need 'Restrict members' permission.")
        return
    uid, name = await _resolve_target(update, context)
    if not uid:
        await update.effective_message.reply_text("Reply to a user or pass @username / id.")
        return
    perms = ChatPermissions(
        can_send_messages=True,
        can_send_audios=True,
        can_send_documents=True,
        can_send_photos=True,
        can_send_videos=True,
        can_send_video_notes=True,
        can_send_voice_notes=True,
        can_send_polls=True,
        can_send_other_messages=True,
        can_add_web_page_previews=True,
        can_change_info=False,
        can_invite_users=True,
        can_pin_messages=False,
    )
    try:
        await context.bot.restrict_chat_member(
            update.effective_chat.id, uid, permissions=perms
        )
    except TelegramError as e:
        await update.effective_message.reply_text(f"⚠️ Could not unmute: {e}")
        return
    await update.effective_message.reply_text(
        f"🔊 Unmuted {mention_html(uid, name)}.", parse_mode=ParseMode.HTML
    )


async def cmd_ban(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_admin_or_reply(update, context):
        return
    if not await _bot_can_restrict(update, context):
        await update.effective_message.reply_text("I need 'Ban members' permission.")
        return
    uid, name = await _resolve_target(update, context)
    if not uid:
        await update.effective_message.reply_text("Reply to a user or pass @username / id.")
        return
    if await is_user_admin(update, context, user_id=uid):
        await update.effective_message.reply_text("Cannot ban an administrator.")
        return
    try:
        await context.bot.ban_chat_member(update.effective_chat.id, uid)
    except TelegramError as e:
        await update.effective_message.reply_text(f"⚠️ Could not ban: {e}")
        return
    await asyncio.to_thread(db.remove_member, update.effective_chat.id, uid)
    await update.effective_message.reply_text(
        f"⛔ Banned {mention_html(uid, name)}.", parse_mode=ParseMode.HTML
    )


async def cmd_kick(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_admin_or_reply(update, context):
        return
    if not await _bot_can_restrict(update, context):
        await update.effective_message.reply_text("I need 'Ban members' permission.")
        return
    uid, name = await _resolve_target(update, context)
    if not uid:
        await update.effective_message.reply_text("Reply to a user or pass @username / id.")
        return
    if await is_user_admin(update, context, user_id=uid):
        await update.effective_message.reply_text("Cannot kick an administrator.")
        return
    chat_id = update.effective_chat.id
    try:
        # ban + unban = kick (lets user rejoin)
        await context.bot.ban_chat_member(chat_id, uid)
        await asyncio.sleep(0.5)
        await context.bot.unban_chat_member(chat_id, uid, only_if_banned=True)
    except TelegramError as e:
        await update.effective_message.reply_text(f"⚠️ Could not kick: {e}")
        return
    await asyncio.to_thread(db.remove_member, chat_id, uid)
    await update.effective_message.reply_text(
        f"👢 Kicked {mention_html(uid, name)}.", parse_mode=ParseMode.HTML
    )


async def cmd_warn(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_admin_or_reply(update, context):
        return
    uid, name = await _resolve_target(update, context)
    if not uid:
        await update.effective_message.reply_text("Reply to a user or pass @username / id.")
        return
    if await is_user_admin(update, context, user_id=uid):
        await update.effective_message.reply_text("Cannot warn an administrator.")
        return

    count = await asyncio.to_thread(db.add_warning, update.effective_chat.id, uid)
    max_w = cfg.max_warnings if cfg else 3
    text = (f"⚠️ {mention_html(uid, name)} has been warned "
            f"({count}/{max_w}).")
    await update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)

    if count >= max_w:
        # auto-ban on threshold
        try:
            await context.bot.ban_chat_member(update.effective_chat.id, uid)
            await asyncio.to_thread(db.reset_warnings, update.effective_chat.id, uid)
            await asyncio.to_thread(db.remove_member, update.effective_chat.id, uid)
            await safe_call(update.effective_message.reply_text(
                f"⛔ Warning limit reached — {mention_html(uid, name)} banned.",
                parse_mode=ParseMode.HTML,
            ))
        except TelegramError as e:
            log.warning("Auto-ban on warn failed: %s", e)
