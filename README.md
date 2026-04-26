# SportsGuard AI

> **Automated sports piracy detection and DMCA enforcement — powered by computer vision and Gemini AI.**

SportsGuard AI is a full-stack prototype that fingerprints official broadcast clips, continuously scans Reddit for visual matches, classifies each hit using Gemini 2.5 Flash, and surfaces one-click DMCA takedown notices inside a clean enforcement console.

---

## How It Works

```
Rights Holder Uploads .mp4
         │
         ▼
  FastAPI streams file in 1 MB chunks
  OpenCV extracts 3 evenly-spaced frames
  ImageHash computes a pHash per frame
  Hashes stored in Supabase (official_assets)
         │
         ▼
  Operator triggers Live Scan
         │
         ▼
  Scraper fetches Reddit /r/<subreddit>/hot.json
  (no API key — public JSON endpoint, desktop UA)
         │
         ▼
  For each post: download thumbnail / preview image
  Compute pHash → Hamming distance vs stored hashes
  If distance < threshold (default 10):
         │
         ▼
  Gemini 2.5 Flash classifies post title
  → "Piracy" | "Meme" | "Transformative"
  → confidence score + 1-5 word reasoning
         │
         ▼
  Detection written to Supabase (detections)
         │
         ▼
  Next.js dashboard polls every 5 s
  Renders Threat Feed with risk scores + DMCA button
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 15, TypeScript, Tailwind CSS |
| Backend | FastAPI, Python 3.12+ |
| Database | Supabase (PostgreSQL) |
| Computer Vision | OpenCV (`opencv-python-headless`), ImageHash (`pHash`) |
| AI Classification | Google Gemini 2.5 Flash (`google-genai`) |
| Hosting (backend) | Render · Railway |
| Hosting (frontend) | Vercel |

---

## Project Structure

```
sportsguard.ai/
├── backend/
│   ├── main.py           # FastAPI app — all API routes
│   ├── vision.py         # OpenCV frame extraction + pHash logic
│   ├── scraper.py        # Reddit scraper + matching pipeline
│   ├── gemini_agent.py   # Gemini 2.5 Flash classification
│   ├── database.py       # Supabase client (singleton, lru_cache)
│   └── state.py          # In-memory scan status shared state
├── frontend/
│   └── src/app/
│       ├── page.tsx       # Enforcement console UI
│       └── layout.tsx     # Root layout + global styles
├── supabase/
│   └── schema.sql         # Table definitions + indexes
├── scripts/
│   └── api_smoke_test.py  # End-to-end API test script
├── test_data/             # Sample .mp4 clips for local testing
├── .env.example           # Environment variable template
├── requirements.txt       # Python dependencies
├── render.yaml            # Render deployment config
└── railway.json           # Railway deployment config
```

---

## Quickstart

### 1. Prerequisites

- Python 3.12 or later
- Node.js 18 or later
- A [Supabase](https://supabase.com) project (free tier works)
- A [Google AI Studio](https://aistudio.google.com) API key

### 2. Clone & Configure

```bash
git clone https://github.com/immessy/sportsguard.ai.git
cd sportsguard.ai
cp .env.example .env
```

Edit `.env`:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-service-role-key
GEMINI_API_KEY=your-gemini-api-key

# Optional — defaults shown
REDDIT_SUBREDDIT=sports
HASH_DISTANCE_THRESHOLD=10
CORS_ORIGINS=http://localhost:3000
```

### 3. Set Up the Database

1. Open your Supabase project → **SQL Editor**
2. Paste and run the contents of [`supabase/schema.sql`](supabase/schema.sql)

This creates two tables:

| Table | Purpose |
|---|---|
| `official_assets` | Stores filename + 3 pHash values per uploaded clip |
| `detections` | Stores every Reddit post that matched, with classification + risk score |

### 4. Run the Backend

```bash
# Create and activate a virtual environment (recommended)
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # macOS / Linux

pip install -r requirements.txt

uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Backend is now live at `http://localhost:8000`.

### 5. Run the Frontend

```bash
cd frontend
cp .env.local.example .env.local   # sets NEXT_PUBLIC_API_BASE_URL

npm install
npm run dev
```

Open `http://localhost:3000` — you should see the Enforcement Console with a green **Live** indicator.

---

## Using the Dashboard

| Step | Action |
|---|---|
| **1. Upload** | Click **Upload MP4** and select an official broadcast clip (`.mp4`). The backend hashes it and stores 3 pHash fingerprints. |
| **2. Scan** | Click **Start Scan**. FastAPI runs the Reddit scraper in a background task and polls for status every 2 seconds. |
| **3. Review** | The **Threat Feed** table populates with detections — each showing the Reddit URL, classification badge, risk score, and AI reasoning. |
| **4. Enforce** | For any `Piracy` detection, click **Issue DMCA** to generate a fully formatted DMCA takedown notice. Copy it to your clipboard and send it to the platform's copyright agent. |
| **5. Clear** | Click **Clear Feed** to reset the detections table for the next session. |

### Classification & Risk Scores

