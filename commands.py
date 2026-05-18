"""Basic command handlers: /start /help /about /rules /ping /joke /settings."""
from __future__ import annotations

import logging
import random
import time
from typing import List

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

import database as db
from utils.helpers import ensure_admin_or_reply, safe_html

log = logging.getLogger(__name__)

JOKES: List[str] = [
    "Why don't scientists trust atoms? Because they make up everything.",
    "I told my computer I needed a break — it said: 'No problem, I'll go to sleep.'",
    "Why did the developer go broke? Because he used up all his cache.",
    "There are 10 kinds of people: those who understand binary and those who don't.",
    "Debugging: being the detective in a crime movie where you are also the murderer.",
    "Why do programmers prefer dark mode? Because light attracts bugs.",
]

DEFAULT_RULES = (
    "📜 <b>Group Rules</b>\n"
    "1. Be respectful — no insults or hate speech.\n"
    "2. No spam, flooding or unsolicited promotions.\n"
    "3. Keep discussions on-topic.\n"
    "4. No NSFW content.\n"
    "5. Listen to admins.\n\n"
    "Admins can override these with <code>/setrules &lt;text&gt;</code>."
)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    name = safe_html(user.first_name) if user else "there"
    text = (
        f"👋 Hello <b>{name}</b>!\n\n"
        "I'm a group management bot. Add me to your group and promote me to admin "
        "to unlock welcomes, moderation, /tagall and more.\n\n"
        "Use /help to see what I can do."
    )
    await update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "<b>Core</b>\n"
        "/start /help /about /rules /ping /settings\n"
        "\n<b>Fun</b>\n"
        "/joke /riddle /puzzle /truth /dare /tod (truth-or-dare)\n"
        "/quiz – random trivia quiz poll\n"
        "/weather &lt;city&gt; – live weather\n"
        "/ttt [bot] – Tic-Tac-Toe (2 players or vs bot)\n"
        "\n<b>Reactions</b> (reply to a user)\n"
        "/hug /kiss /slap /kill /cry /smile /run /laugh /punch /bite\n"
        "/poke /pat /wave /dance /wink /highfive /shoot /yawn /shrug /facepalm\n"
        "\n<b>Tagging</b>\n"
        "/tagall [msg] – mention everyone (admins, cooldown)\n"
        "/tagadmins [msg] – ping all admins\n"
        "\n<b>Moderation</b> (admins only)\n"
        "/mute /unmute /ban /kick /warn\n"
        "/promote /demote – manage admins\n"
        "/lock /unlock – lock or unlock the group\n"
        "/antilink on|off – auto-delete links\n"
        "/setwelcome &lt;text&gt;, /setgoodbye &lt;text&gt;, /setrules &lt;text&gt;\n"
        "/addreply &lt;kw&gt; | &lt;reply&gt;, /delreply &lt;kw&gt;, /replies\n"
        "\n<b>DM</b> — just chat with me privately. I reply, and yes, I bite back if insulted."
    )
    await update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)


async def cmd_about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "<b>Group Manager Bot</b>\n"
        "Built with python-telegram-bot v20+ and SQLite.\n"
        "Features: welcomes, goodbyes, auto-replies, /tagall, moderation, "
        "warnings, flood protection."
    )
    await update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)


async def cmd_rules(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    settings = await _run(db.get_chat_settings, chat.id)
    rules = settings.get("rules") or DEFAULT_RULES
    await update.effective_message.reply_text(rules, parse_mode=ParseMode.HTML)


async def cmd_ping(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    start = time.monotonic()
    msg = await update.effective_message.reply_text("🏓 Pinging…")
    latency_ms = int((time.monotonic() - start) * 1000)
    await msg.edit_text(f"🏓 Pong! <code>{latency_ms} ms</code>",
                        parse_mode=ParseMode.HTML)


async def cmd_joke(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.effective_message.reply_text(random.choice(JOKES))


async def cmd_settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    s = await _run(db.get_chat_settings, chat.id)
    welcome = s.get("welcome_msg") or "<i>(default)</i>"
    goodbye = s.get("goodbye_msg") or "<i>(default)</i>"
    rules = "<i>(custom)</i>" if s.get("rules") else "<i>(default)</i>"
    text = (
        f"<b>Settings for {safe_html(chat.title or 'this chat')}</b>\n\n"
        f"<b>Welcome:</b> {safe_html(welcome) if not welcome.startswith('<i>') else welcome}\n"
        f"<b>Goodbye:</b> {safe_html(goodbye) if not goodbye.startswith('<i>') else goodbye}\n"
        f"<b>Rules:</b> {rules}\n"
    )
    await update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)


# ---------- setters (admins) ----------

async def cmd_setwelcome(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_admin_or_reply(update, context):
        return
    text = " ".join(context.args) if context.args else ""
    await _run(db.set_chat_setting, update.effective_chat.id, "welcome_msg",
               text or None)
    await update.effective_message.reply_text(
        "✅ Welcome message updated." if text else "✅ Welcome message reset to default."
    )


async def cmd_setgoodbye(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_admin_or_reply(update, context):
        return
    text = " ".join(context.args) if context.args else ""
    await _run(db.set_chat_setting, update.effective_chat.id, "goodbye_msg",
               text or None)
    await update.effective_message.reply_text(
        "✅ Goodbye message updated." if text else "✅ Goodbye message reset."
    )


async def cmd_setrules(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await ensure_admin_or_reply(update, context):
        return
    text = " ".join(context.args) if context.args else ""
    await _run(db.set_chat_setting, update.effective_chat.id, "rules",
               text or None)
    await update.effective_message.reply_text(
        "✅ Rules updated." if text else "✅ Rules reset to default."
    )


# ---------- helper ----------

async def _run(fn, *args, **kwargs):
    import asyncio
    return await asyncio.to_thread(fn, *args, **kwargs)
