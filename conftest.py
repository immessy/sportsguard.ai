"""
SportsGuard AI — Pytest Fixtures (conftest.py)
Shared fixtures for all test modules.
"""

import os
import sys
import tempfile
from pathlib import Path

import cv2
import numpy as np
import pytest

# Ensure project root is on sys.path
PROJECT_ROOT = str(Path(__file__).resolve().parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


# ── Test database ─────────────────────────────────────────────────────────

@pytest.fixture
def test_db(tmp_path):
    """
    Create a throwaway SQLite database for each test.
    Automatically cleaned up by pytest's tmp_path machinery.
    """
    from setup_database import init_database

    db_path = str(tmp_path / "test_sportsguard.db")
    init_database(db_path, reset=True)
    yield db_path


# ── Synthetic test video ─────────────────────────────────────────────────

@pytest.fixture
def test_video(tmp_path):
    """
    Generate a small 3-second synthetic MP4 (30 FPS, 320×240)
    with randomly coloured frames so pHash produces varied hashes.
    Returns the path to the temp file.
    """
    video_path = str(tmp_path / "test_clip.mp4")
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(video_path, fourcc, 30.0, (320, 240))

    rng = np.random.RandomState(42)
    for _ in range(90):  # 3 seconds × 30 FPS
        frame = rng.randint(0, 256, (240, 320, 3), dtype=np.uint8)
        writer.write(frame)

    writer.release()
    return video_path
