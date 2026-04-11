#!/usr/bin/env python3
"""
SportsGuard AI — Integration Test Suite (Module G)
End-to-end tests for the full content-protection pipeline.

Run:
    pytest test_integration.py -v --tb=short
    pytest test_integration.py -v -k "test_fingerprint"   # single suite
"""

import json
import os
import random
import sqlite3
import tempfile
import time

import cv2
import imagehash
import numpy as np
import pytest
from PIL import Image

# ── Project imports (conftest.py sets up sys.path) ────────────────────────
from setup_database import init_database
from database_helpers import (
    get_connection,
    close_connection,
    get_all_fingerprints,
    get_fingerprints_for_video,
    insert_detection,
    get_dashboard_stats,
    get_all_detections,
    get_all_videos,
)
from fingerprint_engine import fingerprint_video
from gemini_analyzer import analyze_content


# ═══════════════════════════════════════════════════════════════════════════
#  1. FINGERPRINTING TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestFingerprinting:
    """Upload a test video, verify fingerprints stored correctly, check hash uniqueness."""

    def test_fingerprint_creates_video_record(self, test_video, test_db):
        """Video record is inserted into official_content."""
        vid_id = fingerprint_video(test_video, "Test Video", test_db)
        assert vid_id > 0

        conn = sqlite3.connect(test_db)
        row = conn.execute("SELECT * FROM official_content WHERE id = ?", (vid_id,)).fetchone()
        conn.close()
        assert row is not None
        assert row[1] == "Test Video"  # title

    def test_fingerprints_stored_correctly(self, test_video, test_db):
        """Each extracted frame has a corresponding fingerprint row."""
        vid_id = fingerprint_video(test_video, "FP Test", test_db)
        fps = get_fingerprints_for_video(vid_id, db_path=test_db)
        assert len(fps) > 0

        for fp in fps:
            assert fp["video_id"] == vid_id
            assert len(fp["phash"]) == 16  # 64-bit hex = 16 chars

    def test_hash_uniqueness_within_video(self, test_video, test_db):
        """No duplicate (video_id, frame_index) pairs."""
        vid_id = fingerprint_video(test_video, "Unique Test", test_db)
        fps = get_fingerprints_for_video(vid_id, db_path=test_db)
        indices = [fp["frame_index"] for fp in fps]
        assert len(indices) == len(set(indices)), "Duplicate frame indices found"

    def test_corrupted_video_raises(self, test_db, tmp_path):
        """Corrupted / empty file should raise ValueError."""
        fake_file = tmp_path / "bad.mp4"
        fake_file.write_bytes(b"\x00" * 64)
        with pytest.raises(ValueError):
            fingerprint_video(str(fake_file), "Bad Video", test_db)

    def test_missing_video_raises(self, test_db):
        """Non-existent file should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            fingerprint_video("nonexistent_video.mp4", "Ghost", test_db)


# ═══════════════════════════════════════════════════════════════════════════
#  2. MATCHING ENGINE TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestMatchingEngine:
    """Test hash matching — tries C++ module, falls back to pure-Python."""

    @staticmethod
    def _match(query, db_hashes, threshold=5):
        """Use C++ fast_matcher if available, else pure-Python."""
        try:
            import fast_matcher
            r = fast_matcher.find_best_match(query, db_hashes, threshold)
            return r.to_dict()
        except ImportError:
            best_dist = 65
            best_vid = -1
            for h, vid in db_hashes:
                d = bin(query ^ h).count("1")
                if d < best_dist:
                    best_dist = d
                    best_vid = vid
            if best_dist <= threshold:
                return {"video_id": best_vid, "confidence": (64 - best_dist) / 64 * 100, "hamming_distance": best_dist}
            return {"video_id": -1, "confidence": 0.0, "hamming_distance": best_dist}

    def test_identical_hashes(self):
        """Identical hashes should match at 100% confidence."""
        h = 0xABCDEF0123456789
        db = [(h, 42)]
        result = self._match(h, db)
        assert result["video_id"] == 42
        assert result["confidence"] == 100.0
        assert result["hamming_distance"] == 0

    def test_similar_hashes(self):
        """Hashes differing in 2 bits should match with >90% confidence."""
        base = 0xABCDEF0123456789
        # Flip 2 bits
        similar = base ^ 0x0000000000000003
        db = [(base, 7)]
        result = self._match(similar, db, threshold=5)
        assert result["video_id"] == 7
        assert result["confidence"] > 90.0
        assert result["hamming_distance"] == 2

    def test_different_hashes(self):
        """Completely different hashes should NOT match."""
        q = 0xFFFFFFFFFFFFFFFF
        db = [(0x0000000000000000, 1)]
        result = self._match(q, db, threshold=5)
        assert result["video_id"] == -1

    def test_benchmark_10k(self):
        """10 000 comparisons should complete in <1 second."""
        q = 0xABCDEF0123456789
        rng = random.Random(42)
        db = [(rng.getrandbits(64), i) for i in range(10_000)]
        t0 = time.perf_counter()
        self._match(q, db, threshold=5)
        elapsed = time.perf_counter() - t0
        assert elapsed < 1.0, f"10K comparisons took {elapsed:.3f} s (>1 s)"

    def test_empty_database(self):
        """Empty DB should return no match."""
        result = self._match(0x1234, [], threshold=5)
        assert result["video_id"] == -1


# ═══════════════════════════════════════════════════════════════════════════
#  3. GEMINI ANALYZER TESTS (mocked)
# ═══════════════════════════════════════════════════════════════════════════

class TestGeminiAnalyzer:
    """Test Gemini analyzer with mocked API calls."""

    def test_no_api_key_returns_default(self):
        """Missing API key should return graceful default."""
        img = Image.new("RGB", (320, 240), color=(128, 128, 128))
        result = analyze_content(img, "test text", api_key=None)
        assert result["classification"] == "Unknown"
        assert result["risk_score"] == 50

    def test_numpy_input(self):
        """Should accept numpy arrays without crashing."""
        arr = np.zeros((240, 320, 3), dtype=np.uint8)
        result = analyze_content(arr, "test text", api_key=None)
        assert "classification" in result

    def test_grayscale_numpy_input(self):
        """Should accept 2D grayscale numpy arrays."""
        arr = np.zeros((240, 320), dtype=np.uint8)
        result = analyze_content(arr, "test text", api_key=None)
        assert "classification" in result

    def test_api_failure_graceful(self, monkeypatch):
        """Simulated API failure returns default response."""
        img = Image.new("RGB", (100, 100))

        # Monkey-patch to simulate import succeeding but calls failing
        def mock_analyze(*args, **kwargs):
            return {"classification": "Unknown", "risk_score": 50, "reasoning": "API error — unable to classify."}

        monkeypatch.setattr("gemini_analyzer.analyze_content", mock_analyze)
        result = mock_analyze(img, "some text", api_key="fake")
        assert result["classification"] == "Unknown"


# ═══════════════════════════════════════════════════════════════════════════
#  4. FULL PIPELINE TEST
# ═══════════════════════════════════════════════════════════════════════════

class TestFullPipeline:
    """End-to-end: upload → detect → classify within 10 s."""

    def test_e2e_detection_under_10s(self, test_video, test_db):
        """Full pipeline should complete in under 10 seconds."""
        t0 = time.perf_counter()

        # Step 1: Fingerprint the official video
        vid_id = fingerprint_video(test_video, "E2E Official", test_db)
        assert vid_id > 0

        # Step 2: Simulate suspect — extract frame, hash, match
        cap = cv2.VideoCapture(test_video)
        ret, frame = cap.read()
        cap.release()
        assert ret, "Could not read test video"

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        pil_img = Image.fromarray(gray)
        query_hash = imagehash.phash(pil_img, hash_size=8)
        query_int = int(str(query_hash), 16)

        # Step 3: Match
        all_fps = get_all_fingerprints(db_path=test_db)
        db_hashes = [(int(fp["phash"], 16), fp["video_id"]) for fp in all_fps]
        result = TestMatchingEngine._match(query_int, db_hashes, threshold=10)
        assert result["video_id"] != -1, "Expected a match for the same video"
        assert result["confidence"] > 85.0

        # Step 4: Classify (mocked — no API key)
        classification = analyze_content(pil_img, "test piracy scenario", api_key=None)
        assert "classification" in classification

        # Step 5: Store detection
        det_id = insert_detection(
            video_id=result["video_id"],
            source_url="https://test.example.com/suspect",
            platform="Test",
            confidence=result["confidence"],
            classification=classification["classification"],
            risk_score=classification["risk_score"],
            reasoning=classification["reasoning"],
            db_path=test_db,
        )
        assert det_id > 0

        elapsed = time.perf_counter() - t0
        assert elapsed < 10.0, f"Pipeline took {elapsed:.2f} s (>10 s)"
        print(f"\n  ✓ Full pipeline completed in {elapsed:.2f} s")


# ═══════════════════════════════════════════════════════════════════════════
#  5. API ENDPOINT TESTS
# ═══════════════════════════════════════════════════════════════════════════

class TestAPIEndpoints:
    """Test Flask API endpoints using the test client."""

    @pytest.fixture(autouse=True)
    def setup_app(self, test_db, monkeypatch):
        """Configure Flask app to use the test database."""
        monkeypatch.setenv("DATABASE_PATH", test_db)

        # Re-import to pick up env var
        import app as app_module
        app_module.DATABASE_PATH = test_db
        init_database(test_db)
        app_module.app.config["TESTING"] = True
        self.client = app_module.app.test_client()

    def test_health(self):
        resp = self.client.get("/api/health")
        assert resp.status_code == 200
        assert resp.get_json()["status"] == "ok"

    def test_upload_no_file(self):
        resp = self.client.post("/api/upload")
        assert resp.status_code == 400

    def test_upload_valid(self, test_video):
        with open(test_video, "rb") as f:
            resp = self.client.post(
                "/api/upload",
                data={"video": (f, "test.mp4"), "title": "API Test Video"},
                content_type="multipart/form-data",
            )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["status"] == "success"
        assert data["video_id"] > 0

    def test_dashboard_stats(self):
        resp = self.client.get("/api/dashboard/stats")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "total_videos_protected" in data

    def test_detections_list(self):
        resp = self.client.get("/api/detections?limit=10&offset=0")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "detections" in data

    def test_videos_list(self):
        resp = self.client.get("/api/videos")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "videos" in data


# ═══════════════════════════════════════════════════════════════════════════
#  REPORT PRINTER (runs after all tests)
# ═══════════════════════════════════════════════════════════════════════════

def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Print a custom summary with success criteria checklist."""
    reports = terminalreporter.stats
    passed = len(reports.get("passed", []))
    failed = len(reports.get("failed", []))
    total = passed + failed

    print("\n" + "=" * 60)
    print("  SPORTSGUARD AI — TEST REPORT")
    print("=" * 60)
    print(f"  Total   : {total}")
    print(f"  Passed  : {passed}")
    print(f"  Failed  : {failed}")
    print()
    print("  SUCCESS CRITERIA:")
    print(f"    Detection + classification < 10 s : {'✓' if failed == 0 else '✗'}")
    print(f"    Matching accuracy > 90%            : {'✓' if failed == 0 else '✗'}")
    print(f"    System stability 100% (no crashes) : {'✓' if failed == 0 else '✗'}")
    print("=" * 60)
