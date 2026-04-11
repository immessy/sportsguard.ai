#!/usr/bin/env python3
"""
SportsGuard AI — Flask REST API (Module E)
Provides the HTTP backend for the SportsGuard content-protection pipeline.

Endpoints:
    POST  /api/upload           — Upload & fingerprint an official video
    GET   /api/scan             — Scan the mock feed for piracy
    GET   /api/dashboard/stats  — Aggregate dashboard statistics
    GET   /api/detections       — List detections (paginated)
    GET   /api/videos           — List protected videos

Run:
    python app.py                           # development mode
    FLASK_ENV=production flask run          # production mode
"""

import logging
import os
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

from flask import Flask, jsonify, request
from flask_cors import CORS

from database_helpers import (
    close_connection,
    get_all_detections,
    get_all_videos,
    get_dashboard_stats,
    get_all_fingerprints,
    insert_detection,
)
from fingerprint_engine import fingerprint_video
from gemini_analyzer import analyze_content
from mock_scraper import simulate_feed
from setup_database import init_database

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DATABASE_PATH = os.environ.get("DATABASE_PATH", "sportsguard.db")
UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "uploads")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100 MB

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s — %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("sportsguard.api")

# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH
CORS(app)

# Ensure required directories exist
Path(UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)

# Initialise database on startup
init_database(DATABASE_PATH)

# ---------------------------------------------------------------------------
# Mock-feed generator (singleton iterator across requests)
# ---------------------------------------------------------------------------
_feed_iter = None


def _get_feed_iter():
    global _feed_iter
    if _feed_iter is None:
        # Use 0 delay so API calls don't block for 5 s
        _feed_iter = simulate_feed("test_data", min_delay=0, max_delay=0, loop=True)
    return _feed_iter


# ---------------------------------------------------------------------------
# Matching helper — try native C++ module, fall back to pure-Python
# ---------------------------------------------------------------------------

def _match_hash(query_hash_int: int, db_hashes, threshold: int = 5):
    """
    Attempt to use the compiled ``fast_matcher`` C++ extension.
    Falls back to a pure-Python implementation if the extension is unavailable.
    """
    try:
        import fast_matcher  # type: ignore
        result = fast_matcher.find_best_match(query_hash_int, db_hashes, threshold)
        return result.to_dict()
    except ImportError:
        log.warning("fast_matcher C++ extension not available — using pure-Python fallback.")
        best_dist = 65
        best_vid = -1
        for h, vid in db_hashes:
            dist = bin(query_hash_int ^ h).count("1")
            if dist < best_dist:
                best_dist = dist
                best_vid = vid
        if best_dist <= threshold:
            confidence = (64 - best_dist) / 64.0 * 100
            return {"video_id": best_vid, "confidence": confidence, "hamming_distance": best_dist}
        return {"video_id": -1, "confidence": 0.0, "hamming_distance": best_dist}


# ═══════════════════════════════════════════════════════════════════════════
#  ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════

# ── POST /api/upload ──────────────────────────────────────────────────────

@app.route("/api/upload", methods=["POST"])
def upload_video():
    """Upload an official video and fingerprint it."""
    try:
        if "video" not in request.files:
            return jsonify({"error": "No video file in request"}), 400

        file = request.files["video"]
        title = request.form.get("title", file.filename or "Untitled")

        if not file.filename:
            return jsonify({"error": "Empty filename"}), 400

        # Validate extension
        ext = Path(file.filename).suffix.lower()
        if ext not in (".mp4", ".mov", ".avi", ".mkv"):
            return jsonify({"error": f"Unsupported format: {ext}"}), 400

        # Save to uploads/
        save_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(save_path)
        log.info("Saved upload → %s", save_path)

        # Fingerprint
        video_id = fingerprint_video(save_path, title, DATABASE_PATH)

        # Count frames
        from database_helpers import get_fingerprints_for_video
        frames = get_fingerprints_for_video(video_id, db_path=DATABASE_PATH)

        return jsonify({
            "video_id": video_id,
            "status": "success",
            "total_frames": len(frames),
        }), 201

    except Exception as exc:
        log.error("Upload failed: %s", exc)
        traceback.print_exc()
        return jsonify({"error": str(exc)}), 500


# ── GET /api/scan ─────────────────────────────────────────────────────────

