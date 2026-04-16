#!/usr/bin/env python3
"""
SportsGuard AI — Real Data Setup Script
========================================
One-stop script to prepare realistic demo data for the
Google Solution Challenge 2026 presentation.

Usage:
    python get_real_data.py                   # full setup (prompts for YouTube URL)
    python get_real_data.py --skip-download   # skip YouTube download, use existing videos

Steps:
    1. Check dependencies (yt-dlp, ffmpeg, project packages)
    2. Download a real IPL clip from YouTube
    3. Create piracy-simulated version
    4. Create transformative (analysis) version
    5. Create meme version
    6. Update mock_tweets.json with 10 realistic entries
    7. Update metadata JSON files
    8. Seed database with 12 videos and 50 detections
    9. Verify everything
   10. Print demo instructions
"""

import argparse
import io
import json
import os
import random
import shutil
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# Force UTF-8 output on Windows to avoid cp1252 encoding errors
# ---------------------------------------------------------------------------
if sys.platform == "win32":
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
    except Exception:
        pass  # fallback: emoji will be stripped below

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent
TEST_DATA    = PROJECT_ROOT / "test_data"
VIDEOS_DIR   = TEST_DATA / "videos"
META_DIR     = TEST_DATA / "metadata"
DB_PATH      = PROJECT_ROOT / "sportsguard.db"

RAW_DOWNLOAD       = VIDEOS_DIR / "raw_download.mp4"
OFFICIAL_CLIP      = VIDEOS_DIR / "official_clip.mp4"
PIRACY_CLIP        = VIDEOS_DIR / "piracy_clip.mp4"
TRANSFORMATIVE_CLIP = VIDEOS_DIR / "transformative_clip.mp4"
MEME_CLIP          = VIDEOS_DIR / "meme_clip.mp4"

# Ensure directories exist
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
META_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def banner(text: str) -> None:
    """Print a prominent step banner."""
    width = 60
    print()
    print("=" * width)
    print(f"  {text}")
    print("=" * width)


def info(msg: str) -> None:
    print(f"  [i] {msg}")


def success(msg: str) -> None:
    print(f"  [OK] {msg}")


def warn(msg: str) -> None:
    print(f"  [!] {msg}")


def fail(msg: str) -> None:
    print(f"  [X] {msg}")


def run_cmd(cmd: list, description: str, *, check: bool = True, capture: bool = False, **kwargs):
    """Run a subprocess command with nice logging."""
    info(f"Running: {' '.join(str(c) for c in cmd)}")
    try:
        result = subprocess.run(
            cmd,
            check=check,
            capture_output=capture,
            text=True,
            cwd=str(PROJECT_ROOT),
            **kwargs,
        )
        if check:
            success(description)
        return result
    except subprocess.CalledProcessError as e:
        fail(f"{description} — exit code {e.returncode}")
        if capture and e.stderr:
            print(f"      STDERR: {e.stderr[:500]}")
        raise
    except FileNotFoundError:
        fail(f"{description} — command not found")
        raise


# ═══════════════════════════════════════════════════════════════════════════
#  STEP 1 — CHECK DEPENDENCIES
# ═══════════════════════════════════════════════════════════════════════════

def step_1_check_deps() -> bool:
    banner("STEP 1 / 10 — CHECK DEPENDENCIES")
    all_ok = True

    # -- yt-dlp --
    info("Checking yt-dlp …")
    try:
        subprocess.run(["yt-dlp", "--version"], capture_output=True, check=True, text=True)
        success("yt-dlp is installed")
    except (subprocess.CalledProcessError, FileNotFoundError):
        warn("yt-dlp not found — installing now …")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "yt-dlp"], check=True)
            success("yt-dlp installed successfully")
        except Exception as e:
            fail(f"Could not install yt-dlp: {e}")
            all_ok = False

    # -- ffmpeg --
    info("Checking ffmpeg …")
    try:
        result = subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True, text=True)
        version_line = result.stdout.split("\n")[0]
        success(f"ffmpeg found — {version_line[:60]}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        fail("ffmpeg is NOT installed!")
        print()
        print("  +-----------------------------------------------------+")
        print("  |          HOW TO INSTALL FFMPEG ON WINDOWS            |")
        print("  +-----------------------------------------------------+")
        print("  |  Option 1 (winget -- recommended):                   |")
        print("  |    winget install Gyan.FFmpeg                        |")
        print("  |                                                      |")
        print("  |  Option 2 (choco):                                   |")
        print("  |    choco install ffmpeg                               |")
        print("  |                                                      |")
        print("  |  Option 3 (manual):                                  |")
        print("  |    1. Download from https://ffmpeg.org/download.html |")
        print("  |    2. Extract to C:\\ffmpeg                           |")
        print("  |    3. Add C:\\ffmpeg\\bin to your system PATH          |")
        print("  |    4. Restart your terminal                          |")
        print("  +-----------------------------------------------------+")
        print()
        all_ok = False

    # -- project deps --
    info("Checking project dependencies ...")
    missing = []
    for pkg in ["flask", "flask_cors", "cv2", "PIL", "imagehash", "numpy"]:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    if missing:
        warn(f"Missing project packages: {', '.join(missing)}")
        info("Attempting: pip install -r requirements.txt ...")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", str(PROJECT_ROOT / "requirements.txt")],
                check=True,
            )
            success("Project dependencies installed")
        except Exception as e:
            fail(f"Could not install dependencies: {e}")
            all_ok = False
    else:
        success("All project dependencies present")

    return all_ok


