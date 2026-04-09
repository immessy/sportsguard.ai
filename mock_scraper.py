"""
mock_scraper.py
===============
SportsGuard AI - Module D: Mock Data Simulation
Member 2 (AI & Data Specialist)

Simulates a live Twitter/X video feed by pairing local video files with
mock tweet metadata from test_data/mock_tweets.json.

Yields one {video_path, tweet_text, username, timestamp} event every 5 seconds
in an infinite loop — perfect for live demo purposes.

Usage:
    python mock_scraper.py            # start live simulation (Ctrl+C to stop)
    from mock_scraper import stream_feed  # import in other modules
"""

import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("mock_scraper")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
TEST_DATA_DIR = Path("test_data")
MOCK_TWEETS_FILE = TEST_DATA_DIR / "mock_tweets.json"
SUPPORTED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
STREAM_INTERVAL_SECONDS = 5  # delay between yielded events


# ---------------------------------------------------------------------------
# Data loading helpers
# ---------------------------------------------------------------------------

def load_mock_tweets(json_path: "str | Path" = MOCK_TWEETS_FILE) -> list[dict]:
    """Load mock tweet metadata from a JSON file.

    Expected JSON format — a list of tweet objects::

        [
          {
            "tweet_text": "Look at this crazy goal! #soccer",
            "username": "@soccerfan99",
            "timestamp": "2026-04-08T12:00:00Z"
          },
          ...
        ]

    Args:
        json_path: Path to the mock tweets JSON file.

    Returns:
        List of tweet dicts.

    Raises:
        FileNotFoundError: If the JSON file does not exist.
        json.JSONDecodeError: If the file contains invalid JSON.
    """
    path = Path(json_path)
    if not path.exists():
        raise FileNotFoundError(
            f"Mock tweets file not found: {path}\n"
            "Run: python mock_scraper.py --init  to create sample data."
        )
    with open(path, "r", encoding="utf-8") as f:
        tweets = json.load(f)
    logger.info("Loaded %d mock tweets from '%s'.", len(tweets), path)
    return tweets


def discover_videos(data_dir: "str | Path" = TEST_DATA_DIR) -> list[Path]:
    """Scan the test_data directory for video files.

    Args:
        data_dir: Directory to search for video files.

    Returns:
        Sorted list of Path objects for found video files.
        Returns empty list if directory does not exist.
    """
    directory = Path(data_dir)
    if not directory.exists():
        logger.warning("test_data directory not found: %s", directory)
        return []

    videos = sorted(
        p for p in directory.rglob("*")
        if p.is_file() and p.suffix.lower() in SUPPORTED_VIDEO_EXTENSIONS
    )
    logger.info("Discovered %d video file(s) in '%s'.", len(videos), directory)
    return videos


# ---------------------------------------------------------------------------
# Feed simulation
# ---------------------------------------------------------------------------

def _pair_videos_with_tweets(
    videos: list[Path],
    tweets: list[dict],
) -> list[dict]:
    """Create (video, tweet) pairs by cycling through both lists.

    If there are more tweets than videos (or vice-versa) the shorter list
    cycles round-robin to fill out the pairings.

    Args:
        videos: List of video file paths.
        tweets: List of tweet metadata dicts.

    Returns:
        List of combined event dicts ready for streaming.
    """
    if not videos and not tweets:
        return []

    n = max(len(videos), len(tweets))
    pairs = []
    for i in range(n):
        tweet = tweets[i % len(tweets)] if tweets else {}
        video = videos[i % len(videos)] if videos else None

        pairs.append({
            "video_path": str(video) if video else None,
            "tweet_text": tweet.get("tweet_text", ""),
            "username": tweet.get("username", "@unknown"),
            "timestamp": tweet.get(
                "timestamp",
                datetime.now(timezone.utc).isoformat(),
            ),
        })
    return pairs


def stream_feed(
    data_dir: "str | Path" = TEST_DATA_DIR,
    tweets_file: "str | Path" = MOCK_TWEETS_FILE,
    interval: float = STREAM_INTERVAL_SECONDS,
    max_cycles: int = 0,
) -> Generator[dict, None, None]:
    """Simulate a live social media video feed.

    Yields one event dict every ``interval`` seconds in a (near-)infinite loop.
    Each event represents a social media post containing a video.

    Args:
        data_dir: Directory containing test video files.
        tweets_file: Path to mock_tweets.json.
        interval: Seconds between yielded events (default = 5).
        max_cycles: Maximum number of full cycles through the data before
                    stopping. Set to 0 (default) for infinite loop.

    Yields:
        Dict with the following schema::

            {
                "video_path": str,       # absolute/relative path to video file
                "tweet_text": str,       # social media post text
                "username":   str,       # @handle of the poster
                "timestamp":  str,       # ISO 8601 timestamp string
            }

    Example:
        >>> for event in stream_feed(max_cycles=1):
        ...     print(event["username"], event["tweet_text"][:40])
    """
    videos = discover_videos(data_dir)
    tweets = load_mock_tweets(tweets_file)

    if not videos:
        logger.warning(
            "No video files found in '%s'. Streaming tweet-only events.", data_dir
        )
    if not tweets:
        raise RuntimeError(f"No tweets loaded from '{tweets_file}'.")

    pairs = _pair_videos_with_tweets(videos, tweets)
    logger.info(
        "Feed ready: %d event(s) per cycle, %.1fs interval, %s cycles.",
        len(pairs),
        interval,
        "∞" if max_cycles == 0 else str(max_cycles),
    )

    cycle = 0
    while True:
        cycle += 1
        for event in pairs:
            # Stamp current real-time for each yield
            event_with_realtime = dict(event)
            event_with_realtime["timestamp"] = datetime.now(timezone.utc).isoformat()
            event_with_realtime["cycle"] = cycle
            yield event_with_realtime
            time.sleep(interval)

        if max_cycles and cycle >= max_cycles:
            logger.info("Reached max_cycles=%d — stopping feed.", max_cycles)
            break


