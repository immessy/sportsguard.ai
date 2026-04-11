
# dashboard/api_client.py
# ─────────────────────────────────────────────────────────────────────────────
# Bridge between the Streamlit dashboard and Member 1's Flask backend.
# Every function has a silent mock fallback — the UI never crashes if
# Flask is offline or not yet built.
#
# Branch: armaal/dev-frontend
# Integration: swap MOCK_MODE = False when Flask is confirmed at localhost:5000
# ─────────────────────────────────────────────────────────────────────────────

import requests
import datetime

# ─── Config ───────────────────────────────────────────────────────────────────
BASE_URL  = "http://localhost:5000"
TIMEOUT   = 5        # seconds before giving up on a request
MOCK_MODE = True     # Set False when Member 1's Flask is confirmed running

# ─────────────────────────────────────────────────────────────────────────────
# MOCK DATA
# Schema must be IDENTICAL to real API responses.
# Agreed with Member 1 on Day 1 — do not change field names here without
# also updating the Flask routes.
# ─────────────────────────────────────────────────────────────────────────────

MOCK_STATS = {
    "total_protected":        12,
    "violations_today":       47,
    "avg_detection_seconds":  6.3,
}

MOCK_DETECTIONS = {
    "detections": [
        {
            "id":                      1,
            "source_url":              "stream.pro/ipl-live-m42",
            "c_plus_plus_confidence":  0.998,
            "gemini_classification":   "Piracy",
            "gemini_risk_score":       9,
            "detected_at":             "2026-04-11 14:22:01",
            "video_id":                3,
        },
        {
            "id":                      2,
            "source_url":              "youtube.com/v=xk2mP9qL",
            "c_plus_plus_confidence":  0.842,
            "gemini_classification":   "Transformative",
            "gemini_risk_score":       5,
            "detected_at":             "2026-04-11 14:21:44",
            "video_id":                2,
        },
        {
            "id":                      3,
            "source_url":              "twitter.com/fan_cricket_09",
            "c_plus_plus_confidence":  0.421,
            "gemini_classification":   "Meme",
            "gemini_risk_score":       2,
            "detected_at":             "2026-04-11 14:20:12",
            "video_id":                1,
        },
        {
            "id":                      4,
            "source_url":              "iptv-portal.net/channel/ipl",
            "c_plus_plus_confidence":  0.946,
            "gemini_classification":   "Piracy",
            "gemini_risk_score":       10,
            "detected_at":             "2026-04-11 14:19:55",
            "video_id":                3,
        },
        {
            "id":                      5,
            "source_url":              "t.me/cricket_leaks_2026",
            "c_plus_plus_confidence":  0.911,
            "gemini_classification":   "Piracy",
            "gemini_risk_score":       8,
            "detected_at":             "2026-04-11 14:18:30",
            "video_id":                3,
        },
        {
            "id":                      6,
            "source_url":              "tiktok.com/@ipl_fan_clips",
            "c_plus_plus_confidence":  0.389,
            "gemini_classification":   "Meme",
            "gemini_risk_score":       1,
            "detected_at":             "2026-04-11 14:17:10",
            "video_id":                1,
        },
    ]
}

MOCK_UPLOAD_RESPONSE = {
    "video_id":         7,
    "title":            "IPL Match 42 Highlights",
    "frames_processed": 143,
    "status":           "protected",
    "registry_id":      "SG-7729-AX",
    "fingerprint": {
        "frames_processed": 143,
        "hash_algorithm":   "pHash-512/Sentinel",
        "root_merkle":      "0xBf2a...f921",
    },
    "protection": {
        "takedown_enabled": True,
        "whitelist":        ["youtube.com/official"],
    },
}

# New detection pushed by mock_scraper.py simulation
MOCK_NEW_DETECTION = {
    "id":                      99,
    "source_url":              "t.me/ipl_leaks_channel",
    "c_plus_plus_confidence":  0.967,
    "gemini_classification":   "Piracy",
    "gemini_risk_score":       10,
    "detected_at":             datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "video_id":                3,
}


# ─────────────────────────────────────────────────────────────────────────────
# HEALTH CHECK
# ─────────────────────────────────────────────────────────────────────────────

def check_backend_health() -> bool:
    """
    Ping Flask at GET /api/health.
    Returns True if backend is reachable and returns status 200.
    Returns False silently if offline — never raises.

    Expected response: {"status": "ok"}
    """
    if MOCK_MODE:
        return False
    try:
        r = requests.get(f"{BASE_URL}/api/health", timeout=2)
        return r.status_code == 200
    except Exception:
        return False


# ─────────────────────────────────────────────────────────────────────────────
# GET STATS
# ─────────────────────────────────────────────────────────────────────────────

