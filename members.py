"""Welcome / goodbye handlers and member tracking."""
from __future__ import annotations

import asyncio
import logging
from typing import Optional

from telegram import ChatMemberUpdated, Update
from telegram.constants import ChatMemberStatus, ParseMode
from telegram.ext import ContextTypes

import database as db
from utils.helpers import mention_html, safe_call, safe_html

log = logging.getLogger(__name__)

DEFAULT_WELCOME = "👋 Welcome {mention} to <b>{chat}</b>! Please read /rules."
DEFAULT_GOODBYE = "👋 {name} has left the chat."


def _status_change(cmu: ChatMemberUpdated) -> Optional[tuple[bool, bool]]:
    """Returns (was_member, is_member) or None if irrelevant."""
    old = cmu.old_chat_member.status
    new = cmu.new_chat_member.status
    was = old in (
        ChatMemberStatus.MEMBER,
        ChatMemberStatus.OWNER,
        ChatMemberStatus.ADMINISTRATOR,
        ChatMemberStatus.RESTRICTED,
    )
    is_ = new in (
        ChatMemberStatus.MEMBER,
        ChatMemberStatus.OWNER,
        ChatMemberStatus.ADMINISTRATOR,
        ChatMemberStatus.RESTRICTED,
    )
    if was == is_:
        return None
    return was, is_


async def chat_member_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    cmu = update.chat_member
    if cmu is None:
        return
    change = _status_change(cmu)
    if change is None:
        return
    was, is_ = change
    chat = cmu.chat
    user = cmu.new_chat_member.user
    if user.is_bot:
        return  # ignore other bots joining/leaving

    await asyncio.to_thread(db.upsert_chat, chat.id, chat.title)
    settings = await asyncio.to_thread(db.get_chat_settings, chat.id)

    if not was and is_:
        # joined
        await asyncio.to_thread(
            db.upsert_member, chat.id, user.id, user.username, user.first_name
        )
        template = settings.get("welcome_msg") or DEFAULT_WELCOME
        text = _format_template(template, user, chat.title)
        await safe_call(context.bot.send_message(
            chat.id, text, parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        ))
    elif was and not is_:
        # left / kicked
        await asyncio.to_thread(db.remove_member, chat.id, user.id)
        template = settings.get("goodbye_msg") or DEFAULT_GOODBYE
        text = _format_template(template, user, chat.title)
        await safe_call(context.bot.send_message(
            chat.id, text, parse_mode=ParseMode.HTML,
            disable_web_page_preview=True,
        ))


def _format_template(template: str, user, chat_title: Optional[str]) -> str:
    mention = mention_html(user.id, user.first_name)
    name = safe_html(user.first_name or (user.username or f"user{user.id}"))
    username = f"@{safe_html(user.username)}" if user.username else name
    chat = safe_html(chat_title or "this group")
    try:
        return template.format(mention=mention, name=name,
                               username=username, chat=chat, id=user.id)
    except (KeyError, IndexError, ValueError):
        # fall back to default if user-provided template has bad placeholders
        return DEFAULT_WELCOME.format(mention=mention, chat=chat)


async def track_message_author(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Persist any user we see speaking in a tracked chat."""
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    if not msg or not chat or not user or user.is_bot:
        return
    if chat.type not in ("group", "supergroup"):
        return
    await asyncio.to_thread(db.upsert_chat, chat.id, chat.title)
    await asyncio.to_thread(
        db.upsert_member, chat.id, user.id, user.username, user.first_name
    )