# ---------------------------------------------------------------------------
# Sample data initializer
# ---------------------------------------------------------------------------

def init_sample_data(data_dir: "str | Path" = TEST_DATA_DIR) -> None:
    """Create the test_data directory and a sample mock_tweets.json.

    This is a one-time setup helper that creates realistic demo data.
    Existing files are NOT overwritten.

    Args:
        data_dir: Directory where test data will be created.
    """
    directory = Path(data_dir)
    directory.mkdir(parents=True, exist_ok=True)

    tweets_path = directory / "mock_tweets.json"
    if not tweets_path.exists():
        sample_tweets = [
            {
                "tweet_text": "Look at this crazy goal! #soccer #WorldCup ⚽",
                "username": "@soccerfan99",
                "timestamp": "2026-04-08T06:00:00Z",
            },
            {
                "tweet_text": "Full match replay 🔴 LIVE #NFL #football — watch before it's taken down!",
                "username": "@nfl_leaks_2026",
                "timestamp": "2026-04-08T06:05:00Z",
            },
            {
                "tweet_text": "My reaction to the game-winning buzzer beater 😂 #NBA #basketball",
                "username": "@hoopsfan_real",
                "timestamp": "2026-04-08T06:10:00Z",
            },
            {
                "tweet_text": "LMAO this tennis meme is everything 🎾 #Wimbledon #meme",
                "username": "@memequeen",
                "timestamp": "2026-04-08T06:15:00Z",
            },
            {
                "tweet_text": "FULL BROADCAST of the Olympics 100m final — no commentary needed",
                "username": "@sports_pirate_xD",
                "timestamp": "2026-04-08T06:20:00Z",
            },
            {
                "tweet_text": "Analysis: Why this corner kick strategy changed the game #tactics",
                "username": "@coachingnerds",
                "timestamp": "2026-04-08T06:25:00Z",
            },
            {
                "tweet_text": "Streaming the F1 race RIGHT NOW — link in bio 🏎️ #F1 #GrandPrix",
                "username": "@f1_stream_free",
                "timestamp": "2026-04-08T06:30:00Z",
            },
            {
                "tweet_text": "When the ref makes THAT call 😤 (comedy clip) #hockey #NHL",
                "username": "@icehockeyhumor",
                "timestamp": "2026-04-08T06:35:00Z",
            },
        ]
        with open(tweets_path, "w", encoding="utf-8") as f:
            json.dump(sample_tweets, f, indent=2)
        logger.info("Created sample tweets file: %s", tweets_path)
    else:
        logger.info("Tweets file already exists, skipping: %s", tweets_path)

    # Create a README for test_data/
    readme_path = directory / "README.md"
    if not readme_path.exists():
        readme_path.write_text(
            "# test_data/\n\n"
            "This folder contains mock data for SportsGuard AI demos.\n\n"
            "## Contents\n"
            "- `mock_tweets.json` — Simulated social media post metadata\n"
            "- `*.mp4` / `*.mov` — Place test video clips here\n\n"
            "## Generating a synthetic test video\n"
            "```bash\n"
            "python fingerprint_engine.py\n"
            "```\n"
            "This will create `test_data/synthetic_test.mp4` automatically.\n",
            encoding="utf-8",
        )
        logger.info("Created test_data/README.md")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    if "--init" in sys.argv:
        print("Initializing sample test data...")
        init_sample_data()
        print("✅ Done. Check the test_data/ folder.")
        sys.exit(0)

    print("=" * 60)
    print("SportsGuard AI — Module D: Mock Scraper Demo")
    print("=" * 60)
    print(f"Streaming one event every {STREAM_INTERVAL_SECONDS}s  (Ctrl+C to stop)\n")

    # Auto-init sample data if not present
    if not MOCK_TWEETS_FILE.exists():
        logger.info("No mock data found — initializing sample data...")
        init_sample_data()

    try:
        for event in stream_feed(interval=STREAM_INTERVAL_SECONDS):
            print(f"[{event['timestamp']}]")
            print(f"  User   : {event['username']}")
            print(f"  Tweet  : {event['tweet_text']}")
            print(f"  Video  : {event.get('video_path') or '(no video file yet)'}")
            print(f"  Cycle  : {event['cycle']}")
            print()

    except KeyboardInterrupt:
        print("\n\nStream stopped by user.")
    except FileNotFoundError as e:
        print(f"\n[ERROR] {e}")
        print("Tip: run  python mock_scraper.py --init  to create sample data.")
