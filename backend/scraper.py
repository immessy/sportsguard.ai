from __future__ import annotations

from datetime import datetime, timezone
import json
import os
import tempfile
from typing import Any
from urllib.parse import urlparse
import time

import requests

from backend.database import supabase
from backend.gemini_agent import classify_content
from backend.vision import compare_hashes, hash_image
from backend.state import latest_scan_status   # <-- shared state

REDDIT_SUBREDDIT = os.getenv("REDDIT_SUBREDDIT", "sports")
HASH_DISTANCE_THRESHOLD = int(os.getenv("HASH_DISTANCE_THRESHOLD", "10"))
REDDIT_URL = f"https://www.reddit.com/r/{REDDIT_SUBREDDIT}/hot.json?limit=10"
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}


def _create_image_session() -> requests.Session:
    """Return a requests Session with headers that bypass Reddit's image CDN restrictions."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.reddit.com/",
        "Sec-Fetch-Dest": "image",
        "Sec-Fetch-Mode": "no-cors",
        "Sec-Fetch-Site": "cross-site",
    })
    return session


def _download_preview(url: str) -> bytes:
    session = _create_image_session()
    for attempt in range(1, 4):
        try:
            resp = session.get(url, timeout=30)
            resp.raise_for_status()
            return resp.content
        except requests.exceptions.RequestException as e:
            print(f"[SCAN] Download attempt {attempt} failed: {e}")
            if attempt < 3:
                time.sleep(2)
            else:
                raise


def _safe_preview_url(post_data: dict[str, Any]) -> str | None:
    try:
        # 1. Check if the post itself is a direct image (e.g. i.redd.it)
        url = post_data.get("url", "")
        if isinstance(url, str) and url.startswith("http") and any(
            url.lower().endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".gif", ".webp")
        ):
            return url

        # 2. Use the thumbnail if it's a full URL
        thumbnail = post_data.get("thumbnail")
        if isinstance(thumbnail, str) and thumbnail.startswith("http"):
            return thumbnail

        # 3. Try the preview image (for embedded media)
        preview = post_data.get("preview") or {}
        images = preview.get("images") or []
        if images:
            source = images[0].get("source") or {}
            candidate = source.get("url")
            if isinstance(candidate, str) and candidate.startswith("http"):
                return candidate.replace("&amp;", "&")
    except Exception:
        return None
    return None


def _fetch_official_assets() -> list[dict[str, Any]]:
    response = supabase.table("official_assets").select("id, filename, hashes").execute()
    return response.data or []


def _normalize_hashes(raw_hashes: Any) -> list[str]:
    if isinstance(raw_hashes, list):
        return [item for item in raw_hashes if isinstance(item, str)]
    if isinstance(raw_hashes, str):
        try:
            parsed = json.loads(raw_hashes)
            if isinstance(parsed, list):
                return [item for item in parsed if isinstance(item, str)]
        except json.JSONDecodeError:
            return []
    return []


def _insert_detection(payload: dict[str, Any]) -> None:
    supabase.table("detections").insert(payload).execute()


def scrape_and_check() -> None:
    # --- Update scan status to "running" ---
    latest_scan_status["status"] = "running"
    latest_scan_status["message"] = "Scan is in progress..."

    print("[SCAN] Starting Reddit scan...")
    try:
        official_assets = _fetch_official_assets()
        print(f"[SCAN] Fetched {len(official_assets)} official asset(s) from Supabase.")
        if not official_assets:
            print("[SCAN] No official assets. Aborting scan.")
            latest_scan_status["status"] = "completed"
            latest_scan_status["message"] = "Scan aborted: no official assets."
            return

        reddit_response = requests.get(REDDIT_URL, headers=REQUEST_HEADERS, timeout=20)
        reddit_response.raise_for_status()
        listing = reddit_response.json()
        children = (((listing or {}).get("data") or {}).get("children")) or []
        print(f"[SCAN] Reddit /r/{REDDIT_SUBREDDIT} returned {len(children)} post(s).")
    except Exception as e:
        print(f"[SCAN] Failed to fetch Reddit posts: {e}")
        latest_scan_status["status"] = "completed"
        latest_scan_status["message"] = f"Scan failed: {e}"
        return

    match_attempts = 0
    insertions = 0
    for idx, child in enumerate(children, start=1):
        temp_image_path: str | None = None
        try:
            post_data = (child or {}).get("data") or {}
            preview_url = _safe_preview_url(post_data)
            reddit_post_url = post_data.get("url")
            title = post_data.get("title", "Untitled Reddit post")

            if not preview_url:
                print(f"[SCAN] Post {idx} skipped – no preview image available. Title: '{title[:60]}'")
                continue
            if not reddit_post_url:
                print(f"[SCAN] Post {idx} skipped – missing Reddit URL. Title: '{title[:60]}'")
                continue

            print(f"[SCAN] Post {idx}: '{title[:60]}' – preview URL: {preview_url[:60]}...")

            # --- Use the browser‑like session to download ---
            try:
                image_bytes = _download_preview(preview_url)
            except Exception as dl_err:
                print(f"[SCAN] Post {idx} download failed: {dl_err}")
                continue

            suffix = os.path.splitext(urlparse(preview_url).path)[1] or ".jpg"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                temp_file.write(image_bytes)
                temp_image_path = temp_file.name

            thumbnail_hash = hash_image(temp_image_path)
            print(f"[SCAN] Post {idx} thumbnail hash: {thumbnail_hash}")

            closest_match: dict[str, Any] | None = None
            closest_distance: int | None = None

            for asset in official_assets:
                stored_hashes = _normalize_hashes(asset.get("hashes"))
                for official_hash in stored_hashes:
                    distance = compare_hashes(thumbnail_hash, official_hash)
                    if closest_distance is None or distance < closest_distance:
                        closest_distance = distance
                        closest_match = asset

            print(f"[SCAN] Post {idx} best distance = {closest_distance} (threshold = {HASH_DISTANCE_THRESHOLD})")
            if closest_match is None or closest_distance is None or closest_distance >= HASH_DISTANCE_THRESHOLD:
                print(f"[SCAN] Post {idx} rejected – distance {closest_distance} >= threshold {HASH_DISTANCE_THRESHOLD}")
                continue

            match_attempts += 1
            print(f"[SCAN] Post {idx} MATCH FOUND! Calling Gemini for classification...")
            gemini_result = classify_content(title)
            print(f"[SCAN] Gemini classification: {gemini_result['classification']} ({gemini_result['confidence']}) — {gemini_result['reasoning']}")

            # Map classification to a real enforcement risk score
            classification = gemini_result["classification"]
            confidence = gemini_result["confidence"]
            
            if classification == "Piracy":
                real_risk = max(85, confidence)   # always high if piracy
            elif classification == "Meme":
                real_risk = 35                    # medium – may still need review
            else:  # Transformative
                real_risk = min(15, confidence)   # low risk

            _insert_detection(
                {
                    "reddit_url": reddit_post_url,
                    "reddit_post_title": title,
                    "classification": classification,
                    "risk_score": real_risk,
                    "reasoning": gemini_result["reasoning"],
                    "matched_asset_id": closest_match.get("id"),
                    "matched_asset_filename": closest_match.get("filename"),
                    "thumbnail_hash": thumbnail_hash,
                    "distance": int(closest_distance),
                    "scanned_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            insertions += 1
            print(f"[SCAN] Post {idx} detection inserted into Supabase.")
        except Exception as e:
            print(f"[SCAN] Error processing post {idx} ({post_data.get('url', '??')}): {e}")
            continue
        finally:
            if temp_image_path and os.path.exists(temp_image_path):
                try:
                    os.remove(temp_image_path)
                except OSError:
                    pass

    # --- Final scan summary ---
    print(f"[SCAN] Scan complete. Matches attempted: {match_attempts}, detections inserted: {insertions}")
    latest_scan_status["status"] = "completed"
    latest_scan_status["message"] = (
        f"Scanned {len(children)} posts, {match_attempts} visual matches, {insertions} detections inserted."
    )