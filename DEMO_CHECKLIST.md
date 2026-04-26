# SportsGuard AI Demo Checklist

## Before the Demo

1. Confirm Supabase tables exist by running [supabase/schema.sql](C:/Users/abhin/sportsguard.ai%20-%20Copy/supabase/schema.sql).
2. Confirm backend `.env` contains:
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `GEMINI_API_KEY`
   - `CORS_ORIGINS`
3. Start the backend:

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

4. Start the frontend:

```bash
cd frontend
npm run dev
```

5. Open `http://localhost:3000`.
6. Keep the backend terminal visible so judges can see the real API is running.

## Fast Rehearsal

1. Run the smoke test in another terminal:

```bash
python scripts/api_smoke_test.py --base-url http://localhost:8000 --video test_data/videos/official_match.mp4
```

2. Confirm:
   - `/api/health` returns `ok`
   - upload returns 3 hashes
   - scan trigger returns success
   - detections endpoint returns rows or an empty list without crashing

## Live Demo Flow

1. Start on the dashboard and explain the pipeline in one sentence:
   "We upload an official sports clip, store visual fingerprints in Supabase, scan Reddit previews only, and classify matches with Gemini."
2. Upload `official_match.mp4`.
3. Point out that the upload goes to FastAPI, not directly to the browser or a fake mock.
4. Trigger `Live Web Scan`.
5. Explain the memory guardrail:
   "We never download Reddit videos on the free server, only thumbnails and preview images."
6. Open the detections feed and narrate:
   - matched Reddit URL
   - Gemini label
   - risk score
   - reasoning

## Backup Talking Points

1. If Reddit has no fresh visual match at demo time, explain that the scan is still live and bounded to the most recent posts.
2. If Gemini times out, mention the explicit fallback path in the backend.
3. If asked about scale, mention:
   - background tasks
   - thumbnail-only scan path
   - Supabase persistence
   - deployable backend on Render or Railway
   - deployable frontend on Vercel

## Hard Stop Checks

1. Do not show the old Firebase/Vite prototype.
2. Do not mention PRAW or Reddit API keys because this MVP intentionally avoids them.
3. Keep one browser tab on the frontend and one terminal on the backend.
