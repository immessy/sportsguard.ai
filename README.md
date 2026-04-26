# SportsGuard AI MVP

SportsGuard AI is a working end-to-end prototype for detecting likely sports piracy using:

- Next.js + Tailwind frontend
- FastAPI backend
- Supabase PostgreSQL
- OpenCV + ImageHash
- Gemini 2.5 Flash
- Reddit `.json` scraping without PRAW or Reddit API keys

## Architecture

1. A rights holder uploads an official `.mp4` through the Next.js dashboard.
2. FastAPI streams the upload to a temp file, extracts 3 evenly spaced frames, computes `pHash` values, and stores them in Supabase `official_assets`.
3. The operator triggers a live scan.
4. FastAPI runs `scrape_and_check()` in a `BackgroundTask`.
5. The scraper fetches `https://www.reddit.com/r/<subreddit>/new.json?limit=10` with a desktop `User-Agent`.
6. The scraper downloads only preview images or thumbnails, never full Reddit videos.
7. Each preview image is hashed and compared against stored official hashes by Hamming distance.
8. If the best match is below the configured threshold, the Reddit title is sent to Gemini for classification: `Piracy`, `Meme`, or `Transformative`.
9. The final result is written to Supabase `detections`.
10. The Next.js dashboard polls the backend every 5 seconds and renders the latest 20 detections.

## Project Structure

```text
backend/
  database.py
  gemini_agent.py
  main.py
  scraper.py
  vision.py
frontend/
  package.json
  src/app/layout.tsx
  src/app/page.tsx
supabase/
  schema.sql
requirements.txt
render.yaml
railway.json
```

## Environment Variables

Copy [.env.example](C:/Users/abhin/sportsguard.ai%20-%20Copy/.env.example) to `.env` for the backend and set:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-service-role-or-secret-key
GEMINI_API_KEY=your-gemini-api-key
REDDIT_SUBREDDIT=sports
HASH_DISTANCE_THRESHOLD=10
CORS_ORIGINS=http://localhost:3000,https://your-vercel-app.vercel.app
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

For the frontend, copy [frontend/.env.local.example](C:/Users/abhin/sportsguard.ai%20-%20Copy/frontend/.env.local.example) to `frontend/.env.local`:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## Supabase Setup

1. Create a Supabase project.
2. Open the SQL editor.
3. Run [supabase/schema.sql](C:/Users/abhin/sportsguard.ai%20-%20Copy/supabase/schema.sql).
4. Copy the project URL and service-role key into your backend `.env`.

The schema creates:

- `official_assets`
- `detections`

## Local Development

### Backend

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Backend endpoints:

- `GET /api/health`
- `POST /api/upload`
- `POST /api/start-scan`
- `GET /api/detections`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

## Smoke Test Script

Use [scripts/api_smoke_test.py](C:/Users/abhin/sportsguard.ai%20-%20Copy/scripts/api_smoke_test.py) to exercise the live backend with a real upload and scan trigger:

```bash
python scripts/api_smoke_test.py --base-url http://localhost:8000 --video test_data/videos/official_match.mp4
```

What it does:

- checks `GET /api/health`
- uploads a real `.mp4` through `POST /api/upload`
- triggers the live Reddit scan through `POST /api/start-scan`
- polls `GET /api/detections`

## Sample API Commands

### Health Check

```bash
curl http://localhost:8000/api/health
```

### Upload Official Video

```bash
curl -X POST "http://localhost:8000/api/upload" ^
  -H "accept: application/json" ^
  -H "Content-Type: multipart/form-data" ^
  -F "file=@test_data/videos/official_match.mp4;type=video/mp4"
```

### Trigger Live Scan

```bash
curl -X POST http://localhost:8000/api/start-scan
```

### Fetch Latest Detections

```bash
curl http://localhost:8000/api/detections
```

## Production Deployment

### Backend on Render

This repo includes [render.yaml](C:/Users/abhin/sportsguard.ai%20-%20Copy/render.yaml).

1. Push the repo to GitHub.
2. Create a new Render Blueprint or Web Service.
3. Point it at this repo.
4. Set these required env vars in Render:
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `GEMINI_API_KEY`
   - `CORS_ORIGINS`
5. Optional env vars:
   - `REDDIT_SUBREDDIT`
   - `HASH_DISTANCE_THRESHOLD`

Render start command:

```bash
uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

### Backend on Railway

This repo includes [railway.json](C:/Users/abhin/sportsguard.ai%20-%20Copy/railway.json).

1. Create a new Railway project from the repo.
2. Add the same backend env vars as above.
3. Railway will run:

```bash
uvicorn backend.main:app --host 0.0.0.0 --port $PORT
```

### Frontend on Vercel

The frontend lives in [frontend](C:/Users/abhin/sportsguard.ai%20-%20Copy/frontend) and includes [frontend/vercel.json](C:/Users/abhin/sportsguard.ai%20-%20Copy/frontend/vercel.json).

1. Import the repo into Vercel.
2. Set the project root to `frontend`.
3. Set:

```env
NEXT_PUBLIC_API_BASE_URL=https://your-backend-host.onrender.com
```

4. Deploy.

## API Contract

### `POST /api/upload`

Accepts `multipart/form-data` with a single `.mp4` file.

Returns:

```json
{
  "message": "Official asset uploaded and hashed successfully.",
  "filename": "official_clip.mp4",
  "hashes": ["abc123...", "def456...", "ghi789..."],
  "record": {}
}
```

### `POST /api/start-scan`

Returns:

```json
{
  "message": "Live scan started in the background."
}
```

### `GET /api/detections`

Returns the latest 20 rows from `detections`.

## Memory-Safety Choices

- Official uploads are streamed to disk in 1 MB chunks.
- Temp files are cleaned up after hashing.
- Reddit scans use thumbnails or preview images only.
- No `.mp4` Reddit media is downloaded in the scraper.
- Matching is bounded to the latest 10 Reddit posts per scan.
- Vision work is done on 3 frames per official upload to keep compute small.

## Notes

- `SUPABASE_KEY` should be a backend-only key because inserts happen server-side.
- The frontend never talks directly to Supabase.
- Gemini has a fallback response if the model times out or returns invalid JSON.
- Reddit JSON payloads are handled defensively with `try/except` so missing nodes do not crash the scan.

## Demo Runbook

Use [DEMO_CHECKLIST.md](C:/Users/abhin/sportsguard.ai%20-%20Copy/DEMO_CHECKLIST.md) as the short presentation checklist before going in front of judges.
