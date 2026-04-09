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
from fingerprint_engine import extract_fingerprints, save_fingerprints, load_fingerprints
fps = extract_fingerprints("test_data/synthetic_test.mp4", fps_target=1)
print(f"    Fingerprints extracted: {len(fps)}")
for idx, h in fps:
    print(f"    Frame {idx:5d}: {h}")
saved = save_fingerprints("verify_test", fps)
loaded = load_fingerprints("verify_test")
assert len(loaded) == len(fps), "Mismatch in saved vs loaded fingerprints!"
print(f"    Saved & reloaded: {len(loaded)} fingerprints")
print("    [OK] fingerprint_engine works\n")

# --- Test 3: mock_scraper ---
print("[3] Testing mock_scraper...")
from mock_scraper import init_sample_data, stream_feed
init_sample_data()
events = []
for event in stream_feed(interval=0, max_cycles=1):
    events.append(event)
    if len(events) >= 3:
        break
for e in events:
    print(f"    {e['username']}: {e['tweet_text'][:50]}")
print(f"    Total events in feed: {len(events)}")
print("    [OK] mock_scraper works\n")

print("=== All tests passed! ===")
print("\nNext: Set GEMINI_API_KEY and run: python gemini_analyzer.py")
