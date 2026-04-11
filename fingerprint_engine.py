#!/usr/bin/env python3
"""
SportsGuard AI — Fingerprint Engine (Module A)
Extracts perceptual hashes from video frames and stores them in SQLite.

Usage (CLI):
    python fingerprint_engine.py path/to/video.mp4 "Match Title"

Usage (library):
    from fingerprint_engine import fingerprint_video
    vid_id = fingerprint_video("clip.mp4", "IPL Highlights")
"""

import logging
import os
import sqlite3
import sys
import time
from pathlib import Path
from typing import List, Tuple

import cv2
import imagehash
from PIL import Image

from setup_database import init_database

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s — %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("fingerprint_engine")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
FRAMES_PER_SECOND = 1          # Extract 1 frame per second of video
HASH_SIZE = 8                  # 8×8 → 64-bit perceptual hash
BATCH_SIZE = 100               # Commit fingerprints every N frames


# ---------------------------------------------------------------------------
# Frame extraction
# ---------------------------------------------------------------------------

def _extract_frames_generator(video_path: str, fps: int = FRAMES_PER_SECOND):
    """
    Generator that yields (frame_index, grayscale_pil_image) tuples at
    the requested *fps* rate from the video at *video_path*.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video file: {video_path}")

    video_fps = cap.get(cv2.CAP_PROP_FPS)
    if video_fps <= 0:
        cap.release()
        raise ValueError(f"Invalid FPS ({video_fps}) — file may be corrupted: {video_path}")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration_sec = total_frames / video_fps
    frame_interval = int(round(video_fps / fps))   # grab every Nth frame
    if frame_interval < 1:
        frame_interval = 1

    expected_output = int(duration_sec * fps)
    log.info(
        "Video opened — %.1f s, %d native frames, extracting ~%d frames at %d FPS",
        duration_sec, total_frames, expected_output, fps,
    )

    frame_idx = 0   # output frame counter
    native_idx = 0   # native frame counter

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if native_idx % frame_interval == 0:
            # Convert BGR → Grayscale → PIL
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            pil_img = Image.fromarray(gray)
            yield frame_idx, pil_img
            frame_idx += 1

        native_idx += 1

    cap.release()
    log.info("Extraction complete — %d frames produced.", frame_idx)


# ---------------------------------------------------------------------------
# Hashing
# ---------------------------------------------------------------------------

def _compute_phash(image: Image.Image) -> str:
    """Return the hex representation of a perceptual hash."""
    h = imagehash.phash(image, hash_size=HASH_SIZE)
    return str(h)


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def fingerprint_video(
    video_path: str,
    title: str,
    db_path: str = "sportsguard.db",
) -> int:
    """
    End-to-end fingerprinting pipeline.

    1. Extract frames at 1 FPS
    2. Compute pHash for each grayscale frame
    3. Store video + fingerprints in SQLite

    Returns
    -------
    int — the ``video_id`` of the newly fingerprinted video.

    Raises
    ------
    ValueError  — if the video cannot be opened or is corrupted.
    FileNotFoundError — if *video_path* does not exist.
    """
    video_path = str(Path(video_path).resolve())
    if not os.path.isfile(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    # Ensure database tables exist
    init_database(db_path)

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")

    try:
        # ── Compute fingerprints ──────────────────────────────────────
        fingerprints: List[Tuple[int, str]] = []
        t0 = time.perf_counter()

        for frame_idx, image in _extract_frames_generator(video_path):
            phash_hex = _compute_phash(image)
            fingerprints.append((frame_idx, phash_hex))

            if (frame_idx + 1) % 10 == 0 or frame_idx == 0:
                log.info("Processing frame %d ...", frame_idx + 1)

        total_frames = len(fingerprints)
        if total_frames == 0:
            raise ValueError("No frames could be extracted — video may be corrupted.")

        elapsed = time.perf_counter() - t0
        log.info("Hashed %d frames in %.2f s (%.1f frames/s)", total_frames, elapsed, total_frames / elapsed)

        # ── Insert video record ───────────────────────────────────────
        cur = conn.execute(
            "INSERT INTO official_content (title, total_frames, file_path) VALUES (?, ?, ?);",
            (title, total_frames, video_path),
        )
        video_id = cur.lastrowid

        # ── Batch insert fingerprints ─────────────────────────────────
        batch: List[Tuple[int, int, str]] = []
        for frame_idx, phash_hex in fingerprints:
            batch.append((video_id, frame_idx, phash_hex))

            if len(batch) >= BATCH_SIZE:
                conn.executemany(
                    "INSERT INTO fingerprints (video_id, frame_index, phash) VALUES (?, ?, ?);",
                    batch,
                )
                conn.commit()
                log.info("Committed batch of %d fingerprints.", len(batch))
                batch.clear()

        # Flush remaining
        if batch:
            conn.executemany(
                "INSERT INTO fingerprints (video_id, frame_index, phash) VALUES (?, ?, ?);",
                batch,
            )
            conn.commit()
            log.info("Committed final batch of %d fingerprints.", len(batch))

        log.info("✓ Video '%s' fingerprinted → video_id=%d, frames=%d", title, video_id, total_frames)
        return video_id

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: python fingerprint_engine.py <video_path> <title> [db_path]")
        sys.exit(1)

    video_path = sys.argv[1]
    title = sys.argv[2]
    db_path = sys.argv[3] if len(sys.argv) > 3 else "sportsguard.db"

    vid_id = fingerprint_video(video_path, title, db_path)
    print(f"Done — video_id = {vid_id}")


if __name__ == "__main__":
    main()
