from __future__ import annotations

import json
import os
import time
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

MODEL_NAME = "gemini-2.5-flash"

FALLBACK_RESULT = {
    "classification": "Transformative",
    "confidence": 35,
    "reasoning": "Gemini timed out or returned an invalid response, so a low-confidence fallback was used.",
}


def _extract_json(raw_text: str) -> dict[str, Any]:
    if not raw_text or not raw_text.strip():
        raise ValueError("Gemini returned an empty response.")

    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in Gemini response.")

    parsed = json.loads(cleaned[start : end + 1])
    classification = parsed.get("classification")
    confidence = parsed.get("confidence")
    reasoning = parsed.get("reasoning")

    if classification not in {"Piracy", "Meme", "Transformative"}:
        raise ValueError("Gemini returned an unsupported classification.")
    if not isinstance(confidence, (int, float)):
        raise ValueError("Gemini confidence must be a number.")
    if not isinstance(reasoning, str) or not reasoning.strip():
        raise ValueError("Gemini reasoning must be a non-empty string.")

    return {
        "classification": classification,
        "confidence": int(max(0, min(100, confidence))),
        "reasoning": reasoning.strip(),
    }

def classify_content(post_text: str) -> dict[str, Any]:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {**FALLBACK_RESULT, "reasoning": "GEMINI_API_KEY is missing."}

    prompt = f"""
You are a sports media copyright classifier. Analyze the post title and return a JSON object.

Title: {post_text}

Return exactly this JSON structure:
{{
  "classification": "Piracy" | "Meme" | "Transformative",
  "confidence": 0-100,
  "reasoning": "very short phrase"
}}

Rules:
- Piracy: free streams, leaked broadcasts, unauthorised reposts
- Meme: humor, jokes, tifos, banter, absurd captions
- Transformative: commentary, analysis, edits, fan art
- Reasoning must be 1-5 words.
"""

    for attempt in range(1, 4):
        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.0,
                    max_output_tokens=500,   # more than enough
                    response_mime_type="application/json", ## force JSON mode
                ),
            )

            raw_text = response.text or ""
            print(f"[GEMINI] Raw ({len(raw_text)} chars): {repr(raw_text)}")

            # Try to parse the JSON directly
            try:
                parsed = json.loads(raw_text)
            except json.JSONDecodeError:
                # Maybe it has code fences
                cleaned = raw_text.strip().strip("`")
                if cleaned.startswith("json\n"):
                    cleaned = cleaned[5:]
                parsed = json.loads(cleaned)

            classification = str(parsed.get("classification", "")).capitalize()
            confidence = int(parsed.get("confidence", 0))
            reasoning = str(parsed.get("reasoning", ""))

            if classification in {"Piracy", "Meme", "Transformative"} and reasoning.strip():
                return {
                    "classification": classification,
                    "confidence": max(0, min(100, confidence)),
                    "reasoning": reasoning.strip(),
                }

            raise ValueError("Invalid fields")

        except Exception as e:
            print(f"[GEMINI] Attempt {attempt} error: {e}")
        time.sleep(1)

    # Final fallback: try to use whatever text we have as reasoning
    return {**FALLBACK_RESULT, "reasoning": "Gemini could not return valid JSON."}