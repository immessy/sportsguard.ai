"""
fingerprint_engine.py
=====================
SportsGuard AI - Module A: Video Fingerprinting
Member 2 (AI & Data Specialist)

Extracts perceptual hash fingerprints from video files at 1 FPS.
Fingerprints are stored in SQLite for fast similarity lookups.

Usage:
    python fingerprint_engine.py path/to/video.mp4   # CLI mode
    from fingerprint_engine import extract_fingerprints  # import mode
"""

import os
import sys
import sqlite3
import logging
from pathlib import Path
from typing import Optional

import cv2
import imagehash
from PIL import Image

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("fingerprint_engine")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DEFAULT_HASH_SIZE = 8          # phash grid size (8×8 = 64-bit hash)
DEFAULT_FPS_TARGET = 1         # extract 1 frame per second of video
SUPPORTED_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
DEFAULT_DB_PATH = "sportsguard.db"


# ---------------------------------------------------------------------------
# Core extraction
# ---------------------------------------------------------------------------

def extract_frames(
    video_path: str,
    fps_target: int = DEFAULT_FPS_TARGET,
) -> list[tuple[int, Image.Image]]:
    """Extract frames from a video file at the specified FPS rate.

    Args:
        video_path: Absolute or relative path to the video file (MP4/MOV/etc.).
        fps_target: Number of frames to extract per second of video.
                    Defaults to 1 (one frame per second) to avoid bloat.

    Returns:
        List of ``(frame_index, PIL_Image)`` tuples where ``frame_index`` is the
        original frame number in the video (0-based).

    Raises:
        FileNotFoundError: If the video file does not exist.
        ValueError: If the video cannot be opened by OpenCV.

    Example:
        >>> frames = extract_frames("match.mp4", fps_target=1)
        >>> print(f"Extracted {len(frames)} frames")
    """
    path = Path(video_path)
    if not path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        logger.warning(
            "Unsupported extension '%s'. Attempting anyway...", path.suffix
        )

    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise ValueError(f"OpenCV could not open video: {video_path}")

    native_fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration_s = total_frames / native_fps if native_fps > 0 else 0

    logger.info(
        "Opened '%s': %.1f FPS, %d frames, %.1fs duration",
        path.name, native_fps, total_frames, duration_s,
    )

    # Calculate frame step: how many native frames to skip between extractions
    frame_step = max(1, int(native_fps / fps_target)) if native_fps > 0 else 1

    extracted: list[tuple[int, Image.Image]] = []
    frame_idx = 0

    while True:
        ret, bgr_frame = cap.read()
        if not ret:
            break

        if frame_idx % frame_step == 0:
            # Convert BGR (OpenCV default) → RGB for PIL
            rgb_frame = cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(rgb_frame)
            extracted.append((frame_idx, pil_image))

        frame_idx += 1

    cap.release()
    logger.info("Extracted %d frames from '%s'.", len(extracted), path.name)
    return extracted


def compute_phash(
    image: Image.Image,
    hash_size: int = DEFAULT_HASH_SIZE,
) -> str:
    """Compute a perceptual hash (pHash) for a PIL Image.

    The image is first converted to grayscale before hashing, which makes the
    hash robust to color changes while remaining sensitive to structural content.

    Args:
        image: PIL Image (any mode; will be converted to grayscale internally).
        hash_size: Size of the DCT hash grid. Larger = more precision but
                   slower comparison. Default is 8 (64-bit hash).

    Returns:
        Hex string representation of the perceptual hash (e.g. ``"f8e4b2a1...``).

    Example:
        >>> img = Image.open("frame.jpg")
        >>> h = compute_phash(img)
        >>> print(h)  # e.g. "f8e4b2a107c39d1e"
    """
    grayscale = image.convert("L")
    phash = imagehash.phash(grayscale, hash_size=hash_size)
    return str(phash)