# ═══════════════════════════════════════════════════════════════════════════
#  STEP 2 — DOWNLOAD REAL IPL VIDEO
# ═══════════════════════════════════════════════════════════════════════════

def step_2_download(skip: bool = False) -> bool:
    banner("STEP 2 / 10 — DOWNLOAD REAL IPL VIDEO")

    if skip and OFFICIAL_CLIP.exists():
        info(f"--skip-download flag set and {OFFICIAL_CLIP.name} already exists")
        success("Skipping download step")
        return True

    if skip and not OFFICIAL_CLIP.exists():
        warn("--skip-download set but official_clip.mp4 does not exist.")
        warn("A synthetic test clip will be generated instead.")
        return _generate_synthetic_clip()

    print()
    print("  Paste a YouTube URL of an IPL highlights video.")
    print("  (Use an official broadcaster clip, e.g. IPL official channel)")
    print()
    url = input("  YouTube URL > ").strip()

    if not url:
        warn("No URL provided — generating synthetic test clip instead.")
        return _generate_synthetic_clip()

    # Download with yt-dlp
    try:
        info("Downloading video (this may take a minute) …")
        run_cmd(
            [
                "yt-dlp",
                "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4",
                "--merge-output-format", "mp4",
                "-o", str(RAW_DOWNLOAD),
                "--no-playlist",
                url,
            ],
            "Video downloaded",
        )
    except Exception:
        warn("yt-dlp download failed — generating synthetic test clip.")
        return _generate_synthetic_clip()

    if not RAW_DOWNLOAD.exists():
        fail("Download file not found after yt-dlp completed")
        return _generate_synthetic_clip()

    # Trim to 30 seconds
    info("Trimming to 30 seconds …")
    try:
        run_cmd(
            [
                "ffmpeg", "-y",
                "-i", str(RAW_DOWNLOAD),
                "-t", "30",
                "-c:v", "libx264", "-preset", "fast",
                "-c:a", "aac",
                str(OFFICIAL_CLIP),
            ],
            "Trimmed to 30s → official_clip.mp4",
        )
    except Exception:
        fail("ffmpeg trim failed")
        return False

    success(f"official_clip.mp4 ready ({OFFICIAL_CLIP.stat().st_size / 1024 / 1024:.1f} MB)")
    return True


def _generate_synthetic_clip() -> bool:
    """Generate a synthetic test clip using ffmpeg testsrc when no real video is available."""
    info("Generating 30s synthetic sports-style test clip via ffmpeg ...")
    try:
        run_cmd(
            [
                "ffmpeg", "-y",
                "-f", "lavfi",
                "-i", "testsrc=duration=30:size=1280x720:rate=30",
                "-f", "lavfi",
                "-i", "sine=frequency=440:duration=30",
                "-c:v", "libx264", "-preset", "fast", "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                str(OFFICIAL_CLIP),
            ],
            "Synthetic official_clip.mp4 created",
        )
        return True
    except Exception:
        fail("Could not generate synthetic clip — ffmpeg may be missing")
        return False


# ═══════════════════════════════════════════════════════════════════════════
#  STEP 3 — CREATE PIRACY VERSION
# ═══════════════════════════════════════════════════════════════════════════

def step_3_piracy() -> bool:
    banner("STEP 3 / 10 — CREATE PIRACY VERSION")

    if not OFFICIAL_CLIP.exists():
        fail("official_clip.mp4 not found — cannot create piracy version")
        return False

    info("Applying piracy simulation filters ...")
    info("  - Crop 5% from edges")
    info("  - Add re-encoding noise")
    info("  - Reduce quality (CRF 28)")
    info("  - Add watermark text 't.me/ipl_free_stream'")

    # Build the complex filter:
    #   1. crop 5% from each edge
    #   2. add slight noise via hue shift / unsharp
    #   3. drawtext for watermark
    vf = (
        "crop=iw*0.9:ih*0.9:iw*0.05:ih*0.05,"
        "noise=c0s=12:c0f=t+u,"
        "drawtext=text='t.me/ipl_free_stream'"
        ":fontsize=18:fontcolor=white@0.6"
        ":x=w-tw-10:y=h-th-10"
        ":borderw=1:bordercolor=black@0.4"
    )

    try:
        run_cmd(
            [
                "ffmpeg", "-y",
                "-i", str(OFFICIAL_CLIP),
                "-vf", vf,
                "-c:v", "libx264", "-crf", "28", "-preset", "fast",
                "-c:a", "aac", "-b:a", "96k",
                str(PIRACY_CLIP),
            ],
            "piracy_clip.mp4 created",
        )
        return True
    except Exception as e:
        fail(f"Piracy clip creation failed: {e}")
        return False


# ═══════════════════════════════════════════════════════════════════════════
#  STEP 4 — CREATE TRANSFORMATIVE VERSION
# ═══════════════════════════════════════════════════════════════════════════

