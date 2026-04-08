#!/usr/bin/env python3
"""
SportsGuard AI — Database Helpers
Reusable query functions wrapping SQLite3 for the SportsGuard pipeline.

All public functions accept an optional *db_path* so callers can point at
any database (useful for testing).  The module also exposes a lightweight
connection-pool helper that returns the same connection per-thread.
"""

import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

DEFAULT_DB_PATH = "sportsguard.db"

# ---------------------------------------------------------------------------
# Thread-local connection "pool" (one connection per thread for SQLite)
# ---------------------------------------------------------------------------
_local = threading.local()


def get_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """
    Return a thread-local SQLite connection with sensible defaults.
    Re-uses the same connection within a thread to avoid excessive opens.
    """
    attr = f"conn_{db_path}"
    conn = getattr(_local, attr, None)
    if conn is None:
        conn = sqlite3.connect(db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row  # dict-like access
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        setattr(_local, attr, conn)
    return conn


def close_connection(db_path: str = DEFAULT_DB_PATH) -> None:
    """Explicitly close the thread-local connection (e.g. at shutdown)."""
    attr = f"conn_{db_path}"
    conn = getattr(_local, attr, None)
    if conn is not None:
        conn.close()
        setattr(_local, attr, None)


@contextmanager
def transactional(db_path: str = DEFAULT_DB_PATH):
    """
    Context manager that yields a connection and commits on success
    or rolls back on exception.
    """
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


# ---------------------------------------------------------------------------
# Generic query helpers
# ---------------------------------------------------------------------------

def execute_query(sql: str, params: tuple = (), *, db_path: str = DEFAULT_DB_PATH) -> sqlite3.Cursor:
    """Execute a write query (INSERT/UPDATE/DELETE) and commit."""
    conn = get_connection(db_path)
    cur = conn.execute(sql, params)
    conn.commit()
    return cur


def fetch_all(sql: str, params: tuple = (), *, db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Run a SELECT and return all rows as a list of dicts."""
    conn = get_connection(db_path)
    rows = conn.execute(sql, params).fetchall()
    return [dict(row) for row in rows]


def fetch_one(sql: str, params: tuple = (), *, db_path: str = DEFAULT_DB_PATH) -> Optional[Dict[str, Any]]:
    """Run a SELECT and return first row as dict, or None."""
    conn = get_connection(db_path)
    row = conn.execute(sql, params).fetchone()
    return dict(row) if row else None


# ---------------------------------------------------------------------------
# Domain-specific helpers
# ---------------------------------------------------------------------------

# ── Official Content ──────────────────────────────────────────────────────

def insert_video(title: str, total_frames: int, file_path: str, *, db_path: str = DEFAULT_DB_PATH) -> int:
    """Insert an official video and return its id."""
    cur = execute_query(
        "INSERT INTO official_content (title, total_frames, file_path) VALUES (?, ?, ?);",
        (title, total_frames, file_path),
        db_path=db_path,
    )
    return cur.lastrowid


def get_video(video_id: int, *, db_path: str = DEFAULT_DB_PATH) -> Optional[Dict[str, Any]]:
    """Fetch a single video by id."""
    return fetch_one("SELECT * FROM official_content WHERE id = ?;", (video_id,), db_path=db_path)


def get_all_videos(*, db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Return every registered video."""
    return fetch_all("SELECT * FROM official_content ORDER BY uploaded_at DESC;", db_path=db_path)


# ── Fingerprints ──────────────────────────────────────────────────────────

def insert_fingerprints_batch(
    video_id: int,
    fingerprints: List[Tuple[int, str]],
    *,
    db_path: str = DEFAULT_DB_PATH,
) -> int:
    """
    Batch-insert fingerprints for a video.

    Parameters
    ----------
    video_id : int
    fingerprints : list of (frame_index, phash_hex)

    Returns
    -------
    int — number of rows inserted
    """
    conn = get_connection(db_path)
    data = [(video_id, fi, ph) for fi, ph in fingerprints]
    conn.executemany(
        "INSERT OR IGNORE INTO fingerprints (video_id, frame_index, phash) VALUES (?, ?, ?);",
        data,
    )
    conn.commit()
    return len(data)


def get_all_fingerprints(*, db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Return all fingerprints (used by the matching engine to build the search set)."""
    return fetch_all("SELECT video_id, phash FROM fingerprints;", db_path=db_path)


def get_fingerprints_for_video(video_id: int, *, db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Return fingerprints for a specific video, ordered by frame index."""
    return fetch_all(
        "SELECT * FROM fingerprints WHERE video_id = ? ORDER BY frame_index;",
        (video_id,),
        db_path=db_path,
    )


# ── Detections ────────────────────────────────────────────────────────────

def insert_detection(
    video_id: int,
    source_url: str,
    platform: str,
    confidence: float,
    classification: Optional[str] = None,
    risk_score: Optional[int] = None,
    reasoning: Optional[str] = None,
    *,
    db_path: str = DEFAULT_DB_PATH,
) -> int:
    """Record a new detection event and return its id."""
    cur = execute_query(
        """INSERT INTO detections
               (video_id, source_url, platform, c_plus_plus_confidence,
                gemini_classification, gemini_risk_score, gemini_reasoning)
           VALUES (?, ?, ?, ?, ?, ?, ?);""",
        (video_id, source_url, platform, confidence, classification, risk_score, reasoning),
        db_path=db_path,
    )
    return cur.lastrowid


def get_all_detections(
    *,
    limit: int = 50,
    offset: int = 0,
    db_path: str = DEFAULT_DB_PATH,
) -> List[Dict[str, Any]]:
    """Paginated list of detections, newest first."""
    return fetch_all(
        "SELECT * FROM detections ORDER BY detected_at DESC LIMIT ? OFFSET ?;",
        (limit, offset),
        db_path=db_path,
    )


def get_dashboard_stats(*, db_path: str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    """Aggregate statistics for the dashboard endpoint."""
    conn = get_connection(db_path)

    total_videos = conn.execute("SELECT COUNT(*) FROM official_content;").fetchone()[0]
    total_detections = conn.execute("SELECT COUNT(*) FROM detections;").fetchone()[0]

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    detections_today = conn.execute(
        "SELECT COUNT(*) FROM detections WHERE DATE(detected_at) = ?;", (today,)
    ).fetchone()[0]

    high_risk = conn.execute(
        "SELECT COUNT(*) FROM detections WHERE gemini_risk_score >= 75;"
    ).fetchone()[0]

    avg_confidence = conn.execute(
        "SELECT AVG(c_plus_plus_confidence) FROM detections;"
    ).fetchone()[0]

    return {
        "total_videos_protected": total_videos,
        "total_detections": total_detections,
        "detections_today": detections_today,
        "high_risk_count": high_risk,
        "avg_detection_time": round(avg_confidence or 0, 2),
    }


# ---------------------------------------------------------------------------
# Example queries (for documentation / quick reference)
# ---------------------------------------------------------------------------
EXAMPLE_QUERIES = {
    "all_piracy_detections": (
        "SELECT d.*, oc.title "
        "FROM detections d "
        "JOIN official_content oc ON d.video_id = oc.id "
        "WHERE d.gemini_classification = 'Piracy' "
        "ORDER BY d.detected_at DESC;"
    ),
    "top_pirated_videos": (
        "SELECT oc.title, COUNT(d.id) AS detection_count "
        "FROM detections d "
        "JOIN official_content oc ON d.video_id = oc.id "
        "GROUP BY d.video_id "
        "ORDER BY detection_count DESC "
        "LIMIT 10;"
    ),
    "recent_high_risk": (
        "SELECT * FROM detections "
        "WHERE gemini_risk_score >= 80 "
        "ORDER BY detected_at DESC "
        "LIMIT 20;"
    ),
    "fingerprint_count_per_video": (
        "SELECT oc.title, COUNT(f.id) AS fp_count "
        "FROM official_content oc "
        "LEFT JOIN fingerprints f ON oc.id = f.video_id "
        "GROUP BY oc.id;"
    ),
}