def extract_fingerprints(
    video_path: str,
    fps_target: int = DEFAULT_FPS_TARGET,
    hash_size: int = DEFAULT_HASH_SIZE,
) -> list[tuple[int, str]]:
    """Extract perceptual hash fingerprints from a video file.

    Combines ``extract_frames()`` and ``compute_phash()`` into a single
    convenience function. This is the primary entry point for Module A.

    Args:
        video_path: Path to the MP4/MOV video file.
        fps_target: Frames per second to sample (default = 1).
        hash_size: pHash grid size (default = 8).

    Returns:
        List of ``(frame_index, phash_hex_string)`` tuples.

    Raises:
        FileNotFoundError: If the video file does not exist.
        ValueError: If the video cannot be opened.

    Example:
        >>> fingerprints = extract_fingerprints("match.mp4")
        >>> for idx, h in fingerprints[:3]:
        ...     print(f"Frame {idx}: {h}")
    """
    logger.info("Starting fingerprint extraction for: %s", video_path)
    frames = extract_frames(video_path, fps_target=fps_target)

    fingerprints: list[tuple[int, str]] = []
    for frame_idx, pil_image in frames:
        phash_hex = compute_phash(pil_image, hash_size=hash_size)
        fingerprints.append((frame_idx, phash_hex))

    logger.info("Generated %d fingerprints.", len(fingerprints))
    return fingerprints


# ---------------------------------------------------------------------------
# Similarity comparison
# ---------------------------------------------------------------------------

def hamming_distance(hash1: str, hash2: str) -> int:
    """Compute Hamming distance between two pHash hex strings.

    Args:
        hash1: First pHash hex string.
        hash2: Second pHash hex string.

    Returns:
        Integer Hamming distance (0 = identical, higher = more different).
        Returns -1 if hashes have different lengths (incompatible sizes).
    """
    if len(hash1) != len(hash2):
        logger.warning("Hash length mismatch: %d vs %d", len(hash1), len(hash2))
        return -1
    h1 = imagehash.hex_to_hash(hash1)
    h2 = imagehash.hex_to_hash(hash2)
    return h1 - h2  # imagehash overloads __sub__ as Hamming distance


def find_matching_frames(
    query_fingerprints: list[tuple[int, str]],
    db_fingerprints: list[tuple[int, str]],
    threshold: int = 10,
) -> list[dict]:
    """Find frames in the database that match query fingerprints.

    Args:
        query_fingerprints: Fingerprints from the video being checked.
        db_fingerprints: Reference fingerprints from the protected video.
        threshold: Maximum Hamming distance to consider a match (default = 10).
                   Lower = stricter matching.

    Returns:
        List of match dicts: ``{"query_frame": int, "db_frame": int, "distance": int}``.
    """
    matches = []
    for q_idx, q_hash in query_fingerprints:
        for db_idx, db_hash in db_fingerprints:
            dist = hamming_distance(q_hash, db_hash)
            if 0 <= dist <= threshold:
                matches.append({
                    "query_frame": q_idx,
                    "db_frame": db_idx,
                    "distance": dist,
                })
    return matches


# ---------------------------------------------------------------------------
# SQLite persistence
# ---------------------------------------------------------------------------