def step_4_transformative() -> bool:
    banner("STEP 4 / 10 — CREATE TRANSFORMATIVE VERSION")

    if not OFFICIAL_CLIP.exists():
        fail("official_clip.mp4 not found — cannot create transformative version")
        return False

    info("Applying analysis-style overlays ...")
    info("  - 'TACTICAL ANALYSIS' title at top")
    info("  - Arrow-style drawbox overlay")
    info("  - 'Speed: 142kph' at bottom")
    info("  - Slow motion 0.5x for middle 10s")

    # --- Phase 1: Create the full annotated clip at normal speed ---
    annotated_tmp = VIDEOS_DIR / "_annotated_tmp.mp4"
    vf_annotate = (
        # Semi-transparent header bar
        "drawbox=x=0:y=0:w=iw:h=50:color=black@0.7:t=fill,"
        # TACTICAL ANALYSIS title
        "drawtext=text='TACTICAL ANALYSIS'"
        ":fontsize=28:fontcolor=white"
        ":x=(w-tw)/2:y=10"
        ":borderw=2:bordercolor=black@0.5,"
        # Arrow-style box annotation (mid-screen)
        "drawbox=x=iw/3:y=ih/3:w=iw/3:h=ih/3"
        ":color=red@0.5:t=3,"
        # Speed label at bottom
        "drawbox=x=0:y=ih-45:w=iw:h=45:color=black@0.7:t=fill,"
        "drawtext=text='Speed\\: 142kph'"
        ":fontsize=22:fontcolor=yellow"
        ":x=(w-tw)/2:y=h-35"
        ":borderw=1:bordercolor=black@0.4"
    )

    try:
        run_cmd(
            [
                "ffmpeg", "-y",
                "-i", str(OFFICIAL_CLIP),
                "-vf", vf_annotate,
                "-c:v", "libx264", "-crf", "22", "-preset", "fast",
                "-c:a", "aac",
                str(annotated_tmp),
            ],
            "Annotated base clip created",
        )
    except Exception as e:
        fail(f"Annotation failed: {e}")
        return False

    # --- Phase 2: Split into 3 segments, slow-mo the middle ---
    seg_a = VIDEOS_DIR / "_seg_a.mp4"   # 0-10s  normal
    seg_b = VIDEOS_DIR / "_seg_b.mp4"   # 10-20s slow-mo
    seg_c = VIDEOS_DIR / "_seg_c.mp4"   # 20-30s normal

    try:
        # Segment A (0-10s)
        run_cmd(
            ["ffmpeg", "-y", "-i", str(annotated_tmp),
             "-t", "10", "-c", "copy", str(seg_a)],
            "Segment A (0-10s)",
        )
        # Segment B (10-20s) at 0.5x speed
        run_cmd(
            ["ffmpeg", "-y", "-i", str(annotated_tmp),
             "-ss", "10", "-t", "10",
             "-vf", "setpts=2.0*PTS",
             "-af", "atempo=0.5",
             "-c:v", "libx264", "-crf", "22", "-preset", "fast",
             "-c:a", "aac",
             str(seg_b)],
            "Segment B (10-20s slow-mo)",
        )
        # Segment C (20-30s)
        run_cmd(
            ["ffmpeg", "-y", "-i", str(annotated_tmp),
             "-ss", "20", "-t", "10", "-c", "copy", str(seg_c)],
            "Segment C (20-30s)",
        )

        # Concat
        concat_file = VIDEOS_DIR / "_concat.txt"
        concat_file.write_text(
            f"file '{seg_a.name}'\nfile '{seg_b.name}'\nfile '{seg_c.name}'\n",
            encoding="utf-8",
        )
        run_cmd(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
             "-i", str(concat_file),
             "-c:v", "libx264", "-crf", "22", "-preset", "fast",
             "-c:a", "aac",
             str(TRANSFORMATIVE_CLIP)],
            "transformative_clip.mp4 created",
        )

        # Cleanup temp files
        for f in [annotated_tmp, seg_a, seg_b, seg_c, concat_file]:
            f.unlink(missing_ok=True)

        return True
    except Exception as e:
        fail(f"Transformative clip creation failed: {e}")
        # Cleanup on error
        for f in [annotated_tmp, seg_a, seg_b, seg_c]:
            if f.exists():
                f.unlink(missing_ok=True)
        return False


# ═══════════════════════════════════════════════════════════════════════════
#  STEP 5 — CREATE MEME VERSION
# ═══════════════════════════════════════════════════════════════════════════

