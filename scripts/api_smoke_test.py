from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import requests


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Smoke test the SportsGuard API using a real MP4 upload and live scan trigger."
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Base URL for the FastAPI backend.",
    )
    parser.add_argument(
        "--video",
        default="test_data/videos/official_match.mp4",
        help="Path to the official video to upload.",
    )
    parser.add_argument(
        "--poll-attempts",
        type=int,
        default=6,
        help="Number of times to poll /api/detections after starting a scan.",
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=5,
        help="Seconds between detection polls.",
    )
    return parser.parse_args()


def print_json(label: str, payload: object) -> None:
    print(f"\n=== {label} ===")
    print(json.dumps(payload, indent=2, default=str))


def main() -> int:
    args = parse_args()
    base_url = args.base_url.rstrip("/")
    video_path = Path(args.video)

    if not video_path.exists():
        print(f"Video file not found: {video_path}", file=sys.stderr)
        return 1

    try:
        health_response = requests.get(f"{base_url}/api/health", timeout=20)
        health_response.raise_for_status()
        print_json("Health", health_response.json())

        with video_path.open("rb") as video_file:
            upload_response = requests.post(
                f"{base_url}/api/upload",
                files={"file": (video_path.name, video_file, "video/mp4")},
                timeout=300,
            )
        upload_response.raise_for_status()
        print_json("Upload", upload_response.json())

        scan_response = requests.post(f"{base_url}/api/start-scan", timeout=30)
        scan_response.raise_for_status()
        print_json("Scan Trigger", scan_response.json())

        for attempt in range(1, args.poll_attempts + 1):
            detections_response = requests.get(f"{base_url}/api/detections", timeout=30)
            detections_response.raise_for_status()
            detections = detections_response.json()
            print_json(f"Detections Poll {attempt}", detections[:5])
            if detections:
                break
            time.sleep(args.poll_interval)

        return 0
    except requests.RequestException as exc:
        print(f"Smoke test failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