| Classification | Risk Score | Meaning |
|---|---|---|
| 🔴 **Piracy** | 85–100 | Unauthorised repost or live stream — issue DMCA immediately |
| 🟡 **Meme** | 35 | Humour / banter — may still infringe, manual review recommended |
| 🟢 **Transformative** | 0–15 | Commentary, analysis, or fan art — likely fair use |

---

## API Reference

All endpoints are served from `http://localhost:8000`.

### `GET /api/health`
Returns `{"status": "ok"}`. Used by the frontend for the live/down indicator.

### `POST /api/upload`
Upload an official `.mp4` file. Accepts `multipart/form-data`.

```bash
curl -X POST http://localhost:8000/api/upload \
  -F "file=@test_data/videos/official_match.mp4;type=video/mp4"
```

**Response:**
```json
{
  "message": "Official asset uploaded and hashed successfully.",
  "filename": "official_match.mp4",
  "hashes": ["a1b2c3d4e5f6...", "..."],
  "record": { "id": "uuid", "filename": "...", "hashes": [...] }
}
```

### `POST /api/start-scan`
Triggers the Reddit scraper as a FastAPI `BackgroundTask`.

```bash
curl -X POST http://localhost:8000/api/start-scan
```

**Response:**
```json
{ "message": "Live scan started in the background." }
```

### `GET /api/scan-status`
Returns the current scan state (polled every 2 s by the frontend).

```json
{ "status": "running" | "completed", "message": "..." }
```

### `GET /api/detections`
Returns the latest 20 detections, ordered newest first.

### `POST /api/reset-detections`
Deletes all rows from the `detections` table.

---

## Running the Smoke Test

The [`scripts/api_smoke_test.py`](scripts/api_smoke_test.py) script exercises the entire live pipeline end-to-end:

```bash
python scripts/api_smoke_test.py \
  --base-url http://localhost:8000 \
  --video test_data/videos/official_match.mp4
```

It will:
1. Check `GET /api/health`
2. Upload the test video via `POST /api/upload`
3. Trigger a Reddit scan via `POST /api/start-scan`
4. Poll `GET /api/detections` and print the results

---

## Deployment

### Backend — Render

This repo includes [`render.yaml`](render.yaml). To deploy:

1. Push the repo to GitHub.
2. Create a new **Web Service** on Render and point it at the repo.
3. Set the following environment variables in the Render dashboard:

| Variable | Required |
|---|---|
| `SUPABASE_URL` | ✅ |
| `SUPABASE_KEY` | ✅ |
| `GEMINI_API_KEY` | ✅ |
| `CORS_ORIGINS` | ✅ (set to your Vercel URL) |
| `REDDIT_SUBREDDIT` | Optional (default: `sports`) |
| `HASH_DISTANCE_THRESHOLD` | Optional (default: `10`) |

Render start command (already in `render.yaml`):
```bash
uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

### Backend — Railway

This repo includes [`railway.json`](railway.json). Import the repo into Railway and set the same environment variables as above.

### Frontend — Vercel

1. Import the repo into Vercel.
2. Set the **Root Directory** to `frontend`.
3. Add one environment variable:

```
NEXT_PUBLIC_API_BASE_URL=https://your-backend.onrender.com
```

4. Deploy.

---

## Environment Variables Reference

### Backend (`.env`)

| Variable | Description | Default |
|---|---|---|
| `SUPABASE_URL` | Your Supabase project URL | — |
| `SUPABASE_KEY` | Supabase service-role key (backend only) | — |
| `GEMINI_API_KEY` | Google AI Studio API key | — |
| `REDDIT_SUBREDDIT` | Subreddit to scan | `sports` |
| `HASH_DISTANCE_THRESHOLD` | Max Hamming distance for a match (0–64) | `10` |
| `CORS_ORIGINS` | Comma-separated allowed origins | `*` |

### Frontend (`frontend/.env.local`)

| Variable | Description | Default |
|---|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | Base URL of the FastAPI backend | `http://localhost:8000` |

---

## Design Decisions

**Why pHash over exact matching?**  
Perceptual hashing is resilient to the exact edits pirates use: re-encoding, resolution changes, brightness/contrast adjustments, and letterboxing. An exact hash would miss every one of those variants. Hamming distance of ≤10 bits (~84% similarity) catches them all.

**Why 3 frames per video?**  
A start frame, a middle frame, and an end frame give good coverage of a clip without loading the full video into memory. This keeps compute and storage costs near zero.

**Why Reddit's `.json` API without a key?**  
Reddit's public `*.json` endpoint works without authentication when a realistic browser `User-Agent` is used. This avoids rate-limit complexity and OAuth setup while still returning the data we need.

**Why Gemini as a second stage?**  
Hash matching can only tell you a thumbnail *looks similar* to an official frame. It can't tell you if the Reddit post is a meme, a highlights reel, or an actual pirated stream. Gemini reads the post title and provides the legal context needed to act responsibly.

**Why is the Supabase key backend-only?**  
The frontend never speaks directly to Supabase — all database reads and writes go through FastAPI. This keeps the service-role key off the client and prevents direct table manipulation.

---