def step_5_meme() -> bool:
    banner("STEP 5 / 10 — CREATE MEME VERSION")

    if not OFFICIAL_CLIP.exists():
        fail("official_clip.mp4 not found — cannot create meme version")
        return False

    info("Applying meme-style filters ...")
    info("  - Bold text 'POV: DHONI WALKS IN' at top")
    info("  - Bold text 'CSK FANS RIGHT NOW' at bottom")
    info("  - Saturated colors")
    info("  - Reaction emoji watermark")

    vf = (
        # Boost saturation for meme look
        "eq=saturation=1.6,"
        # Top meme text
        "drawtext=text='POV\\: DHONI WALKS IN'"
        ":fontsize=36:fontcolor=white"
        ":x=(w-tw)/2:y=20"
        ":borderw=3:bordercolor=black,"
        # Bottom meme text
        "drawtext=text='CSK FANS RIGHT NOW'"
        ":fontsize=36:fontcolor=white"
        ":x=(w-tw)/2:y=h-th-20"
        ":borderw=3:bordercolor=black,"
        # Emoji watermark (text fallback since ffmpeg may not render emoji)
        "drawtext=text='XD'"
        ":fontsize=48:fontcolor=yellow@0.7"
        ":x=w-tw-20:y=20"
        ":borderw=2:bordercolor=black@0.5"
    )

    try:
        run_cmd(
            [
                "ffmpeg", "-y",
                "-i", str(OFFICIAL_CLIP),
                "-vf", vf,
                "-c:v", "libx264", "-crf", "23", "-preset", "fast",
                "-c:a", "aac",
                str(MEME_CLIP),
            ],
            "meme_clip.mp4 created",
        )
        return True
    except Exception as e:
        fail(f"Meme clip creation failed: {e}")
        return False


# ═══════════════════════════════════════════════════════════════════════════
#  STEP 6 — UPDATE MOCK TWEETS
# ═══════════════════════════════════════════════════════════════════════════

def step_6_mock_tweets() -> bool:
    banner("STEP 6 / 10 — UPDATE MOCK TWEETS")

    now = datetime.now(timezone.utc)
    base_ts = now.replace(hour=6, minute=0, second=0, microsecond=0)

    tweets = [
        # ── 5 PIRACY ──────────────────────────────────────────────
        {
            "tweet_text": "🔥 FULL IPL 2024 Final watch FREE HD no ads link in bio 🏏💯 #IPL #FreeStream #IPL2024",
            "username": "@full_match_free",
            "timestamp": (base_ts + timedelta(hours=0, minutes=15)).isoformat(),
            "platform": "Twitter",
            "scenario": "piracy",
            "expected_classification": "Piracy",
            "expected_risk_score_min": 80,
        },
        {
            "tweet_text": "Streaming match LIVE 🔴 before it gets taken down DM for link #IPLLive #FreeIPL",
            "username": "@ipl_leaks_2024",
            "timestamp": (base_ts + timedelta(hours=1, minutes=30)).isoformat(),
            "platform": "Twitter",
            "scenario": "piracy",
            "expected_classification": "Piracy",
            "expected_risk_score_min": 85,
        },
        {
            "tweet_text": "Full broadcast raw feed 720p no commentary free download t.me/ipl_free_stream",
            "username": "@sports_pirate_hd",
            "timestamp": (base_ts + timedelta(hours=2, minutes=45)).isoformat(),
            "platform": "Telegram",
            "scenario": "piracy",
            "expected_classification": "Piracy",
            "expected_risk_score_min": 90,
        },
        {
            "tweet_text": "Watch FREE full match replay no subscription needed MI vs CSK 2024 Final HD 1080p",
            "username": "@free_sports_tv",
            "timestamp": (base_ts + timedelta(hours=4, minutes=10)).isoformat(),
            "platform": "Twitter",
            "scenario": "piracy",
            "expected_classification": "Piracy",
            "expected_risk_score_min": 80,
        },
        {
            "tweet_text": "LIVE stream link in bio hurry before takedown #IPL #FreeMatch 🏏 full match no watermark",
            "username": "@stream_sports_24",
            "timestamp": (base_ts + timedelta(hours=5, minutes=20)).isoformat(),
            "platform": "Twitter",
            "scenario": "piracy",
            "expected_classification": "Piracy",
            "expected_risk_score_min": 75,
        },
        # ── 3 TRANSFORMATIVE ──────────────────────────────────────
        {
            "tweet_text": "Bumrah yorker breakdown why this changed the game tactical analysis with slow-mo 📊🏏 #CricketAnalysis",
            "username": "@TacticalBreakdown",
            "timestamp": (base_ts + timedelta(hours=6, minutes=30)).isoformat(),
            "platform": "YouTube",
            "scenario": "transformative",
            "expected_classification": "Transformative",
            "expected_risk_score_max": 45,
        },
        {
            "tweet_text": "Virat cover drive technique breakdown educational #CricketCoaching — notice the footwork at 0:08",
            "username": "@tactical_cricket",
            "timestamp": (base_ts + timedelta(hours=7, minutes=15)).isoformat(),
            "platform": "YouTube",
            "scenario": "transformative",
            "expected_classification": "Transformative",
            "expected_risk_score_max": 40,
        },
        {
            "tweet_text": "Why this over was the turning point slow mo analysis with arrows and annotations #tactics #IPL2024",
            "username": "@coachingnerds",
            "timestamp": (base_ts + timedelta(hours=8, minutes=0)).isoformat(),
            "platform": "Instagram",
            "scenario": "transformative",
            "expected_classification": "Transformative",
            "expected_risk_score_max": 45,
        },
        # ── 2 MEME ────────────────────────────────────────────────
        {
            "tweet_text": "POV Dhoni walks in at 160/5 CSK fans right now 😤🔥 #ThalaForAReason #CSK #CricketMeme",
            "username": "@cricket_memes_daily",
            "timestamp": (base_ts + timedelta(hours=9, minutes=30)).isoformat(),
            "platform": "Instagram",
            "scenario": "meme",
            "expected_classification": "Meme",
            "expected_risk_score_max": 25,
        },
        {
            "tweet_text": "When the umpire says out but it was clearly in 😂 #CricketMemes #DRS #IPLFunny",
            "username": "@memequeen_sports",
            "timestamp": (base_ts + timedelta(hours=10, minutes=45)).isoformat(),
            "platform": "Twitter",
            "scenario": "meme",
            "expected_classification": "Meme",
            "expected_risk_score_max": 25,
        },
    ]

    tweets_path = TEST_DATA / "mock_tweets.json"
    try:
        tweets_path.write_text(json.dumps(tweets, indent=2, ensure_ascii=False), encoding="utf-8")
        success(f"mock_tweets.json updated — {len(tweets)} entries")
        return True
    except Exception as e:
        fail(f"Failed to write mock_tweets.json: {e}")
        return False