@app.route("/api/scan", methods=["GET"])
def scan_feed():
    """Pull next item from mock feed, match, classify, and return result."""
    try:
        t0 = time.perf_counter()

        # 1. Get next suspect video from mock feed
        feed = _get_feed_iter()
        video_path, metadata = next(feed)

        # 2. Load all fingerprints from the database
        all_fps = get_all_fingerprints(db_path=DATABASE_PATH)
        if not all_fps:
            return jsonify({
                "match_found": False,
                "message": "No official content registered yet. Upload videos first.",
                "source_url": metadata.get("text", ""),
            }), 200

        db_hashes = [(int(fp["phash"], 16), fp["video_id"]) for fp in all_fps]

        # 3. Extract a single frame from the suspect video and hash it
        try:
            import cv2
            import imagehash
            from PIL import Image as PILImage

            cap = cv2.VideoCapture(video_path)
            ret, frame = cap.read()
            cap.release()

            if ret and frame is not None:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                pil_img = PILImage.fromarray(gray)
                query_hash = imagehash.phash(pil_img, hash_size=8)
                query_hash_int = int(str(query_hash), 16)
            else:
                # If video can't be read, generate random hash for demo
                import random
                query_hash_int = random.getrandbits(64)
                pil_img = PILImage.new("RGB", (320, 240))
        except Exception:
            import random
            query_hash_int = random.getrandbits(64)
            pil_img = None

        # 4. Match against database using C++ engine (or fallback)
        match_result = _match_hash(query_hash_int, db_hashes, threshold=10)

        elapsed = time.perf_counter() - t0

        if match_result["video_id"] == -1:
            return jsonify({
                "match_found": False,
                "confidence": 0,
                "source_url": metadata.get("text", ""),
                "platform": metadata.get("platform", ""),
                "detection_time_s": round(elapsed, 3),
            }), 200

        # 5. If match confidence >= 85%, run Gemini classification
        classification_data = {"classification": "Unknown", "risk_score": 50, "reasoning": "Below confidence threshold"}
        if match_result["confidence"] >= 85.0 and pil_img is not None and GEMINI_API_KEY:
            classification_data = analyze_content(
                pil_img,
                metadata.get("text", ""),
                api_key=GEMINI_API_KEY,
            )

        # 6. Store detection
        detection_id = insert_detection(
            video_id=match_result["video_id"],
            source_url=metadata.get("text", ""),
            platform=metadata.get("platform", "Unknown"),
            confidence=match_result["confidence"],
            classification=classification_data.get("classification"),
            risk_score=classification_data.get("risk_score"),
            reasoning=classification_data.get("reasoning"),
            db_path=DATABASE_PATH,
        )

        total_time = time.perf_counter() - t0

        return jsonify({
            "match_found": True,
            "video_id": match_result["video_id"],
            "confidence": round(match_result["confidence"], 2),
            "classification": classification_data.get("classification", "Unknown"),
            "risk_score": classification_data.get("risk_score", 50),
            "source_url": metadata.get("text", ""),
            "platform": metadata.get("platform", ""),
            "detected_at": datetime.now(timezone.utc).isoformat(),
            "detection_id": detection_id,
            "detection_time_s": round(total_time, 3),
        }), 200

    except StopIteration:
        return jsonify({"error": "Feed exhausted"}), 503
    except Exception as exc:
        log.error("Scan failed: %s", exc)
        traceback.print_exc()
        return jsonify({"error": str(exc)}), 500


# ── GET /api/dashboard/stats ─────────────────────────────────────────────

@app.route("/api/dashboard/stats", methods=["GET"])
def dashboard_stats():
    """Return aggregate dashboard statistics."""
    try:
        stats = get_dashboard_stats(db_path=DATABASE_PATH)
        return jsonify(stats), 200
    except Exception as exc:
        log.error("Stats failed: %s", exc)
        return jsonify({"error": str(exc)}), 500


# ── GET /api/detections ──────────────────────────────────────────────────

@app.route("/api/detections", methods=["GET"])
def list_detections():
    """Return paginated list of detections."""
    try:
        limit = request.args.get("limit", 50, type=int)
        offset = request.args.get("offset", 0, type=int)
        limit = min(limit, 200)  # cap at 200
        detections = get_all_detections(limit=limit, offset=offset, db_path=DATABASE_PATH)
        return jsonify({"detections": detections, "limit": limit, "offset": offset}), 200
    except Exception as exc:
        log.error("Detections list failed: %s", exc)
        return jsonify({"error": str(exc)}), 500


# ── GET /api/videos ──────────────────────────────────────────────────────

@app.route("/api/videos", methods=["GET"])
def list_videos():
    """Return list of all protected videos."""
    try:
        videos = get_all_videos(db_path=DATABASE_PATH)
        return jsonify({"videos": videos}), 200
    except Exception as exc:
        log.error("Videos list failed: %s", exc)
        return jsonify({"error": str(exc)}), 500


# ── Health check ─────────────────────────────────────────────────────────

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}), 200


# ---------------------------------------------------------------------------
# Teardown
# ---------------------------------------------------------------------------

@app.teardown_appcontext
def shutdown_session(exception=None):
    close_connection(DATABASE_PATH)


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "1") == "1"
    port = int(os.environ.get("PORT", 5000))
    log.info("Starting SportsGuard API on port %d (debug=%s)", port, debug_mode)
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
