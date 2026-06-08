import sqlite3
import os
from config import DB_PATH


def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS decks (
                id TEXT PRIMARY KEY,
                path TEXT UNIQUE NOT NULL,
                filename TEXT NOT NULL,
                category TEXT NOT NULL,
                elo INTEGER DEFAULT 1000,
                matches INTEGER DEFAULT 0,
                slide_count INTEGER DEFAULT 0,
                rendered INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS comparisons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                winner_id TEXT NOT NULL,
                loser_id TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)


def upsert_deck(deck_id, path, filename, category):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO decks (id, path, filename, category)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET path=excluded.path, filename=excluded.filename
        """, (deck_id, path, filename, category))


def get_decks_by_category(category):
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(
            "SELECT * FROM decks WHERE category = ? ORDER BY elo DESC, matches DESC",
            (category,)
        ).fetchall()]


def get_comparison_pair(category):
    with get_conn() as conn:
        decks = [dict(r) for r in conn.execute(
            "SELECT * FROM decks WHERE category = ? ORDER BY matches ASC",
            (category,)
        ).fetchall()]

        if len(decks) < 2:
            return None, None

        for i, a in enumerate(decks):
            for b in decks[i + 1:]:
                played = conn.execute("""
                    SELECT 1 FROM comparisons
                    WHERE category = ?
                    AND ((winner_id = ? AND loser_id = ?) OR (winner_id = ? AND loser_id = ?))
                """, (category, a['id'], b['id'], b['id'], a['id'])).fetchone()
                if not played:
                    return a, b

        return decks[0], decks[1]


def record_vote(category, winner_id, loser_id, new_winner_elo, new_loser_elo):
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO comparisons (category, winner_id, loser_id) VALUES (?, ?, ?)",
            (category, winner_id, loser_id)
        )
        conn.execute(
            "UPDATE decks SET elo = ?, matches = matches + 1 WHERE id = ?",
            (new_winner_elo, winner_id)
        )
        conn.execute(
            "UPDATE decks SET elo = ?, matches = matches + 1 WHERE id = ?",
            (new_loser_elo, loser_id)
        )


def mark_rendered(deck_id, slide_count):
    with get_conn() as conn:
        conn.execute(
            "UPDATE decks SET rendered = 1, slide_count = ? WHERE id = ?",
            (slide_count, deck_id)
        )


def get_deck(deck_id):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM decks WHERE id = ?", (deck_id,)).fetchone()
        return dict(row) if row else None


def get_category_stats(category):
    with get_conn() as conn:
        total = conn.execute(
            "SELECT COUNT(*) FROM decks WHERE category = ?", (category,)
        ).fetchone()[0]
        total_matches = conn.execute(
            "SELECT COUNT(*) FROM comparisons WHERE category = ?", (category,)
        ).fetchone()[0]
        return total, total_matches
