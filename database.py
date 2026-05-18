"""SQLite persistence layer.

All calls are synchronous SQLite operations wrapped through asyncio.to_thread
from the calling code, so handlers stay non-blocking.
"""
from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from typing import Iterable, List, Optional, Tuple

_LOCK = threading.RLock()
_DB_PATH = "bot.db"


def init_db(db_path: str) -> None:
    """Initialise the database file and create tables if missing."""
    global _DB_PATH
    _DB_PATH = db_path
    with _connect() as conn:
        c = conn.cursor()
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS chats (
                chat_id     INTEGER PRIMARY KEY,
                title       TEXT,
                welcome_msg TEXT,
                goodbye_msg TEXT,
                rules       TEXT
            );

            CREATE TABLE IF NOT EXISTS members (
                chat_id     INTEGER NOT NULL,
                user_id     INTEGER NOT NULL,
                username    TEXT,
                first_name  TEXT,
                last_seen   INTEGER NOT NULL DEFAULT (strftime('%s','now')),
                PRIMARY KEY (chat_id, user_id)
            );

            CREATE TABLE IF NOT EXISTS warnings (
                chat_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                count   INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (chat_id, user_id)
            );

            CREATE TABLE IF NOT EXISTS auto_replies (
                chat_id INTEGER NOT NULL,
                keyword TEXT NOT NULL,
                reply   TEXT NOT NULL,
                PRIMARY KEY (chat_id, keyword)
            );
            """
        )
        conn.commit()


@contextmanager
def _connect():
    with _LOCK:
        conn = sqlite3.connect(_DB_PATH, timeout=30, isolation_level=None)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        try:
            yield conn
        finally:
            conn.close()


# ---------- chats ----------

def upsert_chat(chat_id: int, title: Optional[str]) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT INTO chats(chat_id, title) VALUES(?, ?) "
            "ON CONFLICT(chat_id) DO UPDATE SET title=excluded.title",
            (chat_id, title),
        )


def set_chat_setting(chat_id: int, field: str, value: Optional[str]) -> None:
    if field not in {"welcome_msg", "goodbye_msg", "rules"}:
        raise ValueError(f"Invalid chat setting: {field}")
    with _connect() as conn:
        conn.execute(
            f"INSERT INTO chats(chat_id, {field}) VALUES(?, ?) "
            f"ON CONFLICT(chat_id) DO UPDATE SET {field}=excluded.{field}",
            (chat_id, value),
        )


def get_chat_settings(chat_id: int) -> dict:
    with _connect() as conn:
        row = conn.execute(
            "SELECT welcome_msg, goodbye_msg, rules FROM chats WHERE chat_id=?",
            (chat_id,),
        ).fetchone()
    if not row:
        return {"welcome_msg": None, "goodbye_msg": None, "rules": None}
    return {"welcome_msg": row[0], "goodbye_msg": row[1], "rules": row[2]}


# ---------- members ----------

def upsert_member(chat_id: int, user_id: int,
                  username: Optional[str], first_name: Optional[str]) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT INTO members(chat_id, user_id, username, first_name) "
            "VALUES(?, ?, ?, ?) "
            "ON CONFLICT(chat_id, user_id) DO UPDATE SET "
            "username=excluded.username, first_name=excluded.first_name, "
            "last_seen=strftime('%s','now')",
            (chat_id, user_id, username, first_name),
        )


def remove_member(chat_id: int, user_id: int) -> None:
    with _connect() as conn:
        conn.execute(
            "DELETE FROM members WHERE chat_id=? AND user_id=?",
            (chat_id, user_id),
        )


def list_members(chat_id: int) -> List[Tuple[int, Optional[str], Optional[str]]]:
    """Returns [(user_id, username, first_name), ...]."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT user_id, username, first_name FROM members WHERE chat_id=?",
            (chat_id,),
        ).fetchall()
    return [(r[0], r[1], r[2]) for r in rows]


# ---------- warnings ----------

def add_warning(chat_id: int, user_id: int) -> int:
    with _connect() as conn:
        conn.execute(
            "INSERT INTO warnings(chat_id, user_id, count) VALUES(?, ?, 1) "
            "ON CONFLICT(chat_id, user_id) DO UPDATE SET count=count+1",
            (chat_id, user_id),
        )
        row = conn.execute(
            "SELECT count FROM warnings WHERE chat_id=? AND user_id=?",
            (chat_id, user_id),
        ).fetchone()
    return int(row[0]) if row else 0


def reset_warnings(chat_id: int, user_id: int) -> None:
    with _connect() as conn:
        conn.execute(
            "DELETE FROM warnings WHERE chat_id=? AND user_id=?",
            (chat_id, user_id),
        )


# ---------- auto replies ----------

def set_auto_reply(chat_id: int, keyword: str, reply: str) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT INTO auto_replies(chat_id, keyword, reply) VALUES(?, ?, ?) "
            "ON CONFLICT(chat_id, keyword) DO UPDATE SET reply=excluded.reply",
            (chat_id, keyword.lower(), reply),
        )


def delete_auto_reply(chat_id: int, keyword: str) -> None:
    with _connect() as conn:
        conn.execute(
            "DELETE FROM auto_replies WHERE chat_id=? AND keyword=?",
            (chat_id, keyword.lower()),
        )


def list_auto_replies(chat_id: int) -> List[Tuple[str, str]]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT keyword, reply FROM auto_replies WHERE chat_id=?",
            (chat_id,),
        ).fetchall()
    return [(r[0], r[1]) for r in rows]


# ---------- chat flags (toggles like antilink) ----------

def _ensure_flags_table() -> None:
    with _connect() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS chat_flags ("
            "chat_id INTEGER NOT NULL, "
            "name    TEXT    NOT NULL, "
            "value   INTEGER NOT NULL DEFAULT 0, "
            "PRIMARY KEY (chat_id, name))"
        )


def set_flag(chat_id: int, name: str, value: int) -> None:
    _ensure_flags_table()
    with _connect() as conn:
        conn.execute(
            "INSERT INTO chat_flags(chat_id, name, value) VALUES(?,?,?) "
            "ON CONFLICT(chat_id, name) DO UPDATE SET value=excluded.value",
            (chat_id, name, int(value)),
        )


def get_flag(chat_id: int, name: str, default: int = 0) -> int:
    _ensure_flags_table()
    with _connect() as conn:
        row = conn.execute(
            "SELECT value FROM chat_flags WHERE chat_id=? AND name=?",
            (chat_id, name),
        ).fetchone()
    return int(row[0]) if row else int(default)
