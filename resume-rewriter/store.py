"""SQLite-backed unlock-key store.

One key per active subscription. Webhook writes on checkout.session.completed,
marks inactive on customer.subscription.deleted.
"""

from __future__ import annotations

import os
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime
from typing import Optional

DB_PATH = os.environ.get("UNLOCK_DB_PATH", "unlock.db")

_lock = threading.Lock()


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db() -> None:
    with _lock, _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS unlock_keys (
                key TEXT PRIMARY KEY,
                email TEXT NOT NULL,
                stripe_customer_id TEXT,
                stripe_subscription_id TEXT UNIQUE,
                stripe_checkout_session_id TEXT UNIQUE,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_unlock_sub ON unlock_keys(stripe_subscription_id)"
        )


@contextmanager
def _cursor():
    conn = _connect()
    try:
        with _lock:
            yield conn
            conn.commit()
    finally:
        conn.close()


def upsert_key(
    key: str,
    email: str,
    customer_id: Optional[str],
    subscription_id: Optional[str],
    checkout_session_id: Optional[str],
) -> None:
    with _cursor() as conn:
        conn.execute(
            """
            INSERT INTO unlock_keys (
                key, email, stripe_customer_id, stripe_subscription_id,
                stripe_checkout_session_id, active, created_at
            ) VALUES (?, ?, ?, ?, ?, 1, ?)
            ON CONFLICT(stripe_checkout_session_id) DO NOTHING
            """,
            (
                key,
                email,
                customer_id,
                subscription_id,
                checkout_session_id,
                datetime.utcnow().isoformat(timespec="seconds"),
            ),
        )


def find_by_checkout_session(session_id: str) -> Optional[sqlite3.Row]:
    with _cursor() as conn:
        row = conn.execute(
            "SELECT * FROM unlock_keys WHERE stripe_checkout_session_id = ?",
            (session_id,),
        ).fetchone()
        return row


def is_key_active(key: str) -> bool:
    if not key:
        return False
    with _cursor() as conn:
        row = conn.execute(
            "SELECT active FROM unlock_keys WHERE key = ?",
            (key,),
        ).fetchone()
        return bool(row and row["active"])


def deactivate_by_subscription(subscription_id: str) -> None:
    with _cursor() as conn:
        conn.execute(
            "UPDATE unlock_keys SET active = 0 WHERE stripe_subscription_id = ?",
            (subscription_id,),
        )
