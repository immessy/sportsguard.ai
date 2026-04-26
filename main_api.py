from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
from core_engine import SportsGuardEngine 

app = FastAPI()
engine = SportsGuardEngine()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create directory if it doesn't exist
os.makedirs("test_data/videos", exist_ok=True)
OFFICIAL_ASSET_PATH = "test_data/videos/official_match.mp4"

@app.post("/analyze")
async def analyze_video(
    file: UploadFile = File(...), 
    mode: str = Form(...), # NEW: "register" or "scan"
    platform: str = Form(...)
):
    temp_path = f"temp_{file.filename}"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    if mode == "register":
        # 1. HOLDING MEMORY: Save this as the master official asset
        shutil.copy(temp_path, OFFICIAL_ASSET_PATH)
        os.remove(temp_path)
        print("✅ NEW MASTER ASSET REGISTERED")
        return {"status": "registered", "message": "Official asset secured."}
    
    else:
        # 2. SCANNING: Compare uploaded file to the master asset
        if not os.path.exists(OFFICIAL_ASSET_PATH):
            os.remove(temp_path)
            return {"status": "error", "message": "No official asset registered yet!"}
            
        # Run real detection
        engine.process_detection(
            official_path=OFFICIAL_ASSET_PATH, 
            suspect_path=temp_path, 
            platform=platform, 
            post_text=f"Suspicious upload: {file.filename}"
        )
        os.remove(temp_path)
        return {"status": "scanned", "message": "Threat analysis complete."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)