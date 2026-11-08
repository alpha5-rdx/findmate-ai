"""SQLite persistence layer. All SQL lives here."""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Optional

import numpy as np
import pandas as pd

from config import DATA_DIR, DB_PATH, UPLOAD_DIR

SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    kind          TEXT NOT NULL CHECK (kind IN ('lost','found')),
    name          TEXT NOT NULL,
    description   TEXT NOT NULL DEFAULT '',
    category      TEXT NOT NULL,
    location      TEXT NOT NULL,
    event_date    TEXT NOT NULL,
    image_path    TEXT,
    contact_name  TEXT NOT NULL DEFAULT '',
    contact_email TEXT NOT NULL DEFAULT '',
    contact_number TEXT NOT NULL DEFAULT '',
    status        TEXT NOT NULL DEFAULT 'open' CHECK (status IN ('open','resolved')),
    embedding     BLOB,
    created_at    TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS matches (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    lost_id     INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    found_id    INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    semantic    REAL NOT NULL,
    score       REAL NOT NULL,
    status      TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','resolved')),
    created_at  TEXT NOT NULL,
    UNIQUE (lost_id, found_id)
);
CREATE INDEX IF NOT EXISTS idx_items_kind_status ON items(kind, status);
"""


@contextmanager
def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Create folders, tables and indexes if missing (idempotent)."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    with connect() as conn:
        conn.executescript(SCHEMA)
        # Lightweight migration for databases created before contact numbers existed.
        cols = {r[1] for r in conn.execute('PRAGMA table_info(items)')}
        if 'contact_number' not in cols:
            conn.execute("ALTER TABLE items ADD COLUMN contact_number TEXT NOT NULL DEFAULT ''")


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _to_blob(vec: Optional[np.ndarray]) -> Optional[bytes]:
    return None if vec is None else np.asarray(vec, dtype=np.float32).tobytes()


def blob_to_vec(blob: Optional[bytes]) -> Optional[np.ndarray]:
    return None if blob is None else np.frombuffer(blob, dtype=np.float32)


# ---------------------------------------------------------------- items
def add_item(kind, name, description, category, location, event_date,
             image_path, contact_name, contact_email, embedding,
             contact_number="") -> int:
    with connect() as conn:
        cur = conn.execute(
            """INSERT INTO items (kind,name,description,category,location,event_date,
               image_path,contact_name,contact_email,embedding,created_at,contact_number)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (kind, name, description, category, location, str(event_date),
             image_path, contact_name, contact_email, _to_blob(embedding), _now(), contact_number),
        )
        return cur.lastrowid


def update_item(item_id, name, description, category, location, event_date,
                image_path, embedding, contact_number=None) -> None:
    with connect() as conn:
        conn.execute(
            """UPDATE items SET name=?,description=?,category=?,location=?,event_date=?,
               image_path=?,embedding=?,contact_number=COALESCE(?,contact_number) WHERE id=?""",
            (name, description, category, location, str(event_date), image_path,
             _to_blob(embedding), contact_number, item_id),
        )


def delete_item(item_id: int) -> None:
    with connect() as conn:  # matches removed via ON DELETE CASCADE
        conn.execute("DELETE FROM items WHERE id=?", (item_id,))


def get_item(item_id: int) -> Optional[dict]:
    with connect() as conn:
        row = conn.execute("SELECT * FROM items WHERE id=?", (item_id,)).fetchone()
    return dict(row) if row else None


def list_items(kind: Optional[str] = None, status: Optional[str] = None,
               email: Optional[str] = None) -> list[dict]:
    sql, args = "SELECT * FROM items WHERE 1=1", []
    if kind:
        sql += " AND kind=?"; args.append(kind)
    if status:
        sql += " AND status=?"; args.append(status)
    if email:
        sql += " AND lower(contact_email)=lower(?)"; args.append(email)
    sql += " ORDER BY created_at DESC, id DESC"
    with connect() as conn:
        return [dict(r) for r in conn.execute(sql, args).fetchall()]


