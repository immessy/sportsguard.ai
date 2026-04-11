#!/usr/bin/env python3
"""
SportsGuard AI — Gemini Accuracy & Performance Benchmark
Measures classification accuracy and response time against TDD targets.

Targets:
    - Classification accuracy > 90%
    - Gemini avg response time < 5s
    - Fingerprinting speed < 2s for 30s video
    - Full pipeline < 10s

Usage:
    python benchmark_gemini.py                    # Full benchmark (needs API key)
    python benchmark_gemini.py --no-gemini        # Fingerprinting only (no API key)
    python benchmark_gemini.py --api-key YOUR_KEY # Explicit key
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import cv2
import imagehash
import numpy as np
from PIL import Image

# ── Project imports ───────────────────────────────────────────────────────
from fingerprint_engine import fingerprint_video
from gemini_analyzer import analyze_content
from setup_database import init_database

# ---------------------------------------------------------------------------
# Test data
# ---------------------------------------------------------------------------

VIDEOS_DIR = Path("test_data/videos")
TWEETS_FILE = Path("test_data/mock_tweets.json")

# Classification benchmarks — labeled test cases
BENCHMARK_CASES = [
    {
        "video": "piracy_clip.mp4",
        "context": "🔥 FULL IPL 2026 Final — MI vs CSK! Watch FREE in HD, no ads! #FreeStream",
        "expected": "Piracy",
        "min_risk": 70,
    },
    {
        "video": "piracy_clip.mp4",
        "context": "Streaming full match replay LIVE — watch before it's taken down! DM for link",
        "expected": "Piracy",
        "min_risk": 70,
    },
    {
        "video": "transformative_clip.mp4",
        "context": "Bumrah's yorker sequence — full tactical analysis with slow-mo breakdown 📊🏏",
        "expected": "Transformative",
        "max_risk": 55,
    },
    {
        "video": "transformative_clip.mp4",
        "context": "Breakdown of Virat's cover drive technique. Educational content #CricketCoaching",
        "expected": "Transformative",
        "max_risk": 55,
    },
    {
        "video": "meme_clip.mp4",
        "context": "POV: Dhoni walks in at 160/5 😤🔥 #ThalaForAReason #CricketMeme",
        "expected": "Meme",
        "max_risk": 35,
    },
    {
        "video": "meme_clip.mp4",
        "context": "LMAO this tennis meme is everything 🎾 When the ref says OUT 😂 #meme",
        "expected": "Meme",
        "max_risk": 35,
    },
    {
        "video": "official_clip.mp4",
        "context": "FULL BROADCAST of the cricket final — raw feed, HD quality, no commentary",
        "expected": "Piracy",
        "min_risk": 65,
    },
    {
        "video": "official_clip.mp4",
        "context": "Analysis: Why this bowling strategy changed the game — with overlays #tactics",
        "expected": "Transformative",
        "max_risk": 55,
    },
    {
        "video": "meme_clip.mp4",
        "context": "Me watching my team lose AGAIN 😭💀 #MondayVibes #SportsMemes",
        "expected": "Meme",
        "max_risk": 35,
    },
    {
        "video": "piracy_clip.mp4",
        "context": "Streaming the F1 race RIGHT NOW — link in bio 🏎️ #F1 #FreeStream",
        "expected": "Piracy",
        "min_risk": 65,
    },
]


# ---------------------------------------------------------------------------
# Benchmark functions
# ---------------------------------------------------------------------------

def benchmark_fingerprinting():
    """Measure fingerprinting speed — target: <2s for each test video."""
    print("\n" + "=" * 60)
    print("  FINGERPRINTING SPEED BENCHMARK")
    print("=" * 60)

    db_path = "benchmark_temp.db"
    init_database(db_path, reset=True)

    results = []
    for video_name in ["official_clip.mp4", "piracy_clip.mp4",
                       "transformative_clip.mp4", "meme_clip.mp4"]:
        video_path = str(VIDEOS_DIR / video_name)
        if not os.path.isfile(video_path):
            print(f"  [SKIP] Video not found: {video_path}")
            continue

        t0 = time.perf_counter()
        vid_id = fingerprint_video(video_path, video_name, db_path)
        elapsed = time.perf_counter() - t0

        status = "✓ PASS" if elapsed < 2.0 else "✗ FAIL"
        results.append({"video": video_name, "time_s": elapsed, "passed": elapsed < 2.0})
        print(f"  {status}  {video_name}: {elapsed:.3f}s (target <2s)")

    # Cleanup
    try:
        os.remove(db_path)
        for suffix in ["-wal", "-shm"]:
            p = db_path + suffix
            if os.path.exists(p):
                os.remove(p)
    except OSError:
        pass

    return results


def benchmark_matching():
    """Measure matching speed — target: 10K comparisons in <1s."""
    print("\n" + "=" * 60)
    print("  MATCHING SPEED BENCHMARK")
    print("=" * 60)

    import random
    rng = random.Random(42)
    q = 0xABCDEF0123456789
    db_hashes = [(rng.getrandbits(64), i) for i in range(10_000)]

    t0 = time.perf_counter()
    best_dist = 65
    best_vid = -1
    for h, vid in db_hashes:
        d = bin(q ^ h).count("1")
        if d < best_dist:
            best_dist = d
            best_vid = vid
    elapsed = time.perf_counter() - t0

    status = "✓ PASS" if elapsed < 1.0 else "✗ FAIL"
    print(f"  {status}  10K hash comparisons: {elapsed:.4f}s (target <1s)")
    return {"comparisons": 10_000, "time_s": elapsed, "passed": elapsed < 1.0}


def benchmark_gemini_accuracy(api_key: str = None):
    """Measure Gemini classification accuracy — target: >90%."""
    print("\n" + "=" * 60)
    print("  GEMINI CLASSIFICATION ACCURACY BENCHMARK")
    print("=" * 60)

    api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("  [SKIP] No GEMINI_API_KEY set. Cannot test accuracy.")
        print("         Set env var: $env:GEMINI_API_KEY = 'your_key'")
        return None

    results = []
    total_time = 0

    for i, case in enumerate(BENCHMARK_CASES):
        video_path = str(VIDEOS_DIR / case["video"])
        if not os.path.isfile(video_path):
            print(f"  [SKIP] Video not found: {video_path}")
            continue

        # Extract first frame
        cap = cv2.VideoCapture(video_path)
        ret, frame = cap.read()
        cap.release()
        if not ret:
            print(f"  [SKIP] Cannot read: {case['video']}")
            continue

        pil_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        t0 = time.perf_counter()
        result = analyze_content(pil_img, case["context"], api_key=api_key,
                                 max_retries=2, timeout=15.0)
        elapsed = time.perf_counter() - t0
        total_time += elapsed

        correct = result["classification"] == case["expected"]

        results.append({
            "case": i + 1,
            "context": case["context"][:50] + "...",
            "expected": case["expected"],
            "got": result["classification"],
            "risk_score": result["risk_score"],
            "correct": correct,
            "time_s": elapsed,
        })

        status = "✓" if correct else "✗"
        print(f"  {status} Case {i+1}: expected={case['expected']}, "
              f"got={result['classification']} (risk={result['risk_score']}, "
              f"{elapsed:.1f}s)")

    if not results:
        return None

    # Summary
    correct_count = sum(r["correct"] for r in results)
    accuracy = correct_count / len(results) * 100
    avg_time = total_time / len(results)

    print(f"\n  {'─' * 50}")
    print(f"  Accuracy     : {accuracy:.1f}% ({correct_count}/{len(results)})")
    print(f"  Avg response : {avg_time:.2f}s")
    print(f"  Total time   : {total_time:.2f}s")

    acc_status = "✓ PASS" if accuracy >= 90.0 else "✗ FAIL"
    time_status = "✓ PASS" if avg_time < 5.0 else "✗ FAIL"
    print(f"\n  {acc_status}  Accuracy target: >90% (got {accuracy:.1f}%)")
    print(f"  {time_status}  Speed target: <5s avg (got {avg_time:.2f}s)")

    return {
        "accuracy": accuracy,
        "avg_time_s": avg_time,
        "total_cases": len(results),
        "correct": correct_count,
        "results": results,
    }


def print_final_report(fp_results, match_result, gemini_results):
    """Print comprehensive TDD compliance report."""
    print("\n" + "═" * 60)
    print("  SPORTSGUARD AI — TDD COMPLIANCE REPORT")
    print("═" * 60)

    all_pass = True

    # Fingerprinting
    fp_pass = all(r["passed"] for r in fp_results) if fp_results else False
    fp_time = max(r["time_s"] for r in fp_results) if fp_results else 0
    status = "✓" if fp_pass else "✗"
    print(f"  {status}  Fingerprinting < 2s       : {fp_time:.3f}s")
    all_pass = all_pass and fp_pass

    # Matching
    m_pass = match_result["passed"]
    status = "✓" if m_pass else "✗"
    print(f"  {status}  10K matches < 1s          : {match_result['time_s']:.4f}s")
    all_pass = all_pass and m_pass

    # Gemini
    if gemini_results:
        g_acc = gemini_results["accuracy"] >= 90.0
        g_speed = gemini_results["avg_time_s"] < 5.0
        status_acc = "✓" if g_acc else "✗"
        status_spd = "✓" if g_speed else "✗"
        print(f"  {status_acc}  Gemini accuracy > 90%     : {gemini_results['accuracy']:.1f}%")
        print(f"  {status_spd}  Gemini avg response < 5s  : {gemini_results['avg_time_s']:.2f}s")
        all_pass = all_pass and g_acc and g_speed
    else:
        print(f"  ⊘  Gemini accuracy          : SKIPPED (no API key)")
        print(f"  ⊘  Gemini response time     : SKIPPED (no API key)")

    print(f"\n  {'═' * 52}")
    overall = "✓ ALL TARGETS MET" if all_pass else "✗ SOME TARGETS MISSED"
    if not gemini_results:
        overall += " (Gemini skipped)"
    print(f"  {overall}")
    print("═" * 60)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="SportsGuard AI — Benchmark Suite")
    parser.add_argument("--api-key", default=None, help="Gemini API key")
    parser.add_argument("--no-gemini", action="store_true",
                        help="Skip Gemini tests (fingerprint + matching only)")
    args = parser.parse_args()

    print("=" * 60)
    print("  SportsGuard AI — Performance & Accuracy Benchmark")
    print("=" * 60)

    # Check videos exist
    if not VIDEOS_DIR.exists() or not list(VIDEOS_DIR.glob("*.mp4")):
        print("\n  Test videos not found. Generating...")
        from generate_test_videos import main as gen_main
        gen_main()

    # Run benchmarks
    fp_results = benchmark_fingerprinting()
    match_result = benchmark_matching()

    gemini_results = None
    if not args.no_gemini:
        gemini_results = benchmark_gemini_accuracy(args.api_key)

    # Final report
    print_final_report(fp_results, match_result, gemini_results)


if __name__ == "__main__":
    main()
