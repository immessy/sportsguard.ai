#!/usr/bin/env python3
"""
SportsGuard AI — Mock Scraper (Module D)
Simulates a live social-media feed for demo and testing.

Reads video files from ``test_data/videos/`` and matching JSON metadata
from ``test_data/metadata/``, then yields them in an infinite loop with
realistic random jitter (3-7 s between items).

Usage (library):
    from mock_scraper import simulate_feed
    for video_path, metadata in simulate_feed():
        print(metadata["post_id"], video_path)

Usage (CLI):
    python mock_scraper.py                    # default test_data/
    python mock_scraper.py --data-dir mydata  # custom directory
"""

import json
import logging
import os
import random
import sys
import time
from pathlib import Path
from typing import Dict, Iterator, Tuple

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s — %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("mock_scraper")


# ---------------------------------------------------------------------------
# Feed generator
# ---------------------------------------------------------------------------

def simulate_feed(
    data_dir: str = "test_data",
    *,
    min_delay: float = 3.0,
    max_delay: float = 7.0,
    loop: bool = True,
) -> Iterator[Tuple[str, Dict]]:
    """
    Yield ``(video_path, metadata_dict)`` pairs, optionally looping
    forever through the available test files.

    Parameters
    ----------
    data_dir : str
        Root directory containing ``videos/`` and ``metadata/`` sub-folders.
    min_delay, max_delay : float
        Range for random jitter between yields (seconds).
    loop : bool
        If True (default), loop infinitely over available files.
    """
    data_path = Path(data_dir)
    videos_dir = data_path / "videos"
    meta_dir = data_path / "metadata"

    if not meta_dir.is_dir():
        log.error("Metadata directory not found: %s", meta_dir)
        return

    # Collect metadata files sorted for deterministic order
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
                log.warning("Skipping bad metadata file %s — %s", mf.name, exc)
                continue

            # Resolve the video file path
            video_file = metadata.get("video_file", "")
            video_path = str(videos_dir / video_file)

            if not os.path.isfile(video_path):
                log.warning(
                    "Video file '%s' referenced in %s not found — yielding path anyway for pipeline testing.",
                    video_file, mf.name,
                )

            iteration += 1
            log.info(
                "[Feed #%d] %s — @%s on %s",
                iteration,
                metadata.get("post_id", "?"),
                metadata.get("user", "?"),
                metadata.get("platform", "?"),
            )

            yield video_path, metadata

            # Realistic delay
            delay = random.uniform(min_delay, max_delay)
            log.debug("Sleeping %.1f s …", delay)
            time.sleep(delay)

        if not loop:
            break

    log.info("Feed exhausted after %d items.", iteration)


# ---------------------------------------------------------------------------
# CLI mode
# ---------------------------------------------------------------------------

def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="SportsGuard Mock Scraper")
    parser.add_argument("--data-dir", default="test_data", help="Path to test_data directory")
    parser.add_argument("--once", action="store_true", help="Run through files only once (no loop)")
    args = parser.parse_args()

    try:
        for video_path, meta in simulate_feed(args.data_dir, loop=not args.once):
            print(f"  → Video : {video_path}")
            print(f"    Post  : {meta.get('text', '')}")
            print(f"    User  : {meta.get('user', '')} on {meta.get('platform', '')}")
            print()
    except KeyboardInterrupt:
        print("\n[mock_scraper] Stopped.")


if __name__ == "__main__":
    main()
