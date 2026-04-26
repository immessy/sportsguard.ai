import cv2
import imagehash
from PIL import Image
import numpy as np
from google import genai # The new 2026 SDK
import firebase_admin
from firebase_admin import credentials, firestore
import json
import os

# --- 1. SETUP & CONFIGURATION ---
# Replace with your actual Gemini API Key
client = genai.Client(api_key="GEMINI_API_KEY")
MODEL_ID = "gemini-2.5-flash" # Using the latest Flash model

# Initialize Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)
db = firestore.client()

class SportsGuardEngine:
    def __init__(self):
        print("🛡️ SportsGuard REAL Engine (v2026) Active")

    def extract_keyframes(self, video_path):
        if not os.path.exists(video_path):
            print(f"❌ File not found: {video_path}")
            return []
        cap = cv2.VideoCapture(video_path)
        frames = []
        for _ in range(30):
            ret, frame = cap.read()
            if not ret: break
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frames.append(Image.fromarray(rgb_frame))
        cap.release()
        return frames

    def get_match_confidence(self, sig1_frames, sig2_frames):
        sig1 = [imagehash.phash(f) for f in sig1_frames]
        sig2 = [imagehash.phash(f) for f in sig2_frames]
        if not sig1 or not sig2: return 0.0
        matches = sum(1 for h1, h2 in zip(sig1, sig2) if (h1 - h2) <= 5)
        return round((matches / min(len(sig1), len(sig2))) * 100, 2)

    def analyze_with_gemini(self, post_text, match_score):
        prompt = f"""
        Analyze this sports media detection:
        Visual Match: {match_score}% 
        Post Text: "{post_text}"
        
        Return ONLY a raw JSON object (no markdown, no backticks):
        {{
            "classification": "Piracy" | "Transformative" | "Meme",
            "risk_score": 0-100,
            "reasoning": "One short sentence"
        }}
        """
        try:
            # New SDK call format
            response = client.models.generate_content(
                model=MODEL_ID,
                contents=prompt
            )
            # The new SDK returns text directly
            return json.loads(response.text.strip())
        except Exception as e:
            print(f"AI Error: {e}")
            return {"classification": "Review", "risk_score": 50, "reasoning": "AI analysis bypassed."}

    def process_detection(self, official_path, suspect_path, platform, post_text):
        print(f"🧬 Extracting visual fingerprints...")
        f1 = self.extract_keyframes(official_path)
        f2 = self.extract_keyframes(suspect_path)
        
        match_score = self.get_match_confidence(f1, f2)
        print(f"📊 Visual Match: {match_score}%")
        
        print("🤖 Consulting Gemini 2.0 for context...")
        ai_result = self.analyze_with_gemini(post_text, match_score)
        
        doc_data = {
            "platform": platform,
            "post_text": post_text,
            "match_confidence": match_score,
            "classification": ai_result['classification'],
            "risk_score": ai_result['risk_score'],
            "reasoning": ai_result['reasoning'],
            "detected_at": firestore.SERVER_TIMESTAMP
        }
        
        db.collection("detections").add(doc_data)
        print(f"✅ REAL DATA PUSHED TO DASHBOARD")

# --- EXECUTION ---
if __name__ == "__main__":
    engine = SportsGuardEngine()
    engine.process_detection(
        official_path="test_data/videos/official_match.mp4",
        suspect_path="test_data/videos/piracy_clip.mp4",
        platform="X (Twitter)",
        post_text="Watch the game live for free! Best quality here 📺"
    )