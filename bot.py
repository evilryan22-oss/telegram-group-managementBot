"""Entrypoint: wire up handlers and start polling."""
from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CallbackQueryHandler,
    ChatMemberHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

import database as db
from config import load_settings
from utils.logger import setup_logging

from handlers import admin as admin_h
from handlers import commands as cmd_h
from handlers import dm as dm_h
from handlers import fun as fun_h
from handlers import groupctl as gc_h
from handlers import members as members_h
from handlers import quiz as quiz_h
from handlers import replies as replies_h
from handlers import tagall as tagall_h
from handlers import tictactoe as ttt_h
from handlers import weather as weather_h

log = logging.getLogger("bot")


async def _on_error(update: object, context) -> None:  # noqa: ANN001
    log.exception("Unhandled error while processing update: %s",
                  context.error if context else "n/a")


def build_application(settings) -> Application:
    app = ApplicationBuilder().token(settings.bot_token).build()

    # ----- core commands -----
    app.add_handler(CommandHandler("start", cmd_h.cmd_start))
    app.add_handler(CommandHandler("help", cmd_h.cmd_help))
    app.add_handler(CommandHandler("about", cmd_h.cmd_about))
    app.add_handler(CommandHandler("rules", cmd_h.cmd_rules))
    app.add_handler(CommandHandler("ping", cmd_h.cmd_ping))
    app.add_handler(CommandHandler("settings", cmd_h.cmd_settings))
    app.add_handler(CommandHandler("setwelcome", cmd_h.cmd_setwelcome))
    app.add_handler(CommandHandler("setgoodbye", cmd_h.cmd_setgoodbye))
    app.add_handler(CommandHandler("setrules", cmd_h.cmd_setrules))

    # ----- fun -----
    app.add_handler(CommandHandler("joke", fun_h.cmd_joke))
    app.add_handler(CommandHandler("riddle", fun_h.cmd_riddle))
    app.add_handler(CommandHandler("truth", fun_h.cmd_truth))
    app.add_handler(CommandHandler("dare", fun_h.cmd_dare))
    app.add_handler(CommandHandler("truthordare", fun_h.cmd_truthordare))
    app.add_handler(CommandHandler("tod", fun_h.cmd_truthordare))
    app.add_handler(CommandHandler("puzzle", fun_h.cmd_puzzle))
    for name, handler in fun_h.REACTION_HANDLERS.items():
        app.add_handler(CommandHandler(name, handler))

    # ----- quiz / weather / tic-tac-toe -----
    app.add_handler(CommandHandler("quiz", quiz_h.cmd_quiz))
    app.add_handler(CommandHandler("weather", weather_h.cmd_weather))
    app.add_handler(CommandHandler("ttt", ttt_h.cmd_ttt))
    app.add_handler(CommandHandler("tictactoe", ttt_h.cmd_ttt))
    app.add_handler(CallbackQueryHandler(ttt_h.ttt_callback, pattern=r"^ttt\|"))

    # ----- tagall / tagadmins -----
    app.add_handler(CommandHandler("tagall", tagall_h.cmd_tagall))
    app.add_handler(CommandHandler("tagadmins", gc_h.cmd_tagadmins))
    app.add_handler(CommandHandler("admins", gc_h.cmd_tagadmins))

    # ----- moderation -----
    app.add_handler(CommandHandler("mute", admin_h.cmd_mute))
    app.add_handler(CommandHandler("unmute", admin_h.cmd_unmute))
    app.add_handler(CommandHandler("ban", admin_h.cmd_ban))
    app.add_handler(CommandHandler("kick", admin_h.cmd_kick))
    app.add_handler(CommandHandler("warn", admin_h.cmd_warn))

    # ----- group control -----
    app.add_handler(CommandHandler("promote", gc_h.cmd_promote))
    app.add_handler(CommandHandler("demote", gc_h.cmd_demote))
    app.add_handler(CommandHandler("antilink", gc_h.cmd_antilink))
    app.add_handler(CommandHandler("lock", gc_h.cmd_lock))
    app.add_handler(CommandHandler("lockgroup", gc_h.cmd_lock))
    app.add_handler(CommandHandler("unlock", gc_h.cmd_unlock))
    app.add_handler(CommandHandler("unlockgroup", gc_h.cmd_unlock))

    # ----- auto replies management -----
    app.add_handler(CommandHandler("addreply", replies_h.cmd_addreply))
    app.add_handler(CommandHandler("delreply", replies_h.cmd_delreply))
    app.add_handler(CommandHandler("replies", replies_h.cmd_listreplies))

    # ----- member tracking -----
    app.add_handler(ChatMemberHandler(
        members_h.chat_member_update, ChatMemberHandler.CHAT_MEMBER
    ))

    # ----- passive handlers (order matters via 'group' param) -----
    # group 0: record speakers
    app.add_handler(MessageHandler(
        filters.ChatType.GROUPS & ~filters.StatusUpdate.ALL,
        members_h.track_message_author,
    ), group=0)
    # group 1: antilink filter (may delete the message)
    app.add_handler(MessageHandler(
        filters.ChatType.GROUPS & (filters.TEXT | filters.CAPTION) & ~filters.COMMAND,
        gc_h.antilink_filter,
    ), group=1)
    # group 2: insult-back in groups (only when targeted)
    app.add_handler(MessageHandler(
        filters.ChatType.GROUPS & filters.TEXT & ~filters.COMMAND,
        dm_h.handle_group_insult,
    ), group=2)
    # group 3: existing keyword / greeting auto-replies
    app.add_handler(MessageHandler(
        filters.TEXT & filters.ChatType.GROUPS & ~filters.COMMAND,
        replies_h.handle_group_text,
    ), group=3)
    # private chats: full DM conversation handler
    app.add_handler(MessageHandler(
        filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND,
        dm_h.handle_dm,
    ), group=1)

    app.add_error_handler(_on_error)
    return app


def main() -> None:
    settings = load_settings()
    setup_logging(settings.log_level)
    db.init_db(settings.database_url)
    log.info("Database ready at %s", settings.database_url)

    app = build_application(settings)
    log.info("Starting bot (long polling)…")
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