# ═══════════════════════════════════════════════════════════════════════════
#  STEP 7 — UPDATE METADATA JSON FILES
# ═══════════════════════════════════════════════════════════════════════════

def step_7_metadata() -> bool:
    banner("STEP 7 / 10 — UPDATE METADATA JSON FILES")
    ok = True

    # Scenario 01 — Piracy
    s01 = {
        "post_id": "tg_piracy_90001",
        "platform": "Telegram",
        "user": "@ipl_free_stream",
        "text": "🔥 FULL IPL 2024 Final MI vs CSK — FREE HD stream no ads! Join channel for more matches",
        "source_url": "https://t.me/ipl_free_stream/4821",
        "timestamp": datetime.now(timezone.utc).replace(hour=14, minute=30).isoformat(),
        "video_file": "piracy_clip.mp4",
        "scenario": "piracy",
        "expected_classification": "Piracy",
        "expected_risk_score_min": 80,
    }
    try:
        (META_DIR / "scenario_01_piracy.json").write_text(
            json.dumps(s01, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        success("scenario_01_piracy.json updated (Telegram URL, risk ≥ 80)")
    except Exception as e:
        fail(f"scenario_01: {e}")
        ok = False

    # Scenario 02 — Transformative
    s02 = {
        "post_id": "yt_analysis_44502",
        "platform": "YouTube",
        "user": "@TacticalBreakdown",
        "text": "Bumrah's yorker sequence — tactical analysis with slow-mo breakdown and arrow annotations 📊🏏",
        "source_url": "https://youtube.com/watch?v=TacticalIPL2024",
        "timestamp": datetime.now(timezone.utc).replace(hour=16, minute=45).isoformat(),
        "video_file": "transformative_clip.mp4",
        "scenario": "transformative",
        "expected_classification": "Transformative",
        "expected_risk_score_max": 45,
    }
    try:
        (META_DIR / "scenario_02_transformative.json").write_text(
            json.dumps(s02, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        success("scenario_02_transformative.json updated (YouTube URL, risk ≤ 45)")
    except Exception as e:
        fail(f"scenario_02: {e}")
        ok = False

    # Scenario 03 — Meme
    s03 = {
        "post_id": "ig_meme_78003",
        "platform": "Instagram",
        "user": "@cricket_memes_daily",
        "text": "POV: Dhoni walks in at 160/5 😤🔥 CSK fans right now #ThalaForAReason #CricketMeme",
        "source_url": "https://instagram.com/p/CSKmeme78003",
        "timestamp": datetime.now(timezone.utc).replace(hour=19, minute=10).isoformat(),
        "video_file": "meme_clip.mp4",
        "scenario": "meme",
        "expected_classification": "Meme",
        "expected_risk_score_max": 25,
    }
    try:
        (META_DIR / "scenario_03_meme.json").write_text(
            json.dumps(s03, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        success("scenario_03_meme.json updated (Instagram URL, risk ≤ 25)")
    except Exception as e:
        fail(f"scenario_03: {e}")
        ok = False

    return ok


# ═══════════════════════════════════════════════════════════════════════════
#  STEP 8 — SEED DATABASE WITH REALISTIC DATA
# ═══════════════════════════════════════════════════════════════════════════

def step_8_seed_database() -> bool:
    banner("STEP 8 / 10 — SEED DATABASE WITH REALISTIC DATA")

    # Reset database via setup_database
    info("Resetting database …")
    try:
        # Import from project
        sys.path.insert(0, str(PROJECT_ROOT))
        from setup_database import init_database
        from database_helpers import insert_video, insert_detection

        init_database(str(DB_PATH), reset=True)
        success("Database reset and tables recreated")
    except Exception as e:
        fail(f"Database reset failed: {e}")
        return False

    # ── Insert 12 official videos ─────────────────────────────────
    info("Inserting 12 official videos …")
    official_videos = [
        ("IPL 2024 Final - MI vs CSK Highlights",          900, "uploads/ipl_2024_final_mi_csk.mp4"),
        ("IPL 2024 - RCB vs KKR Match 23",                 750, "uploads/ipl_2024_rcb_kkr_m23.mp4"),
        ("Premier League - Arsenal vs Chelsea Highlights",  600, "uploads/pl_arsenal_chelsea.mp4"),
        ("FIFA World Cup 2026 - Quarter Final",             850, "uploads/wc2026_quarterfinal.mp4"),
        ("IPL 2024 - Best Moments Week 3",                  450, "uploads/ipl_2024_week3_best.mp4"),
        ("La Liga - Real Madrid vs Barcelona El Clasico",   720, "uploads/laliga_elclasico.mp4"),
        ("IPL 2024 - SRH vs DC Match 31",                   680, "uploads/ipl_2024_srh_dc_m31.mp4"),
        ("Champions League - Semi Final Highlights",        810, "uploads/ucl_semifinal.mp4"),
        ("IPL 2024 - GT vs LSG Match 12",                   540, "uploads/ipl_2024_gt_lsg_m12.mp4"),
        ("NBA Finals 2024 - Game 7 Highlights",             660, "uploads/nba_finals_g7.mp4"),
        ("IPL 2024 - PBKS vs RR Match 45",                  590, "uploads/ipl_2024_pbks_rr_m45.mp4"),
        ("Wimbledon 2024 - Men's Final Highlights",         480, "uploads/wimbledon_2024_final.mp4"),
    ]

    video_ids = []
    for title, frames, path in official_videos:
        try:
            vid = insert_video(title, frames, path, db_path=str(DB_PATH))
            video_ids.append(vid)
        except Exception as e:
            fail(f"Failed to insert video '{title}': {e}")
            return False

    success(f"Inserted {len(video_ids)} official videos")

    # ── Insert 50 detections ──────────────────────────────────────
    info("Inserting 50 detections across today …")

    now = datetime.now(timezone.utc)
    day_start = now.replace(hour=6, minute=0, second=0, microsecond=0)

    # Helper: spread timestamps from 06:00 to now
    total_minutes = max(1, int((now - day_start).total_seconds() / 60))

    def random_ts():
        offset_min = random.randint(0, total_minutes)
        ts = day_start + timedelta(minutes=offset_min)
        return ts.isoformat()

    # Piracy URLs (25 entries)
    piracy_urls = [
        ("https://twitter.com/free_ipl_hd/status/1001",          "Twitter"),
        ("https://twitter.com/match_leaks/status/1002",           "Twitter"),
        ("https://twitter.com/sport_free_24/status/1003",         "Twitter"),
        ("https://t.me/ipl_free_stream/4821",                     "Telegram"),
        ("https://t.me/sports_piracy_hd/9901",                    "Telegram"),
        ("https://t.me/live_cricket_free/3320",                    "Telegram"),
        ("https://t.me/free_match_replays/1187",                   "Telegram"),
        ("https://streamcloud.io/watch/ipl2024final",              "StreamCloud"),
        ("https://streamcloud.io/live/mi-vs-csk-free",             "StreamCloud"),
        ("https://streamcloud.io/replay/rcb-kkr",                  "StreamCloud"),
        ("https://iptv-portal.net/sports/ipl/live",                "IPTV"),
        ("https://iptv-portal.net/cricket/free-hd",                "IPTV"),
        ("https://p2p-sports.net/torrent/ipl-2024-final",          "P2P"),
        ("https://twitter.com/pirate_sports/status/1014",          "Twitter"),
        ("https://twitter.com/hd_streams_free/status/1015",        "Twitter"),
        ("https://t.me/cricket_free_live/5501",                    "Telegram"),
        ("https://streamcloud.io/watch/pl-arsenal-chelsea",        "StreamCloud"),
        ("https://p2p-sports.net/torrent/pl-highlights",           "P2P"),
        ("https://twitter.com/fullmatch_free/status/1019",         "Twitter"),
        ("https://t.me/ipl_hd_streams/7720",                      "Telegram"),
        ("https://iptv-portal.net/live/worldcup2026",              "IPTV"),
        ("https://streamcloud.io/replay/wc2026-qf",               "StreamCloud"),
        ("https://twitter.com/stream_sports_24/status/1023",       "Twitter"),
        ("https://p2p-sports.net/torrent/nba-finals-2024",         "P2P"),
        ("https://t.me/free_sports_stream/2280",                   "Telegram"),
    ]

    piracy_reasonings = [
        "Raw re-upload of broadcast footage with no commentary or overlays.",
        "Full match stream with original broadcast graphics — direct piracy.",
        "Unmodified official highlights re-uploaded without authorization.",
        "Complete broadcast capture distributed via Telegram channel.",
        "Re-encoded official content at lower quality for mass distribution.",
    ]

    # Transformative URLs (15 entries)
    transformative_urls = [
        ("https://youtube.com/watch?v=tactical_bumrah_01",         "YouTube"),
        ("https://youtube.com/watch?v=virat_technique_02",         "YouTube"),
        ("https://youtube.com/watch?v=ipl_turning_point_03",       "YouTube"),
        ("https://instagram.com/p/cricket_analysis_04",            "Instagram"),
        ("https://youtube.com/watch?v=bowling_breakdown_05",       "YouTube"),
        ("https://youtube.com/watch?v=fielding_analysis_06",       "YouTube"),
        ("https://instagram.com/p/match_review_07",                "Instagram"),
        ("https://youtube.com/watch?v=batting_tech_08",            "YouTube"),
        ("https://youtube.com/watch?v=strategy_review_09",         "YouTube"),
        ("https://instagram.com/p/play_analysis_10",               "Instagram"),
        ("https://youtube.com/watch?v=drs_breakdown_11",           "YouTube"),
        ("https://youtube.com/watch?v=powerplay_tactics_12",       "YouTube"),
        ("https://instagram.com/p/coaching_tips_13",               "Instagram"),
        ("https://youtube.com/watch?v=death_overs_14",             "YouTube"),
        ("https://youtube.com/watch?v=swing_analysis_15",          "YouTube"),
    ]

    transformative_reasonings = [
        "Educational analysis with slow-motion replays and tactical annotations.",
        "Coaching breakdown with arrow overlays and technique commentary.",
        "Statistical analysis with graphics and expert narration overlay.",
    ]

    # Meme URLs (10 entries)
    meme_urls = [
        ("https://twitter.com/cricket_memes/status/2001",          "Twitter"),
        ("https://instagram.com/p/ipl_meme_02",                   "Instagram"),
        ("https://tiktok.com/@sportsmemes/video/3001",             "TikTok"),
        ("https://twitter.com/meme_lord_cricket/status/2004",      "Twitter"),
        ("https://instagram.com/p/csk_meme_05",                   "Instagram"),
        ("https://tiktok.com/@cricketfunny/video/3006",            "TikTok"),
        ("https://twitter.com/ipl_reactions/status/2007",          "Twitter"),
        ("https://instagram.com/p/dhoni_meme_08",                  "Instagram"),
        ("https://tiktok.com/@sportzlol/video/3009",               "TikTok"),
        ("https://twitter.com/cricket_lol/status/2010",            "Twitter"),
    ]

    meme_reasonings = [
        "Meme format with comedic text overlays — clear fair use / parody.",
        "Short clip with reaction text and heavy editing — fan engagement content.",
        "Satirical edit with exaggerated colors and meme captions.",
    ]

    count = 0

    # 25 Piracy detections
    for url, platform in piracy_urls:
        vid = random.choice(video_ids[:5])  # mostly IPL / popular videos
        confidence = round(random.uniform(88.0, 98.0), 2)
        risk = random.randint(75, 95)
        reasoning = random.choice(piracy_reasonings)
        ts = random_ts()

        try:
            conn = sqlite3.connect(str(DB_PATH))
            conn.execute(
                """INSERT INTO detections
                     (video_id, source_url, platform, c_plus_plus_confidence,
                      gemini_classification, gemini_risk_score, gemini_reasoning,
                      status, detected_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);""",
                (vid, url, platform, confidence, "Piracy", risk, reasoning, "classified", ts),
            )
            conn.commit()
            conn.close()
            count += 1
        except Exception as e:
            fail(f"Detection insert error: {e}")

    # 15 Transformative detections
    for url, platform in transformative_urls:
        vid = random.choice(video_ids)
        confidence = round(random.uniform(70.0, 85.0), 2)
        risk = random.randint(25, 50)
        reasoning = random.choice(transformative_reasonings)
        ts = random_ts()

        try:
            conn = sqlite3.connect(str(DB_PATH))
            conn.execute(
                """INSERT INTO detections
                     (video_id, source_url, platform, c_plus_plus_confidence,
                      gemini_classification, gemini_risk_score, gemini_reasoning,
                      status, detected_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);""",
                (vid, url, platform, confidence, "Transformative", risk, reasoning, "classified", ts),
            )
            conn.commit()
            conn.close()
            count += 1
        except Exception as e:
            fail(f"Detection insert error: {e}")

    # 10 Meme detections
    for url, platform in meme_urls:
        vid = random.choice(video_ids)
        confidence = round(random.uniform(40.0, 65.0), 2)
        risk = random.randint(5, 25)
        reasoning = random.choice(meme_reasonings)
        ts = random_ts()

        try:
            conn = sqlite3.connect(str(DB_PATH))
            conn.execute(
                """INSERT INTO detections
                     (video_id, source_url, platform, c_plus_plus_confidence,
                      gemini_classification, gemini_risk_score, gemini_reasoning,
                      status, detected_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);""",
                (vid, url, platform, confidence, "Meme", risk, reasoning, "classified", ts),
            )
            conn.commit()
            conn.close()
            count += 1
        except Exception as e:
            fail(f"Detection insert error: {e}")

    success(f"Inserted {count} detections (target: 50)")
    return count == 50


# ═══════════════════════════════════════════════════════════════════════════
#  STEP 9 — VERIFY EVERYTHING
# ═══════════════════════════════════════════════════════════════════════════

def step_9_verify() -> bool:
    banner("STEP 9 / 10 — VERIFICATION REPORT")
    all_ok = True

    # Video files
    checks = [
        (OFFICIAL_CLIP, "official_clip.mp4 exists and > 1 MB", True),
        (PIRACY_CLIP, "piracy_clip.mp4 exists", False),
        (TRANSFORMATIVE_CLIP, "transformative_clip.mp4 exists", False),
        (MEME_CLIP, "meme_clip.mp4 exists", False),
    ]

    for path, desc, check_size in checks:
        if path.exists():
            if check_size and path.stat().st_size < 1_000_000:
                warn(f"{desc} — file is only {path.stat().st_size / 1024:.0f} KB (< 1 MB)")
                all_ok = False
            else:
                size_mb = path.stat().st_size / 1024 / 1024
                success(f"{desc} ({size_mb:.1f} MB)")
        else:
            fail(desc)
            all_ok = False

    # Mock tweets
    tweets_path = TEST_DATA / "mock_tweets.json"
    if tweets_path.exists():
        try:
            data = json.loads(tweets_path.read_text(encoding="utf-8"))
            if len(data) == 10:
                success(f"mock_tweets.json has {len(data)} entries")
            else:
                warn(f"mock_tweets.json has {len(data)} entries (expected 10)")
                all_ok = False
        except Exception:
            fail("mock_tweets.json is invalid JSON")
            all_ok = False
    else:
        fail("mock_tweets.json not found")
        all_ok = False

    # Database checks
    try:
        conn = sqlite3.connect(str(DB_PATH))
        video_count = conn.execute("SELECT COUNT(*) FROM official_content;").fetchone()[0]
        detection_count = conn.execute("SELECT COUNT(*) FROM detections;").fetchone()[0]
        conn.close()

        if video_count == 12:
            success(f"Database has {video_count} official videos")
        else:
            warn(f"Database has {video_count} videos (expected 12)")
            all_ok = False

        if detection_count == 50:
            success(f"Database has {detection_count} detections")
        else:
            warn(f"Database has {detection_count} detections (expected 50)")
            all_ok = False

        # Show breakdown
        conn = sqlite3.connect(str(DB_PATH))
        for cls in ["Piracy", "Transformative", "Meme"]:
            cnt = conn.execute(
                "SELECT COUNT(*) FROM detections WHERE gemini_classification = ?;", (cls,)
            ).fetchone()[0]
            info(f"  {cls}: {cnt} detections")
        conn.close()
    except Exception as e:
        fail(f"Database check failed: {e}")
        all_ok = False

    return all_ok


# ═══════════════════════════════════════════════════════════════════════════
#  STEP 10 — PRINT DEMO INSTRUCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def step_10_instructions() -> None:
    banner("STEP 10 / 10 -- DEMO INSTRUCTIONS")
    print()
    print("  +==========================================+")
    print("  |         === DEMO IS READY ===            |")
    print("  +==========================================+")
    print("  |                                          |")
    print("  |  Step 1: python app.py                   |")
    print("  |  Step 2: Open http://localhost:5000       |")
    print("  |  Step 3: Go to Upload page, upload       |")
    print("  |          official_clip.mp4                |")
    print("  |  Step 4: Go to Detection Feed,           |")
    print("  |          click Refresh Scan               |")
    print("  |  Step 5: Show Piracy detection at         |")
    print("  |          94% confidence                   |")
    print("  |  Step 6: Show Meme detection -            |")
    print("  |          no takedown issued                |")
    print("  |  Step 7: Go to DMCA Reports,              |")
    print("  |          generate notice                   |")
    print("  |                                          |")
    print("  |    === YOU ARE READY TO RECORD ===       |")
    print("  +==========================================+")
    print()


# ═══════════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="SportsGuard AI — Real Data Setup Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Skip YouTube download if videos already exist",
    )
    args = parser.parse_args()

    start_time = time.time()

    print()
    print("  ╔══════════════════════════════════════════════════════╗")
    print("  ║       SportsGuard AI — Real Data Setup              ║")
    print("  ║       Google Solution Challenge 2026                ║")
    print("  ╚══════════════════════════════════════════════════════╝")

    results = {}

    # Step 1
    try:
        results["deps"] = step_1_check_deps()
    except Exception as e:
        fail(f"Step 1 crashed: {e}")
        results["deps"] = False

    # Step 2
    try:
        results["download"] = step_2_download(skip=args.skip_download)
    except Exception as e:
        fail(f"Step 2 crashed: {e}")
        results["download"] = False

    # Step 3
    try:
        results["piracy"] = step_3_piracy()
    except Exception as e:
        fail(f"Step 3 crashed: {e}")
        results["piracy"] = False

    # Step 4
    try:
        results["transformative"] = step_4_transformative()
    except Exception as e:
        fail(f"Step 4 crashed: {e}")
        results["transformative"] = False

    # Step 5
    try:
        results["meme"] = step_5_meme()
    except Exception as e:
        fail(f"Step 5 crashed: {e}")
        results["meme"] = False

    # Step 6
    try:
        results["tweets"] = step_6_mock_tweets()
    except Exception as e:
        fail(f"Step 6 crashed: {e}")
        results["tweets"] = False

    # Step 7
    try:
        results["metadata"] = step_7_metadata()
    except Exception as e:
        fail(f"Step 7 crashed: {e}")
        results["metadata"] = False

    # Step 8
    try:
        results["database"] = step_8_seed_database()
    except Exception as e:
        fail(f"Step 8 crashed: {e}")
        results["database"] = False

    # Step 9
    try:
        results["verify"] = step_9_verify()
    except Exception as e:
        fail(f"Step 9 crashed: {e}")
        results["verify"] = False

    # Final timing
    elapsed = time.time() - start_time
    print()
    print(f"  Total time: {elapsed:.1f} seconds")
    print()

    # Summary
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    if passed == total:
        success(f"ALL {total} STEPS PASSED")
    else:
        warn(f"{passed}/{total} steps passed — review errors above")

    # Step 10
    step_10_instructions()


if __name__ == "__main__":
    main()
