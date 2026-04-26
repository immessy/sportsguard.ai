#!/usr/bin/env python3
"""
SportsGuard AI — Firebase Feeder (The Brain)
Simulates a live social-media feed and pushes detections directly to Firestore.

Reads video files and metadata, simulates the C++ match, and pushes 
the final JSON payload to Firebase so the React frontend updates in real-time.
"""

import json
import logging
import os
import random
import time
from pathlib import Path
from typing import Dict, Iterator, Tuple

# 1. Import Firebase Admin SDK
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s — %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("mock_scraper")

# ---------------------------------------------------------------------------
# Firebase Initialization
# ---------------------------------------------------------------------------
def initialize_firebase():
    """Initializes the Firebase Admin SDK using the service account key."""
    try:
        # Assumes you downloaded your key to the project root
        cred = credentials.Certificate("serviceAccountKey.json")
        firebase_admin.initialize_app(cred)
        log.info("✅ Firebase initialized successfully.")
        return firestore.client()
    except Exception as e:
        log.error("❌ Failed to initialize Firebase. Is serviceAccountKey.json present?")
        log.error(str(e))
        exit(1)

# ---------------------------------------------------------------------------
# Feed generator (Untouched from your version)
# ---------------------------------------------------------------------------
def simulate_feed(
    data_dir: str = "test_data",
    *,
    min_delay: float = 3.0,
    max_delay: float = 7.0,
    loop: bool = True,
) -> Iterator[Tuple[str, Dict]]:
    
    data_path = Path(data_dir)
    videos_dir = data_path / "videos"
    meta_dir = data_path / "metadata"

    if not meta_dir.is_dir():
        log.error("Metadata directory not found: %s", meta_dir)
        return

    meta_files = sorted(meta_dir.glob("*.json"))
    if not meta_files:
        log.error("No metadata JSON files in %s", meta_dir)
        return

    log.info("Loaded %d scenario(s) from %s", len(meta_files), meta_dir)

    iteration = 0
    while True:
        for mf in meta_files:
            try:
                with open(mf, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
            except (json.JSONDecodeError, OSError) as exc:
                continue

            video_file = metadata.get("video_file", "")
            video_path = str(videos_dir / video_file)

            iteration += 1
            yield video_path, metadata

            delay = random.uniform(min_delay, max_delay)
            log.debug("Sleeping %.1f s …", delay)
            time.sleep(delay)

        if not loop:
            break

# ---------------------------------------------------------------------------
# The Bridge: Push to Firestore
# ---------------------------------------------------------------------------
def push_to_firestore(db, metadata: Dict):
    """Formats the metadata and pushes it to the Firestore 'detections' collection."""
    
    # Extract data from your JSON (or generate realistic mocks)
    platform = metadata.get("platform", "Twitter")
    post_text = metadata.get("text", "Suspicious sports content detected.")
    
    # If your JSON doesn't already have classification, we mock Gemini's response here
    # (Or you could literally call Gemini via API right here before pushing)
    classification = metadata.get("classification", "Piracy")
    risk_score = metadata.get("risk_score", random.randint(75, 99))
    reasoning = metadata.get("reasoning", "Raw broadcast footage redistributed without authorization.")
    source_url = metadata.get("source_url", f"https://{platform.lower()}.com/mock/status/{random.randint(1000,9999)}")
    
    # 1. Format exactly as the React frontend expects
    doc_data = {
        "platform": platform,
        "post_text": post_text,
        "match_confidence": random.randint(85, 99), # Simulating C++ output
        "classification": classification,
        "risk_score": risk_score,
        "reasoning": reasoning,
        "detected_at": firestore.SERVER_TIMESTAMP, # Tells Firebase to use exact current time
        "source_url": source_url,
        "status": "action_required" if risk_score > 70 else "reviewed"
    }

    try:
        # 2. Push to the 'detections' collection
        db.collection(u'detections').add(doc_data)
        log.info(f"🚀 PUSHED TO CLOUD: [{classification}] {platform} (Score: {risk_score})")
    except Exception as e:
        log.error(f"Failed to push to Firestore: {e}")

# ---------------------------------------------------------------------------
# CLI mode
# ---------------------------------------------------------------------------
def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="SportsGuard Mock Scraper -> Firebase Bridge")
    parser.add_argument("--data-dir", default="test_data", help="Path to test_data directory")
    parser.add_argument("--once", action="store_true", help="Run through files only once")
    args = parser.parse_args()

    # Initialize the Database connection
    db = initialize_firebase()

    try:
        for video_path, meta in simulate_feed(args.data_dir, loop=not args.once):
            print(f"\n[LOCAL] Matching Engine flagged: {meta.get('text', '')[:40]}...")
            
            # Send the detection across the bridge to the hosted UI
            push_to_firestore(db, meta)
            
    except KeyboardInterrupt:
        print("\n[mock_scraper] Stopped.")

if __name__ == "__main__":
    main()