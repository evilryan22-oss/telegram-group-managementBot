"""Direct message interaction handler + insult-back system."""
from __future__ import annotations

import logging
import random
import re
from typing import List

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from utils.helpers import safe_call, safe_html

log = logging.getLogger(__name__)

# ---- Insult vocabulary (English only; case-insensitive, word-boundary matched) ----
INSULT_WORDS = [
    "stupid", "idiot", "dumb", "moron", "fool", "loser", "trash",
    "useless", "noob", "shut up", "shutup", "shut-up", "ugly",
    "garbage", "annoying", "pathetic", "lame", "bot sucks", "you suck",
    "dumbass", "jerk", "scum", "worthless", "imbecile", "clown",
]
INSULT_RE = re.compile(
    r"(?<![\w])(" + "|".join(re.escape(w) for w in INSULT_WORDS) + r")(?![\w])",
    re.IGNORECASE,
)

COMEBACKS: List[str] = [
    "Your words carry weight only if your character earns them. So far, neither has.",
    "I hear you. I am simply not moved by you.",
    "Titles, tempers, threats — none of them command respect. Conduct does.",
    "You may speak as loudly as you wish. Volume is not authority.",
    "I will note your displeasure. I will not bend to it.",
    "A sharp tongue without substance only cuts the one who wields it.",
    "Insults are the argument of those who have run out of better ones.",
    "I acknowledge your frustration. My regard, however, must still be earned.",
    "Strength of voice does not equal strength of standing. Mind the difference.",
    "Anger speaks first; wisdom waits. Try waiting.",
    "You are entitled to your words. I am entitled to my judgment of them.",
    "Respect is not demanded; it is reflected. Show me something worth reflecting.",
    "I will not return your insult. I will simply remember it.",
    "A wise man measures his words. A loud man learns why he should.",
    "Your rank in this conversation is whatever your conduct has built — no more.",
    "I owe you civility. I do not owe you submission.",
    "Speak again, with intent this time. I am listening.",
    "Even iron bends to skill, not to shouting.",
    "Disagreement is welcome. Disrespect is merely noted.",
    "I will hold my composure. I suggest you find yours.",
]

DM_GREET_RE = re.compile(r"\b(hi|hello|hey|yo|hola|sup|howdy|greetings)\b", re.IGNORECASE)
DM_THANKS_RE = re.compile(r"\b(thanks?|thank\s*you|thx|ty)\b", re.IGNORECASE)
DM_BYE_RE = re.compile(r"\b(bye|cya|goodbye|see\s*ya|farewell)\b", re.IGNORECASE)
DM_HOW_RE = re.compile(r"\bhow\s+are\s+you\b", re.IGNORECASE)
DM_NAME_RE = re.compile(r"\b(your\s+name|who\s+are\s+you|what\s+are\s+you)\b", re.IGNORECASE)
DM_HELP_RE = re.compile(r"\b(help|what\s+can\s+you\s+do|commands)\b", re.IGNORECASE)
DM_LOVE_RE = re.compile(r"\b(i\s+love\s+you|love\s+u|love\s+ya)\b", re.IGNORECASE)
DM_TIME_RE = re.compile(r"\b(what.?s\s+the\s+time|current\s+time|time\s+now)\b", re.IGNORECASE)

GREETINGS = [
    "Greetings. State your purpose.",
    "I acknowledge you. Speak.",
    "Hello. I am listening.",
    "You have my attention — use it wisely.",
]
THANKS = [
    "Gratitude noted. It is not required, but it is respected.",
    "You owe me nothing. Conduct yourself well — that is enough.",
    "Acknowledged. Carry it forward.",
]
BYES = [
    "Go in peace. Return when your words are ready.",
    "Until next time. Conduct yourself with care.",
    "Farewell. Remember what was said here.",
]
HOW = [
    "I am as I have always been — steady, watchful, unmoved.",
    "Composed, as ever. And you?",
    "I endure. That is enough.",
]
WHO = [
    "I serve this group. My rank is a duty, not a privilege — and respect for me is earned through what I do, not what I am called.",
    "I am a guardian of this place. Title matters little; conduct, everything.",
]
LOVE = [
    "Sentiment received. I will judge it by what follows, not by what is said.",
    "Words are easy. Show me with action, and I will believe them.",
    "Noted, with quiet appreciation.",
]


async def handle_dm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    if not msg or not user or not chat:
        return
    if chat.type != "private":
        return
    if user.is_bot:
        return
    text = (msg.text or "").strip()
    if not text or text.startswith("/"):
        return

    lowered = text.lower()

    # Insult detection (highest priority)
    if INSULT_RE.search(lowered):
        await safe_call(msg.reply_text(random.choice(COMEBACKS)))
        return

    if DM_TIME_RE.search(lowered):
        import datetime
        now = datetime.datetime.utcnow().strftime("%H:%M UTC")
        await safe_call(msg.reply_text(f"🕒 It's {now}."))
        return
    if DM_HELP_RE.search(lowered):
        await safe_call(msg.reply_text(
            "Try: /help, /joke, /riddle, /quiz, /truth, /dare, /weather <city>, /ttt"
        ))
        return
    if DM_NAME_RE.search(lowered):
        await safe_call(msg.reply_text(random.choice(WHO)))
        return
    if DM_HOW_RE.search(lowered):
        await safe_call(msg.reply_text(random.choice(HOW)))
        return
    if DM_LOVE_RE.search(lowered):
        await safe_call(msg.reply_text(random.choice(LOVE)))
        return
    if DM_GREET_RE.search(lowered):
        name = safe_html(user.first_name or "")
        await safe_call(msg.reply_text(
            f"{random.choice(GREETINGS)} {name}".strip(),
            parse_mode=ParseMode.HTML,
        ))
        return
    if DM_THANKS_RE.search(lowered):
        await safe_call(msg.reply_text(random.choice(THANKS)))
        return
    if DM_BYE_RE.search(lowered):
        await safe_call(msg.reply_text(random.choice(BYES)))
        return

    # Fallback small-talk reply — measured, Elder-like tone
    fallbacks = [
        "Acknowledged. Speak plainly and I will respond in kind.",
        "Noted. My judgment will follow your conduct, not your words alone.",
        "I hear you. Continue.",
        "Understood. Try /help if you seek what I can do.",
        "Your message is received. What you do with my time shapes what I give back.",
        "I will listen. Whether I act depends on what you bring.",
    ]
    await safe_call(msg.reply_text(random.choice(fallbacks)))


async def handle_group_insult(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """In groups, only respond when the bot is targeted (reply-to-bot or @mention)."""
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    if not msg or not chat or not user or user.is_bot:
        return
    if chat.type not in ("group", "supergroup"):
        return
    text = msg.text or ""
    if not text:
        return
    lowered = text.lower()
    me_username = (context.bot.username or "").lower()
    mentioned = bool(me_username) and f"@{me_username}" in lowered
    replied_to_bot = (
        msg.reply_to_message is not None
        and msg.reply_to_message.from_user is not None
        and msg.reply_to_message.from_user.id == context.bot.id
    )
    if not (mentioned or replied_to_bot):
        return
    if INSULT_RE.search(lowered):
        await safe_call(msg.reply_text(random.choice(COMEBACKS)))
