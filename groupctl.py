"""Group control: antilink, tagadmins, promote, demote, lock/unlock."""
from __future__ import annotations

import asyncio
import logging
import re
from typing import Optional, Tuple

from telegram import ChatPermissions, Update
from telegram.constants import ChatMemberStatus, ParseMode
from telegram.error import TelegramError
from telegram.ext import ContextTypes

import database as db
from utils.helpers import (
    ensure_admin_or_reply,
    is_user_admin,
    mention_html,
    safe_call,
    safe_html,
)

log = logging.getLogger(__name__)

# url / t.me link detector (covers http(s), telegram invites, t.me)
LINK_RE = re.compile(
    r"(?:(?:https?://)|(?:www\.)|(?:t\.me/)|(?:telegram\.me/)|"
    r"(?:t\.me/joinchat/)|(?:\b[a-z0-9.-]+\.[a-z]{2,}\b))",
    re.IGNORECASE,
)


# ---------- target resolution (mirrors admin.py) ----------
async def _resolve_target(update: Update, context: ContextTypes.DEFAULT_TYPE
                          ) -> Tuple[Optional[int], Optional[str]]:
    msg = update.effective_message
    if msg.reply_to_message and msg.reply_to_message.from_user:
        u = msg.reply_to_message.from_user
        return u.id, u.first_name or u.username
    if context.args:
        arg = context.args[0]
        if arg.lstrip("-").isdigit():
            try:
                return int(arg), None
            except ValueError:
                return None, None
        if arg.startswith("@"):
            try:
                chat = await context.bot.get_chat(arg)
                return chat.id, chat.first_name or chat.username
            except TelegramError:
                return None, None
    return None, None


# ---------- ANTILINK ----------

