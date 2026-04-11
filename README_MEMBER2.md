# SportsGuard AI — Member 2 Guide
### AI & Data Specialist: Video Fingerprinting · Gemini AI · Mock Data Simulation

> **Google Solution Challenge 2026** | Member 2 Deliverables

---

## 📁 File Structure

```
sportsguard.ai/
├── app.py                  # Module E  — Flask REST API (Backend)
├── gemini_analyzer.py      # Module C  — Gemini 2.0 Flash piracy classifier
├── fingerprint_engine.py   # Module A  — Video perceptual hash fingerprinting
├── mock_scraper.py         # Module D  — Live feed simulation
├── fast_matcher.cpp        # Module B  — C++ Hamming distance matcher
├── setup_database.py       # Module F  — SQLite schema setup
├── database_helpers.py     # Module F  — Database query helpers
├── conftest.py             # Shared pytest fixtures
├── test_integration.py     # Module G  — Integration test suite (21 tests)
├── test_e2e_member2.py     # E2E pipeline tests (13 tests)
├── benchmark_gemini.py     # TDD performance & accuracy benchmark
├── generate_test_videos.py # Synthetic test video generator
├── requirements.txt        # All Python dependencies
├── .env.example            # Environment variable template
└── test_data/
    ├── mock_tweets.json    # 10 labeled tweet scenarios
    ├── metadata/           # Per-scenario JSON configs
    │   ├── scenario_01_piracy.json
    │   ├── scenario_02_transformative.json
    │   └── scenario_03_meme.json
    └── videos/             # Generated test videos (run generate_test_videos.py)
        ├── official_clip.mp4
        ├── piracy_clip.mp4
        ├── transformative_clip.mp4
        └── meme_clip.mp4
```

---

## ⚙️ Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set your Gemini API key

Get a **free** key at **https://aistudio.google.com/app/apikey** (Google AI Studio — no billing required).

```bash
# Windows PowerShell
$env:GEMINI_API_KEY = "your_key_here"

# Linux / macOS
export GEMINI_API_KEY="your_key_here"
```

### 3. Initialize database & generate test videos

```bash
python setup_database.py --seed
python generate_test_videos.py
```

---

## 🚀 Running the Full System

### Start the Flask API
```bash
python app.py
# API runs on http://localhost:5000
```

### Run all tests (34 total)
```bash
python -m pytest test_integration.py test_e2e_member2.py -v
```

### Run performance benchmark
```bash
python benchmark_gemini.py              # Full (needs API key)
python benchmark_gemini.py --no-gemini  # Fingerprinting + matching only
```

---

## 🎬 Demo Scenarios

### Scenario 1: Piracy Detection
1. Upload official clip: `POST /api/upload` with `test_data/videos/official_clip.mp4`
2. Mock scraper feeds piracy version from `test_data/videos/piracy_clip.mp4`
3. Fingerprint matcher flags similarity
4. Gemini classifies: **"Piracy"** (risk: 85+)
5. Detection stored in database with DMCA metadata

### Scenario 2: False Positive Prevention (Transformative)
1. Mock scraper feeds analysis clip (`transformative_clip.mp4`)
2. System detects visual similarity to official content
3. Gemini classifies: **"Transformative"** (risk: 25-45)
4. No takedown issued — fair use detected ✅

### Scenario 3: Meme — Fair Use
1. Mock scraper feeds meme clip (`meme_clip.mp4`)
2. Visual style diverges from official (low match score)
3. Gemini classifies: **"Meme"** (risk: 5-25)
4. No action taken ✅

---

## 📊 Performance Metrics (TDD Compliance)

| Metric | Target | Actual | Status |
|--------|--------|--------|:------:|
| Full pipeline time | <10s | 2.35s | ✅ |
| Fingerprinting speed | <2s/video | 0.24s | ✅ |
| 10K hash matching | <1s | 0.005s | ✅ |
| Gemini avg response | <5s | ~2s* | ✅ |
| Integration tests | 100% pass | 21/21 | ✅ |
| E2E tests | 100% pass | 13/13 | ✅ |
| System stability | 100% | 100% | ✅ |

*Gemini response time varies with API load. Tested with `gemini-2.0-flash`.

---

## 🔗 Module C — Gemini Analyzer (`gemini_analyzer.py`)

**Purpose:** Classifies a video frame + tweet text as `Piracy`, `Transformative`, or `Meme`.

**SDK:** Uses `google-genai` (current SDK) with `genai.Client()` and structured JSON output.

```python
from gemini_analyzer import analyze_content
from PIL import Image

frame = Image.open("frame.jpg")
result = analyze_content(frame, "Full IPL match free download!")
# {'classification': 'Piracy', 'risk_score': 92, 'reasoning': '...'}
```

Also supports backward-compatible `analyze_frame()`:
```python
from gemini_analyzer import analyze_frame
result = analyze_frame(frame, "Check out this insane dunk! #NBA")
```

---

## 🔗 Module A — Fingerprint Engine (`fingerprint_engine.py`)

**Purpose:** Extracts perceptual hash fingerprints from a video at 1 FPS and stores them in SQLite.

```bash
python fingerprint_engine.py path/to/video.mp4 "Video Title"
```

```python
from fingerprint_engine import fingerprint_video
vid_id = fingerprint_video("clip.mp4", "IPL Highlights", "sportsguard.db")
```

---

## 🔗 Module D — Mock Scraper (`mock_scraper.py`)

**Purpose:** Simulates a live social-media feed for real-time demo.

```python
from mock_scraper import simulate_feed
for video_path, metadata in simulate_feed(loop=False):
    print(metadata["user"], metadata["text"])
```

---

## 🧪 Testing

### Run integration tests (backend)
```bash
python -m pytest test_integration.py -v --tb=short
```

### Run E2E tests (Member 2)
```bash
python -m pytest test_e2e_member2.py -v --tb=short
```

### Run all tests
```bash
python -m pytest test_integration.py test_e2e_member2.py -v
# Expected: 34 passed
```

### Generate test report
```bash
python benchmark_gemini.py
```

---

## 🐞 Troubleshooting

| Error | Solution |
|-------|----------|
| `No Gemini API key` | Set `GEMINI_API_KEY` env var (see Setup above) |
| `google-genai` import error | Run `pip install google-genai` |
| `FileNotFoundError: metadata` | Run `python generate_test_videos.py` |
| Windows encoding errors | Set `$env:PYTHONIOENCODING="utf-8"` |
| `fast_matcher` not found | Expected — pure-Python fallback is used automatically |

---

## 📋 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/upload` | Upload & fingerprint an official video |
| GET | `/api/scan` | Scan mock feed for piracy |
| GET | `/api/dashboard/stats` | Aggregate dashboard statistics |
| GET | `/api/detections` | List detections (paginated) |
| GET | `/api/videos` | List protected videos |
| GET | `/api/health` | Health check |

---

## 📋 API Key Note

This project uses **Google AI Studio** (not GCP Console).
- URL: https://aistudio.google.com/app/apikey
- **Free tier** includes Gemini 2.0 Flash — no billing needed
- Model used: `gemini-2.0-flash`

---

*SportsGuard AI — Google Solution Challenge 2026*
