"""Tic-Tac-Toe with inline keyboard. Two-player or single-player vs bot."""
from __future__ import annotations

import logging
import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from utils.helpers import mention_html, safe_html

log = logging.getLogger(__name__)

EMPTY = " "
X = "❌"
O = "⭕"


@dataclass
class Game:
    chat_id: int
    message_id: int
    player_x: Tuple[int, str]
    player_o: Optional[Tuple[int, str]] = None  # None until accepted; (0,"Bot") for bot
    board: List[str] = field(default_factory=lambda: [EMPTY] * 9)
    turn: str = X  # whose mark moves next
    finished: bool = False
    vs_bot: bool = False


# (chat_id, message_id) -> Game
GAMES: Dict[Tuple[int, int], Game] = {}


def _render_board(g: Game) -> InlineKeyboardMarkup:
    rows = []
    for r in range(3):
        row = []
        for c in range(3):
            i = r * 3 + c
            cell = g.board[i]
            label = cell if cell != EMPTY else "·"
            row.append(InlineKeyboardButton(label, callback_data=f"ttt|{g.message_id}|{i}"))
        rows.append(row)
    if not g.finished and g.player_o is None:
        rows.append([InlineKeyboardButton("✋ Join as ⭕", callback_data=f"ttt|{g.message_id}|join")])
    rows.append([InlineKeyboardButton("🛑 End game", callback_data=f"ttt|{g.message_id}|end")])
    return InlineKeyboardMarkup(rows)


WIN_LINES = [
    (0, 1, 2), (3, 4, 5), (6, 7, 8),
    (0, 3, 6), (1, 4, 7), (2, 5, 8),
    (0, 4, 8), (2, 4, 6),
]


def _winner(board: List[str]) -> Optional[str]:
    for a, b, c in WIN_LINES:
        if board[a] != EMPTY and board[a] == board[b] == board[c]:
            return board[a]
    return None


def _full(board: List[str]) -> bool:
    return all(s != EMPTY for s in board)


def _bot_move(board: List[str], me: str, opp: str) -> int:
    # Try win, then block, then center, then corners, then random
    for i in range(9):
        if board[i] == EMPTY:
            board[i] = me
            if _winner(board) == me:
                board[i] = EMPTY
                return i
            board[i] = EMPTY
    for i in range(9):
        if board[i] == EMPTY:
            board[i] = opp
            if _winner(board) == opp:
                board[i] = EMPTY
                return i
            board[i] = EMPTY
    if board[4] == EMPTY:
        return 4
    for i in (0, 2, 6, 8):
        if board[i] == EMPTY:
            return i
    options = [i for i, v in enumerate(board) if v == EMPTY]
    return random.choice(options) if options else -1


def _status_text(g: Game) -> str:
    pname_x = safe_html(g.player_x[1] or "Player X")
    pname_o = safe_html(g.player_o[1] if g.player_o else "(waiting…)")
    if g.finished:
        w = _winner(g.board)
        if w == X:
            who = pname_x
            line = f"🏆 <b>{who}</b> ({X}) wins!"
        elif w == O:
            who = pname_o
            line = f"🏆 <b>{who}</b> ({O}) wins!"
        else:
            line = "🤝 Draw!"
    else:
        nxt = pname_x if g.turn == X else pname_o
        line = f"Turn: {g.turn} — {nxt}"
    return (f"🎮 <b>Tic-Tac-Toe</b>\n"
            f"{X} {pname_x}  vs  {O} {pname_o}\n\n{line}")


async def cmd_ttt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    chat = update.effective_chat
    if not user or not chat:
        return
    vs_bot = bool(context.args and context.args[0].lower() in ("bot", "ai", "cpu"))
    placeholder = await update.effective_message.reply_text("Setting up…")
    g = Game(
        chat_id=chat.id,
        message_id=placeholder.message_id,
        player_x=(user.id, user.first_name or user.username or f"user{user.id}"),
        player_o=(0, "Bot") if vs_bot else None,
        vs_bot=vs_bot,
    )
    GAMES[(chat.id, placeholder.message_id)] = g
    await placeholder.edit_text(
        _status_text(g),
        parse_mode=ParseMode.HTML,
        reply_markup=_render_board(g),
    )


async def ttt_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    if not q or not q.data:
        return
    try:
        _, mid_s, action = q.data.split("|", 2)
        mid = int(mid_s)
    except (ValueError, IndexError):
        await q.answer()
        return
    chat_id = q.message.chat.id
    g = GAMES.get((chat_id, mid))
    if not g:
        await q.answer("This game is no longer active.", show_alert=False)
        try:
            await q.edit_message_reply_markup(reply_markup=None)
        except Exception:  # noqa: BLE001
            pass
        return
    user = q.from_user

    if action == "end":
        if user.id != g.player_x[0] and (g.player_o is None or user.id != g.player_o[0]):
            await q.answer("Only the players can end the game.", show_alert=True)
            return
        g.finished = True
        GAMES.pop((chat_id, mid), None)
        await q.answer("Game ended.")
        await q.edit_message_text(_status_text(g) + "\n\n🛑 Ended.",
                                  parse_mode=ParseMode.HTML)
        return

    if action == "join":
        if g.player_o is not None:
            await q.answer("Already has a second player.", show_alert=False)
            return
        if user.id == g.player_x[0]:
            await q.answer("You're already player X.", show_alert=False)
            return
        g.player_o = (user.id, user.first_name or user.username or f"user{user.id}")
        await q.answer("Joined!")
        await q.edit_message_text(_status_text(g), parse_mode=ParseMode.HTML,
                                  reply_markup=_render_board(g))
        return

    # cell move
    try:
        idx = int(action)
    except ValueError:
        await q.answer()
        return
    if g.finished:
        await q.answer("Game over.", show_alert=False)
        return
    if g.player_o is None:
        await q.answer("Waiting for second player to join.", show_alert=False)
        return
    expected_uid = g.player_x[0] if g.turn == X else g.player_o[0]
    if user.id != expected_uid:
        await q.answer("Not your turn.", show_alert=False)
        return
    if not (0 <= idx < 9) or g.board[idx] != EMPTY:
        await q.answer("Invalid move.", show_alert=False)
        return
    g.board[idx] = g.turn
    w = _winner(g.board)
    if w or _full(g.board):
        g.finished = True
        await q.answer()
        await q.edit_message_text(_status_text(g), parse_mode=ParseMode.HTML,
                                  reply_markup=_render_board(g))
        GAMES.pop((chat_id, mid), None)
        return
    g.turn = O if g.turn == X else X
    # bot move
    if g.vs_bot and g.turn == O and not g.finished:
        bidx = _bot_move(g.board, O, X)
        if bidx >= 0:
            g.board[bidx] = O
            w = _winner(g.board)
            if w or _full(g.board):
                g.finished = True
            else:
                g.turn = X
    await q.answer()
    await q.edit_message_text(_status_text(g), parse_mode=ParseMode.HTML,
                              reply_markup=_render_board(g))
    if g.finished:
        GAMES.pop((chat_id, mid), None)