async def cmd_antilink(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_admin_or_reply(update, context):
        return
    chat = update.effective_chat
    arg = (context.args[0].lower() if context.args else "").strip()
    if arg not in ("on", "off"):
        cur = await asyncio.to_thread(db.get_flag, chat.id, "antilink", 0)
        await update.effective_message.reply_text(
            f"Usage: /antilink on|off\nCurrent: <b>{'ON' if cur else 'OFF'}</b>",
            parse_mode=ParseMode.HTML,
        )
        return
    await asyncio.to_thread(db.set_flag, chat.id, "antilink", 1 if arg == "on" else 0)
    await update.effective_message.reply_text(f"🔗 Antilink turned <b>{arg.upper()}</b>.",
                                              parse_mode=ParseMode.HTML)


async def antilink_filter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    if not msg or not chat or not user or user.is_bot:
        return
    if chat.type not in ("group", "supergroup"):
        return
    on = await asyncio.to_thread(db.get_flag, chat.id, "antilink", 0)
    if not on:
        return
    text = msg.text or msg.caption or ""
    if not text:
        return
    if not LINK_RE.search(text):
        # also inspect entities for hidden URLs
        hidden = []
        for e in (msg.entities or []) + (msg.caption_entities or []):
            if e.type in ("url", "text_link") and e.url:
                hidden.append(e.url)
        if not hidden:
            return
    # admins are exempt
    if await is_user_admin(update, context, user_id=user.id):
        return
    await safe_call(msg.delete())
    await safe_call(context.bot.send_message(
        chat.id,
        f"🔗 {mention_html(user.id, user.first_name)}, links are not allowed here.",
        parse_mode=ParseMode.HTML,
    ))


# ---------- TAG ADMINS ----------

async def cmd_tagadmins(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    msg = update.effective_message
    if chat.type not in ("group", "supergroup"):
        await msg.reply_text("This command only works in groups.")
        return
    try:
        admins = await context.bot.get_chat_administrators(chat.id)
    except TelegramError as e:
        await msg.reply_text(f"⚠️ Could not fetch admins: {e}")
        return
    mentions = []
    for a in admins:
        u = a.user
        if u.is_bot:
            continue
        mentions.append(mention_html(u.id, u.first_name or u.username))
    if not mentions:
        await msg.reply_text("No human admins found.")
        return
    extra = " ".join(context.args) if context.args else "Admins, please take a look."
    await msg.reply_text(
        f"📣 <b>{safe_html(extra)}</b>\n" + " ".join(mentions),
        parse_mode=ParseMode.HTML,
    )


# ---------- PROMOTE / DEMOTE ----------

async def _bot_can_promote(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    chat = update.effective_chat
    try:
        me = await context.bot.get_chat_member(chat.id, context.bot.id)
    except TelegramError:
        return False
    return getattr(me, "can_promote_members", False)


async def cmd_promote(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_admin_or_reply(update, context):
        return
    if not await _bot_can_promote(update, context):
        await update.effective_message.reply_text(
            "I need the 'Add new admins' permission to promote users."
        )
        return
    uid, name = await _resolve_target(update, context)
    if not uid:
        await update.effective_message.reply_text("Reply to a user or pass @username / id.")
        return
    try:
        await context.bot.promote_chat_member(
            update.effective_chat.id, uid,
            can_manage_chat=True,
            can_delete_messages=True,
            can_restrict_members=True,
            can_invite_users=True,
            can_pin_messages=True,
            can_manage_video_chats=True,
            can_change_info=False,
            can_promote_members=False,
        )
    except TelegramError as e:
        await update.effective_message.reply_text(f"⚠️ Could not promote: {e}")
        return
    # Optional custom title from any extra args
    title = " ".join(context.args[1:]).strip() if len(context.args or []) > 1 else ""
    if title:
        try:
            await context.bot.set_chat_administrator_custom_title(
                update.effective_chat.id, uid, title[:16]
            )
        except TelegramError as e:
            log.info("set custom title failed: %s", e)
    await update.effective_message.reply_text(
        f"⬆️ Promoted {mention_html(uid, name)} to admin.",
        parse_mode=ParseMode.HTML,
    )


async def cmd_demote(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_admin_or_reply(update, context):
        return
    if not await _bot_can_promote(update, context):
        await update.effective_message.reply_text(
            "I need the 'Add new admins' permission to demote users."
        )
        return
    uid, name = await _resolve_target(update, context)
    if not uid:
        await update.effective_message.reply_text("Reply to a user or pass @username / id.")
        return
    try:
        await context.bot.promote_chat_member(
            update.effective_chat.id, uid,
            can_manage_chat=False,
            can_delete_messages=False,
            can_restrict_members=False,
            can_invite_users=False,
            can_pin_messages=False,
            can_manage_video_chats=False,
            can_change_info=False,
            can_promote_members=False,
        )
    except TelegramError as e:
        await update.effective_message.reply_text(f"⚠️ Could not demote: {e}")
        return
    await update.effective_message.reply_text(
        f"⬇️ Demoted {mention_html(uid, name)}.",
        parse_mode=ParseMode.HTML,
    )


# ---------- LOCK / UNLOCK GROUP ----------

_LOCKED = ChatPermissions(
    can_send_messages=False,
    can_send_audios=False,
    can_send_documents=False,
    can_send_photos=False,
    can_send_videos=False,
    can_send_video_notes=False,
    can_send_voice_notes=False,
    can_send_polls=False,
    can_send_other_messages=False,
    can_add_web_page_previews=False,
    can_change_info=False,
    can_invite_users=False,
    can_pin_messages=False,
)

_UNLOCKED = ChatPermissions(
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


async def cmd_lock(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_admin_or_reply(update, context):
        return
    try:
        await context.bot.set_chat_permissions(update.effective_chat.id, _LOCKED)
    except TelegramError as e:
        await update.effective_message.reply_text(f"⚠️ Could not lock: {e}")
        return
    await update.effective_message.reply_text("🔒 Group locked. Only admins can speak.")


async def cmd_unlock(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_admin_or_reply(update, context):
        return
    try:
        await context.bot.set_chat_permissions(update.effective_chat.id, _UNLOCKED)
    except TelegramError as e:
        await update.effective_message.reply_text(f"⚠️ Could not unlock: {e}")
        return
    await update.effective_message.reply_text("🔓 Group unlocked.")
