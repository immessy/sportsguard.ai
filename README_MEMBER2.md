# SportsGuard AI — Member 2 Guide
### AI & Data Specialist: Video Fingerprinting · Gemini AI · Mock Data Simulation

> **Google Solution Challenge 2026** | Member 2 Deliverables

---

## 📁 File Structure

```
sportsguard.ai/
├── gemini_analyzer.py      # Module C  — Gemini 2.0 Flash piracy classifier
├── fingerprint_engine.py   # Module A  — Video perceptual hash fingerprinting
├── mock_scraper.py         # Module D  — Live feed simulation
├── requirements.txt        # All Python dependencies
├── sportsguard.db          # SQLite DB (auto-created on first run)
└── test_data/
    ├── mock_tweets.json    # 10 sample tweet posts (Piracy / Meme / Transformative)
    └── README.md
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

---

## 🚀 Running Each Module Independently

### Module C — Gemini Analyzer (`gemini_analyzer.py`)

**Purpose:** Classifies a video frame + tweet text as `Piracy`, `Transformative`, or `Meme`.

```bash
python gemini_analyzer.py
```

**What happens:**
- Creates a synthetic 640×360 "sports broadcast" frame
- Sends it to Gemini 2.0 Flash with text: `"Look at this crazy goal! #soccer #WorldCup"`
- Prints JSON result with `classification`, `risk_score`, `reasoning`

**Expected output (example):**
```json
{
  "classification": "Transformative",
  "risk_score": 35,
  "reasoning": "Short highlight clip with fan caption; adds context."
}
```

**Import usage:**
```python
from gemini_analyzer import analyze_frame
from PIL import Image

frame = Image.open("my_frame.jpg")
result = analyze_frame(frame, "Check out this insane dunk! #NBA")
print(result)  # {'classification': 'Transformative', 'risk_score': 40, 'reasoning': '...'}
```

---

### Module A — Fingerprint Engine (`fingerprint_engine.py`)

**Purpose:** Extracts perceptual hash fingerprints from a video at 1 FPS and stores them in SQLite.

```bash
# Auto-generate a synthetic test video and fingerprint it
python fingerprint_engine.py

# Fingerprint your own video
python fingerprint_engine.py path/to/match_clip.mp4
```

**What happens:**
- Opens the video with OpenCV
- Extracts 1 frame per second
- Converts each frame to grayscale
- Computes 8×8 pHash (64-bit hex string)
- Saves all hashes to `sportsguard.db`

**Expected output:**
```
✅ Extracted 3 fingerprints:
  Frame     0: f8e4b2a107c39d1e
  Frame    10: f8e4b0a103c39d1e
  Frame    20: f8e4b2a10fc39d1f
✅ Saved 3 fingerprints to 'sportsguard.db'
✅ Reloaded 3 fingerprints from DB — OK
```

**Import usage:**
```python
from fingerprint_engine import extract_fingerprints, save_fingerprints

fps = extract_fingerprints("match.mp4", fps_target=1)
save_fingerprints("match_video_001", fps)
# each entry: (frame_index: int, phash_hex: str)
```

---

### Module D — Mock Scraper (`mock_scraper.py`)

**Purpose:** Simulates a live Twitter video feed for real-time demo.

```bash
# Start streaming (Ctrl+C to stop)
python mock_scraper.py

# Initialize only sample data (no streaming)
python mock_scraper.py --init
```

**What happens:**
- Reads `test_data/mock_tweets.json`
- Scans `test_data/` for any `.mp4` / `.mov` files
- Yields one combined event every 5 seconds in an infinite loop

**Expected output:**
```
[2026-04-08T12:00:05+00:00]
  👤 @soccerfan99
  🐦 Look at this crazy goal! #soccer #WorldCup ⚽
  🎥 video: test_data/synthetic_test.mp4
  🔄 cycle: 1
```

**Import usage:**
```python
from mock_scraper import stream_feed

for event in stream_feed(interval=5.0, max_cycles=1):
    print(event)
    # {
    #   "video_path": "test_data/match.mp4",
    #   "tweet_text": "...",
    #   "username": "@user",
    #   "timestamp": "2026-04-08T12:00:05+00:00",
    #   "cycle": 1
    # }
```

---

## 🔗 Connecting All Three Modules

For a full end-to-end pipeline demo:

```python
from mock_scraper import stream_feed
from fingerprint_engine import extract_fingerprints
from gemini_analyzer import analyze_frame
from PIL import Image
import cv2

for event in stream_feed(max_cycles=1):
    video_path = event["video_path"]
    tweet = event["tweet_text"]

    if video_path:
        # Step 1: Fingerprint the video
        fingerprints = extract_fingerprints(video_path)
        print(f"Fingerprints: {len(fingerprints)} frames indexed")

        # Step 2: Extract first frame for Gemini analysis
        cap = cv2.VideoCapture(video_path)
        ret, frame_bgr = cap.read()
        cap.release()

        if ret:
            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            pil_frame = Image.fromarray(frame_rgb)

            # Step 3: Classify with Gemini
            result = analyze_frame(pil_frame, tweet)
            print(f"Classification: {result}")
```

---

## 🧪 Testing Without a Real Video

Both `fingerprint_engine.py` and `mock_scraper.py` can generate synthetic data:

```bash
# Creates test_data/synthetic_test.mp4 automatically
python fingerprint_engine.py

# Then run the mock scraper — it will pick it up
python mock_scraper.py
```

---

## 🐞 Troubleshooting

| Error | Solution |
|-------|----------|
| `EnvironmentError: No Gemini API key` | Set `GEMINI_API_KEY` env var (see Setup above) |
| `FileNotFoundError: mock_tweets.json` | Run `python mock_scraper.py --init` |
| `opencv-python` import error | Run `pip install opencv-python` |
| `imagehash` not found | Run `pip install imagehash` |
| Windows codec warning for .mp4 | Use `opencv-python-headless` instead |

---

## 📋 API Key Note

This project uses **Google AI Studio** (not GCP Console).  
- URL: https://aistudio.google.com/app/apikey  
- **Free tier** includes Gemini 2.0 Flash — no billing needed  
- Model used: `gemini-2.0-flash-exp`

---

*SportsGuard AI — Google Solution Challenge 2026*
