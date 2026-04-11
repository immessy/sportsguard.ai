# SportsGuard AI — Backend

> AI-powered sports content piracy detection and classification pipeline.

SportsGuard AI monitors social media feeds for unauthorised redistribution of sports broadcast content. It fingerprints official videos, matches suspect clips at high speed using a C++ Hamming-distance engine, and classifies detected usage via Google Gemini multimodal analysis.

---

## Architecture

```
┌──────────────┐    ┌─────────────────┐    ┌──────────────────┐
│  Flask API   │───▶│  Fingerprint    │───▶│  SQLite DB       │
│  (app.py)    │    │  Engine (A)     │    │  sportsguard.db  │
└──────┬───────┘    └─────────────────┘    └────────┬─────────┘
       │                                            │
       ▼                                            ▼
┌──────────────┐    ┌─────────────────┐    ┌──────────────────┐
│  Mock Scraper│───▶│  C++ Matcher    │───▶│  Gemini Analyzer │
│  (D)         │    │  (B) pybind11   │    │  (C)             │
└──────────────┘    └─────────────────┘    └──────────────────┘
```

## Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.9+ |
| C++ Compiler | MSVC 2019+ (Windows) / GCC 9+ (Linux) |
| OpenCV | 4.8+ |
| SQLite | 3.x (bundled with Python) |

## Installation

```bash
# 1. Clone the repository
git clone <repo-url> && cd sportsguard-backend

# 2. Create a virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Build the C++ matching engine (optional — pure-Python fallback exists)
python setup.py build_ext --inplace

# 5. Set up environment variables
copy .env.example .env
# Then edit .env with your Gemini API key

# 6. Initialise the database
python setup_database.py --seed
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_PATH` | `sportsguard.db` | SQLite database file path |
| `UPLOAD_FOLDER` | `uploads` | Directory for uploaded videos |
| `GEMINI_API_KEY` | — | Google Gemini API key |
| `FLASK_DEBUG` | `1` | Enable Flask debug mode |
| `PORT` | `5000` | API server port |

## Running the Application

```bash
# Start the Flask API server
python app.py

# Or use flask directly
flask --app app run --port 5000
```

## API Documentation

### `POST /api/upload`
Upload and fingerprint an official video.

**Request:** `multipart/form-data`
| Field | Type | Required |
|---|---|---|
| `video` | File (MP4/MOV) | ✓ |
| `title` | String | ✗ |

**Response (201):**
```json
{
  "video_id": 1,
  "status": "success",
  "total_frames": 120
}
```

---

### `GET /api/scan`
Pull next item from mock feed, match against database, classify.

**Response (200):**
```json
{
  "match_found": true,
  "video_id": 1,
  "confidence": 96.87,
  "classification": "Piracy",
  "risk_score": 92,
  "source_url": "https://twitter.com/user/status/tweet_90001",
  "tweet_text": "Full IPL match free download!",
  "platform": "Twitter",
  "detected_at": "2026-04-08T14:30:00Z",
  "detection_id": 5,
  "detection_time_s": 0.234
}
```

---

### `GET /api/dashboard/stats`
Aggregate statistics for the dashboard.

**Response (200):**
```json
{
  "total_videos_protected": 10,
  "total_detections": 47,
  "detections_today": 5,
  "high_risk_count": 12,
  "avg_confidence": 94.5
}
```

---

### `GET /api/detections?limit=50&offset=0`
Paginated list of all detections.

---

### `GET /api/videos`
List all protected official videos.

---

### `GET /api/health`
Health check endpoint.

## Testing

```bash
# Run all tests
pytest test_integration.py -v --tb=short

# Run a specific test class
pytest test_integration.py::TestMatchingEngine -v

# Run with timing info
pytest test_integration.py -v --durations=10
```

### Test categories
| Suite | What it tests |
|---|---|
| `TestFingerprinting` | Upload, storage, hash uniqueness, error handling |
| `TestMatchingEngine` | Identical/similar/different hashes, 10K benchmark |
| `TestGeminiAnalyzer` | Mocked API, graceful fallback |
| `TestFullPipeline` | E2E upload → detect → classify in <10 s |
| `TestAPIEndpoints` | Flask routes, status codes, response shapes |

### Success Criteria
- ✅ Detection + classification in **< 10 seconds**
- ✅ Matching accuracy **> 90%**
- ✅ System stability **100%** (no crashes)

## Project Structure

```
sportsguard-backend/
├── app.py                      # Flask REST API (Module E)
├── fingerprint_engine.py       # Video fingerprinting (Module A)
├── fast_matcher.cpp            # C++ Hamming matcher (Module B)
├── setup.py                    # C++ build configuration
├── gemini_analyzer.py          # Gemini multimodal classifier (Module C)
├── mock_scraper.py             # Mock social feed (Module D)
├── setup_database.py           # Database schema setup (Module F)
├── database_helpers.py         # Reusable DB query functions
├── test_integration.py         # Integration test suite (Module G)
├── conftest.py                 # Pytest fixtures
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variable template
├── README.md                   # This file
├── sportsguard.db              # SQLite database (created at runtime)
├── uploads/                    # Uploaded official videos
└── test_data/
    ├── videos/                 # Test video files
    └── metadata/               # Scenario JSON files
        ├── scenario_01_piracy.json
        ├── scenario_02_transformative.json
        └── scenario_03_meme.json
```

## Deployment Notes

1. **Database**: SQLite is suitable for single-server deployment. For multi-server, migrate to PostgreSQL.
2. **C++ Extension**: Pre-compile for your target platform. The pure-Python fallback works but is slower for large databases.
3. **Gemini API**: Set rate limits in production to avoid quota exhaustion.
4. **File Storage**: For production, use cloud storage (S3/GCS) instead of local `uploads/`.

## Troubleshooting

| Issue | Solution |
|---|---|
| `ModuleNotFoundError: fast_matcher` | Run `python setup.py build_ext --inplace` or the pure-Python fallback will be used automatically |
| `cv2` import error | `pip install opencv-python` |
| Gemini API timeout | Check your API key and network; the analyzer retries 3 times automatically |
| Database locked | Ensure only one write process at a time; WAL mode is enabled by default |
| Build fails on Windows | Install Visual Studio Build Tools with C++ workload |