def get_stats() -> dict:
    """
    GET /api/dashboard/stats
    Returns aggregate metrics for the dashboard home page.

    Real response schema:
    {
        "total_protected":       int,
        "violations_today":      int,
        "avg_detection_seconds": float
    }

    Fallback: MOCK_STATS (same schema)
    """
    if MOCK_MODE:
        return MOCK_STATS
    try:
        r = requests.get(
            f"{BASE_URL}/api/dashboard/stats",
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        # Flask not running — silent fallback
        return MOCK_STATS
    except requests.exceptions.Timeout:
        return MOCK_STATS
    except requests.exceptions.HTTPError as e:
        print(f"[api_client] get_stats HTTP error: {e}")
        return MOCK_STATS
    except Exception as e:
        print(f"[api_client] get_stats unexpected error: {e}")
        return MOCK_STATS


# ─────────────────────────────────────────────────────────────────────────────
# RUN SCAN
# ─────────────────────────────────────────────────────────────────────────────

def run_scan() -> dict:
    """
    GET /api/scan
    Triggers Member 2's mock_scraper pipeline: C++ matcher → Gemini classifier.
    Returns all detections found in the current monitoring window.

    Real response schema:
    {
        "detections": [
            {
                "id":                     int,
                "source_url":             str,
                "c_plus_plus_confidence": float,   # 0.0 to 1.0
                "gemini_classification":  str,     # "Piracy" | "Transformative" | "Meme"
                "gemini_risk_score":      int,     # 1 to 10
                "detected_at":            str,     # "YYYY-MM-DD HH:MM:SS"
                "video_id":               int
            }
        ]
    }

    Fallback: MOCK_DETECTIONS (same schema)
    """
    if MOCK_MODE:
        return MOCK_DETECTIONS
    try:
        r = requests.get(
            f"{BASE_URL}/api/scan",
            timeout=TIMEOUT,
        )
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        return MOCK_DETECTIONS
    except requests.exceptions.Timeout:
        return MOCK_DETECTIONS
    except requests.exceptions.HTTPError as e:
        print(f"[api_client] run_scan HTTP error: {e}")
        return MOCK_DETECTIONS
    except Exception as e:
        print(f"[api_client] run_scan unexpected error: {e}")
        return MOCK_DETECTIONS


# ─────────────────────────────────────────────────────────────────────────────
# UPLOAD VIDEO
# ─────────────────────────────────────────────────────────────────────────────

def upload_video(file_bytes: bytes, filename: str, title: str) -> dict:
    """
    POST /api/upload
    Sends a video file to Flask which triggers:
      fingerprint_engine.py → OpenCV frame extraction → pHash → SQLite

    Request: multipart/form-data
        file_bytes : raw bytes of the uploaded video
        filename   : original filename e.g. "match42.mp4"
        title      : user-entered content title

    Real response schema:
    {
        "video_id":         int,
        "title":            str,
        "frames_processed": int,
        "status":           "protected" | "error",
        "registry_id":      str,
        "fingerprint": {
            "frames_processed": int,
            "hash_algorithm":   str,
            "root_merkle":      str
        },
        "protection": {
            "takedown_enabled": bool,
            "whitelist":        [str]
        }
    }

    Fallback: MOCK_UPLOAD_RESPONSE with real title injected
    """
    if MOCK_MODE:
        mock = MOCK_UPLOAD_RESPONSE.copy()
        mock["title"] = title
        return mock
    try:
        r = requests.post(
            f"{BASE_URL}/api/upload",
            files={"video": (filename, file_bytes, "video/mp4")},
            data={"title": title},
            timeout=30,   # uploads take longer
        )
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        mock = MOCK_UPLOAD_RESPONSE.copy()
        mock["title"] = title
        return mock
    except requests.exceptions.Timeout:
        return {
            "status":  "error",
            "message": "Upload timed out. Try a smaller clip for the demo.",
        }
    except requests.exceptions.HTTPError as e:
        print(f"[api_client] upload_video HTTP error: {e}")
        mock = MOCK_UPLOAD_RESPONSE.copy()
        mock["title"] = title
        return mock
    except Exception as e:
        print(f"[api_client] upload_video unexpected error: {e}")
        mock = MOCK_UPLOAD_RESPONSE.copy()
        mock["title"] = title
        return mock


# ─────────────────────────────────────────────────────────────────────────────
# SIMULATE DETECTION  (demo helper — calls mock_scraper indirectly)
# ─────────────────────────────────────────────────────────────────────────────

def get_simulated_detection() -> dict:
    """
    Returns a single new high-risk detection for the demo Simulate button.
    Generates a fresh timestamp each time so it looks live.

    Not a real endpoint — purely for demo day.
    """
    d = MOCK_NEW_DETECTION.copy()
    d["detected_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return d