from __future__ import annotations

import os
import tempfile
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from backend.database import supabase
from backend.scraper import scrape_and_check
from backend.vision import extract_and_hash_video
from backend.state import latest_scan_status   # <-- shared state

cors_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "*").split(",")
    if origin.strip()
]

app = FastAPI(title="SportsGuard AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins if cors_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "SportsGuard AI API", "status": "running"}


@app.post("/api/upload")
async def upload_official_video(file: UploadFile = File(...)) -> dict[str, object]:
    if not file.filename or not file.filename.lower().endswith(".mp4"):
        raise HTTPException(status_code=400, detail="Only .mp4 files are supported.")

    temp_path: str | None = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
            temp_path = temp_file.name
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                temp_file.write(chunk)

        hashes = extract_and_hash_video(temp_path)
        insert_response = (
            supabase.table("official_assets")
            .insert(
                {
                    "filename": Path(file.filename).name,
                    "hashes": hashes,
                }
            )
            .execute()
        )

        return {
            "message": "Official asset uploaded and hashed successfully.",
            "filename": Path(file.filename).name,
            "hashes": hashes,
            "record": (insert_response.data or [None])[0],
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Upload processing failed: {exc}") from exc
    finally:
        await file.close()
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


@app.post("/api/start-scan")
async def start_scan(background_tasks: BackgroundTasks) -> dict[str, str]:
    background_tasks.add_task(scrape_and_check)
    return {"message": "Live scan started in the background."}


@app.get("/api/scan-status")
def scan_status():
    return latest_scan_status


@app.get("/api/detections")
def get_detections() -> list[dict]:
    try:
        response = (
            supabase.table("detections")
            .select("*")
            .order("scanned_at", desc=True)
            .limit(20)
            .execute()
        )
        return response.data or []
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not fetch detections: {exc}") from exc


@app.post("/api/reset-detections")
async def reset_detections():
    try:
        # Delete all detections by using a condition that matches every row
        supabase.table("detections") \
               .delete() \
               .neq("id", "00000000-0000-0000-0000-000000000000") \
               .execute()
        return {"message": "All detections cleared."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))