def items_dataframe(kind: Optional[str] = None) -> pd.DataFrame:
    rows = list_items(kind)
    df = pd.DataFrame(rows)
    return df.drop(columns=["embedding"], errors="ignore")


def set_embedding(item_id: int, embedding: np.ndarray) -> None:
    with connect() as conn:
        conn.execute("UPDATE items SET embedding=? WHERE id=?", (_to_blob(embedding), item_id))


def count_items() -> int:
    with connect() as conn:
        return conn.execute("SELECT COUNT(*) FROM items").fetchone()[0]


# -------------------------------------------------------------- matches
def replace_pending_matches(rows: list[tuple[int, int, float, float]]) -> None:
    """Replace all *pending* matches with freshly computed ones.
    Resolved matches are kept. rows = (lost_id, found_id, semantic, score)."""
    with connect() as conn:
        conn.execute("DELETE FROM matches WHERE status='pending'")
        for lost_id, found_id, sem, score in rows:
            conn.execute(
                """INSERT OR IGNORE INTO matches (lost_id,found_id,semantic,score,created_at)
                   VALUES (?,?,?,?,?)""",
                (lost_id, found_id, sem, score, _now()),
            )


def list_matches(status: Optional[str] = None, min_score: float = 0.0) -> list[dict]:
    sql = """SELECT m.*, l.name AS lost_name, l.description AS lost_desc,
                    l.location AS lost_location, l.category AS lost_category,
                    l.image_path AS lost_image, l.contact_email AS lost_email,
                    l.contact_name AS lost_contact, l.contact_number AS lost_phone,
                    f.name AS found_name, f.description AS found_desc,
                    f.location AS found_location, f.category AS found_category,
                    f.image_path AS found_image, f.contact_email AS found_email,
                    f.contact_name AS found_contact, f.contact_number AS found_phone
             FROM matches m
             JOIN items l ON l.id = m.lost_id
             JOIN items f ON f.id = m.found_id
             WHERE m.score >= ?"""
    args: list = [min_score]
    if status:
        sql += " AND m.status=?"; args.append(status)
    sql += " ORDER BY m.score DESC"
    with connect() as conn:
        return [dict(r) for r in conn.execute(sql, args).fetchall()]


def resolve_match(match_id: int) -> None:
    """Mark a match resolved and close both underlying reports."""
    with connect() as conn:
        row = conn.execute("SELECT lost_id, found_id FROM matches WHERE id=?",
                           (match_id,)).fetchone()
        if not row:
            return
        conn.execute("UPDATE matches SET status='resolved' WHERE id=?", (match_id,))
        conn.execute("UPDATE items SET status='resolved' WHERE id IN (?,?)",
                     (row["lost_id"], row["found_id"]))
        # Other pending matches involving closed items are no longer actionable.
        conn.execute("""DELETE FROM matches WHERE status='pending'
                        AND (lost_id IN (?,?) OR found_id IN (?,?))""",
                     (row["lost_id"], row["found_id"], row["lost_id"], row["found_id"]))


def reopen_item(item_id: int) -> None:
    with connect() as conn:
        conn.execute("UPDATE items SET status='open' WHERE id=?", (item_id,))
        conn.execute("DELETE FROM matches WHERE status='resolved' AND (lost_id=? OR found_id=?)",
                     (item_id, item_id))


def stats(min_score: float) -> dict:
    with connect() as conn:
        q = lambda s, a=(): conn.execute(s, a).fetchone()[0]  # noqa: E731
        return {
            "lost": q("SELECT COUNT(*) FROM items WHERE kind='lost'"),
            "found": q("SELECT COUNT(*) FROM items WHERE kind='found'"),
            "open_lost": q("SELECT COUNT(*) FROM items WHERE kind='lost' AND status='open'"),
            "open_found": q("SELECT COUNT(*) FROM items WHERE kind='found' AND status='open'"),
            "matches": q("SELECT COUNT(*) FROM matches WHERE status='pending' AND score>=?",
                         (min_score,)),
            "resolved": q("SELECT COUNT(*) FROM matches WHERE status='resolved'"),
        }