def init_db(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Initialize the SQLite database and create the fingerprints table if needed.

    Schema:
        fingerprints(id, video_id, frame_index, phash, created_at)

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        Open ``sqlite3.Connection`` object (caller is responsible for closing).
    """
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS fingerprints (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id   TEXT    NOT NULL,
            frame_index INTEGER NOT NULL,
            phash      TEXT    NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_phash ON fingerprints (phash)"
    )
    conn.commit()
    logger.info("Database ready at: %s", db_path)
    return conn


def save_fingerprints(
    video_id: str,
    fingerprints: list[tuple[int, str]],
    db_path: str = DEFAULT_DB_PATH,
) -> int:
    """Save video fingerprints to the SQLite database.

    Inserts all (frame_index, phash) pairs under the given ``video_id``.
    Existing records for this ``video_id`` are replaced.

    Args:
        video_id: Unique identifier for the video (e.g. filename or UUID).
        fingerprints: List of ``(frame_index, phash_hex_string)`` tuples.
        db_path: Path to the SQLite database file.

    Returns:
        Number of rows inserted.

    Example:
        >>> fps = extract_fingerprints("match.mp4")
        >>> count = save_fingerprints("match_video_001", fps)
        >>> print(f"Saved {count} fingerprints")
    """
    conn = init_db(db_path)
    try:
        # Remove old records for this video_id to allow re-indexing
        conn.execute("DELETE FROM fingerprints WHERE video_id = ?", (video_id,))
        rows = [(video_id, idx, phash) for idx, phash in fingerprints]
        conn.executemany(
            "INSERT INTO fingerprints (video_id, frame_index, phash) VALUES (?, ?, ?)",
            rows,
        )
        conn.commit()
        logger.info("Saved %d fingerprints for video_id='%s'.", len(rows), video_id)
        return len(rows)
    finally:
        conn.close()


def load_fingerprints(
    video_id: str,
    db_path: str = DEFAULT_DB_PATH,
) -> list[tuple[int, str]]:
    """Load fingerprints for a specific video from the database.

    Args:
        video_id: Identifier of the video to retrieve.
        db_path: Path to the SQLite database file.

    Returns:
        List of ``(frame_index, phash_hex_string)`` tuples.
    """
    conn = init_db(db_path)
    try:
        cursor = conn.execute(
            "SELECT frame_index, phash FROM fingerprints WHERE video_id = ? ORDER BY frame_index",
            (video_id,),
        )
        return [(row[0], row[1]) for row in cursor.fetchall()]
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json

    if len(sys.argv) < 2:
        # --- Demo with synthetic video using OpenCV ---
        print("=" * 60)
        print("SportsGuard AI — Module A: Fingerprint Engine Demo")
        print("=" * 60)
        print("\nUsage: python fingerprint_engine.py <video_path>")
        print("\nNo video provided — generating a synthetic test video...\n")

        # Create a small in-memory test video (10 frames, 640×360)
        test_video_path = "test_data/synthetic_test.mp4"
        os.makedirs("test_data", exist_ok=True)

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(test_video_path, fourcc, 10.0, (640, 360))

        import numpy as np
        for i in range(30):  # 30 frames at 10 FPS = 3 seconds
            frame = np.zeros((360, 640, 3), dtype=np.uint8)
            frame[:, :] = [34, max(0, 139 - i * 3), 34]  # slight color variation
            cv2.putText(
                frame, f"SportsGuard Frame {i}",
                (50, 180), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3,
            )
            writer.write(frame)
        writer.release()
        print(f"Synthetic video saved to: {test_video_path}")

        video_path = test_video_path
    else:
        video_path = sys.argv[1]

    print(f"\nProcessing: {video_path}")
    try:
        fingerprints = extract_fingerprints(video_path, fps_target=1)

        print(f"\n[OK] Extracted {len(fingerprints)} fingerprints:")
        for idx, h in fingerprints[:5]:
            print(f"  Frame {idx:5d}: {h}")
        if len(fingerprints) > 5:
            print(f"  ... ({len(fingerprints) - 5} more)")

        # Save to SQLite
        video_name = Path(video_path).stem
        saved = save_fingerprints(video_name, fingerprints)
        print(f"\n[OK] Saved {saved} fingerprints to '{DEFAULT_DB_PATH}'")

        # Reload and verify
        loaded = load_fingerprints(video_name)
        print(f"[OK] Reloaded {len(loaded)} fingerprints from DB" if loaded else "[WARN] Reload returned empty!")

    except FileNotFoundError as e:
        print(f"\n[ERROR] {e}")
    except Exception as e:
        print(f"\n[ERROR] {e}")
        raise

    print("\n" + "=" * 60)
    print("Done.")
    print("=" * 60)
