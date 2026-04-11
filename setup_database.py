#!/usr/bin/env python3
"""
SportsGuard AI — Database Setup (Module F)
Initializes the SQLite database schema with all required tables,
indexes, and constraints for the SportsGuard content-protection pipeline.

Usage:
    python setup_database.py          # Create tables (safe, won't drop existing)
    python setup_database.py --reset  # Drop and recreate all tables
    python setup_database.py --seed   # Reset + insert sample seed data
"""

import argparse
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Default database path
# ---------------------------------------------------------------------------
DEFAULT_DB_PATH = "sportsguard.db"

# ---------------------------------------------------------------------------
# Schema version — bump this whenever the schema changes so migrations can
# detect drift between the expected and actual versions.
# ---------------------------------------------------------------------------
SCHEMA_VERSION = 2

# ---------------------------------------------------------------------------
# DDL statements
# ---------------------------------------------------------------------------
CREATE_OFFICIAL_CONTENT = """
CREATE TABLE IF NOT EXISTS official_content (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT    NOT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_frames INTEGER NOT NULL,
    file_path   TEXT    NOT NULL
);
"""

CREATE_FINGERPRINTS = """
CREATE TABLE IF NOT EXISTS fingerprints (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id    INTEGER NOT NULL,
    frame_index INTEGER NOT NULL,
    phash       TEXT    NOT NULL,
    FOREIGN KEY (video_id) REFERENCES official_content(id) ON DELETE CASCADE,
    UNIQUE (video_id, frame_index)
);
"""

CREATE_DETECTIONS = """
CREATE TABLE IF NOT EXISTS detections (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id              INTEGER NOT NULL,
    source_url            TEXT    NOT NULL,
    platform              TEXT,
    c_plus_plus_confidence REAL   NOT NULL,
    gemini_classification TEXT,
    gemini_risk_score     INTEGER,
    gemini_reasoning      TEXT,
    status                TEXT    NOT NULL DEFAULT 'pending',
    detected_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (video_id) REFERENCES official_content(id) ON DELETE CASCADE
);
"""

CREATE_SCHEMA_META = """
CREATE TABLE IF NOT EXISTS schema_meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

# Performance indexes
INDEX_STATEMENTS = [
    "CREATE INDEX IF NOT EXISTS idx_fingerprints_phash    ON fingerprints(phash);",
    "CREATE INDEX IF NOT EXISTS idx_fingerprints_video_id ON fingerprints(video_id);",
    "CREATE INDEX IF NOT EXISTS idx_detections_video_id   ON detections(video_id);",
    "CREATE INDEX IF NOT EXISTS idx_detections_detected_at ON detections(detected_at);",
]

# Tables in dependency order (children first for safe drops)
ALL_TABLES = ["detections", "fingerprints", "official_content", "schema_meta"]


# ---------------------------------------------------------------------------
# Core setup helpers
# ---------------------------------------------------------------------------

def _enable_pragmas(conn: sqlite3.Connection) -> None:
    """Turn on WAL mode and enforce foreign keys."""
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")


def drop_all_tables(conn: sqlite3.Connection) -> None:
    """Drop every application table (children first to respect FK order)."""
    for table in ALL_TABLES:
        conn.execute(f"DROP TABLE IF EXISTS {table};")
    conn.commit()
    print("[setup] All tables dropped.")


def create_all_tables(conn: sqlite3.Connection) -> None:
    """Create every table and index idempotently."""
    conn.execute(CREATE_OFFICIAL_CONTENT)
    conn.execute(CREATE_FINGERPRINTS)
    conn.execute(CREATE_DETECTIONS)
    conn.execute(CREATE_SCHEMA_META)

    for idx in INDEX_STATEMENTS:
        conn.execute(idx)

    # Record schema version
    conn.execute(
        "INSERT OR REPLACE INTO schema_meta (key, value) VALUES (?, ?);",
        ("schema_version", str(SCHEMA_VERSION)),
    )
    conn.commit()
    print(f"[setup] All tables and indexes created (schema v{SCHEMA_VERSION}).")


def verify_integrity(conn: sqlite3.Connection) -> bool:
    """Run SQLite integrity check and return True if OK."""
    result = conn.execute("PRAGMA integrity_check;").fetchone()
    ok = result[0] == "ok"
    status = "PASSED ✓" if ok else f"FAILED ✗ — {result[0]}"
    print(f"[setup] Integrity check: {status}")
    return ok


def seed_data(conn: sqlite3.Connection) -> None:
    """Insert a small amount of test seed data."""
    now = datetime.now(timezone.utc).isoformat()

    # Official content
    conn.execute(
        "INSERT INTO official_content (title, uploaded_at, total_frames, file_path) VALUES (?, ?, ?, ?);",
        ("IPL 2026 — MI vs CSK Highlights", now, 120, "uploads/ipl_mi_vs_csk.mp4"),
    )
    conn.execute(
        "INSERT INTO official_content (title, uploaded_at, total_frames, file_path) VALUES (?, ?, ?, ?);",
        ("Premier League — Arsenal vs Chelsea", now, 90, "uploads/pl_ars_vs_che.mp4"),
    )

    # A handful of dummy fingerprints for video 1
    dummy_hashes = [
        (1, i, f"{i:016x}") for i in range(5)
    ]
    conn.executemany(
        "INSERT INTO fingerprints (video_id, frame_index, phash) VALUES (?, ?, ?);",
        dummy_hashes,
    )

    # A sample detection
    conn.execute(
        """INSERT INTO detections
               (video_id, source_url, platform, c_plus_plus_confidence,
                gemini_classification, gemini_risk_score, gemini_reasoning, status, detected_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);""",
        (
            1,
            "https://twitter.com/pirate/status/99999",
            "Twitter",
            96.875,
            "Piracy",
            92,
            "Raw re-upload with no commentary or overlays.",
            "classified",
            now,
        ),
    )
    conn.commit()
    print("[setup] Seed data inserted.")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def init_database(db_path: str = DEFAULT_DB_PATH, *, reset: bool = False, seed: bool = False) -> None:
    """
    Main entry point: create (or reset) the database at *db_path*.

    Parameters
    ----------
    db_path : str
        Path to the SQLite file.
    reset : bool
        If True, drop all tables first.
    seed : bool
        If True, insert sample data after creation.
    """
    conn = sqlite3.connect(db_path)
    try:
        _enable_pragmas(conn)

        if reset:
            drop_all_tables(conn)

        create_all_tables(conn)
        verify_integrity(conn)

        if seed:
            seed_data(conn)

        print(f"[setup] Database ready → {Path(db_path).resolve()}")
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="SportsGuard AI — Database Setup")
    parser.add_argument("--reset", action="store_true", help="Drop and recreate all tables")
    parser.add_argument("--seed", action="store_true", help="Insert sample seed data (implies --reset)")
    parser.add_argument("--db", default=DEFAULT_DB_PATH, help=f"Database path (default: {DEFAULT_DB_PATH})")
    args = parser.parse_args()

    if args.seed:
        args.reset = True  # seed implies reset for clean state

    init_database(args.db, reset=args.reset, seed=args.seed)


if __name__ == "__main__":
    main()
