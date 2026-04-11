"""Quick verification script — runs without a Gemini API key."""
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

print("=== SportsGuard AI — Member 2 Verification ===\n")

# --- Test 1: gemini_analyzer helpers ---
print("[1] Testing gemini_analyzer helpers...")
from gemini_analyzer import _create_demo_frame, pil_to_base64
frame = _create_demo_frame()
b64 = pil_to_base64(frame)
print(f"    Frame size : {frame.size}")
print(f"    Base64 len : {len(b64)}")
print("    [OK] gemini_analyzer helpers work\n")

# --- Test 2: fingerprint engine ---
print("[2] Testing fingerprint_engine...")
from fingerprint_engine import fingerprint_video
from pathlib import Path
import tempfile

# Auto-generate a test video if needed
test_video_path = "test_data/videos/official_clip.mp4"
if not Path(test_video_path).exists():
    print("    Generating test video...")
    from generate_test_videos import generate_official
    Path("test_data/videos").mkdir(parents=True, exist_ok=True)
    generate_official()

with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
    tmp_db = f.name

from setup_database import init_database
init_database(tmp_db)
vid_id = fingerprint_video(test_video_path, "Verify Test", tmp_db)
print(f"    Fingerprinted video_id: {vid_id}")
print("    [OK] fingerprint_engine works\n")

# --- Test 3: mock_scraper ---
print("[3] Testing mock_scraper...")
from mock_scraper import simulate_feed
events = []
for video_path, metadata in simulate_feed("test_data", min_delay=0, max_delay=0, loop=False):
    events.append(metadata)
    if len(events) >= 3:
        break
for e in events:
    print(f"    @{e.get('user', '?')}: {e.get('text', '')[:50]}")
print(f"    Total events in feed: {len(events)}")
print("    [OK] mock_scraper works\n")

print("=== All tests passed! ===")
print("\nNext: Set GEMINI_API_KEY and run: python gemini_analyzer.py")
