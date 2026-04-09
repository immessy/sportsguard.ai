"""
gemini_analyzer.py
==================
SportsGuard AI - Module C: Gemini AI Integration
Member 2 (AI & Data Specialist)

Analyzes video frames + social media context to classify content as
Piracy, Transformative, or Meme using Google Gemini 2.0 Flash.

Uses the current google-genai SDK (NOT the deprecated google-generativeai).

Usage:
    python gemini_analyzer.py                     # runs built-in demo
    from gemini_analyzer import analyze_frame     # import in other modules

Setup:
    pip install google-genai Pillow
    export GEMINI_API_KEY="your_key"   # get free key at aistudio.google.com
"""

import os
import base64
import json
import logging
from io import BytesIO
from typing import Optional, Literal
from enum import Enum

from PIL import Image
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("gemini_analyzer")

# ---------------------------------------------------------------------------
# Model & Schema
# ---------------------------------------------------------------------------
MODEL_NAME = "gemini-2.5-flash-exp"


class Classification(str, Enum):
    PIRACY = "Piracy"
    TRANSFORMATIVE = "Transformative"
    MEME = "Meme"


class ContentAnalysis(BaseModel):
    """Strict JSON schema for Gemini piracy classification output."""
    classification: Classification = Field(
        description="Content category: Piracy, Transformative, or Meme"
    )
    risk_score: int = Field(
        ge=0, le=100,
        description="Piracy risk score: 0 (safe) to 100 (high risk)"
    )
    reasoning: str = Field(
        description="Brief explanation of the classification decision"
    )


SYSTEM_INSTRUCTION = """You are SportsGuard AI, a copyright compliance assistant for sports content.

Analyze the provided video frame and social media post to determine:
1. CLASSIFICATION — Piracy (unauthorized broadcast/replay), Transformative (commentary/reaction/educational), or Meme (humorous remix)
2. RISK_SCORE — 0-100 piracy likelihood (0=clearly safe, 100=blatant piracy)
3. REASONING — brief explanation

Guidelines:
- Full match broadcasts, replays without commentary -> HIGH risk (Piracy, 70-100)
- Reaction videos, commentary, highlights with substantial added content -> LOW-MEDIUM (Transformative, 10-50)  
- Memes, short funny clips with humor/text overlays -> LOW risk (Meme, 0-30)
- Consider: hashtags, captions, visible watermarks all matter.
"""


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _get_client(api_key: Optional[str] = None) -> genai.Client:
    """Create a configured Gemini client.

    Priority:
        1. Explicit ``api_key`` argument
        2. ``GEMINI_API_KEY`` environment variable
        3. ``GOOGLE_API_KEY`` environment variable (legacy fallback)

    Raises:
        EnvironmentError: If no API key is found.
    """
    key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not key:
        raise EnvironmentError(
            "No Gemini API key found.\n"
            "Set the GEMINI_API_KEY environment variable:\n"
            "  Windows PowerShell: $env:GEMINI_API_KEY = 'your_key'\n"
            "  Linux/macOS:        export GEMINI_API_KEY='your_key'\n"
            "Get a free key at: https://aistudio.google.com/app/apikey"
        )
    return genai.Client(api_key=key)


def pil_to_base64(image: Image.Image, fmt: str = "JPEG") -> str:
    """Convert a PIL Image to a base64-encoded string.

    Args:
        image: Source PIL Image object.
        fmt: Image format for encoding (JPEG recommended for photos).

    Returns:
        Base64-encoded string of the image.
    """
    buffer = BytesIO()
    if image.mode != "RGB":
        image = image.convert("RGB")
    image.save(buffer, format=fmt)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def _build_image_part(frame: "Image.Image | str") -> types.Part:
    """Build a Gemini-compatible image Part from a PIL Image or base64 string.

    Args:
        frame: Either a PIL Image or a base64-encoded JPEG string.

    Returns:
        ``types.Part`` with inline image data.
    """
    if isinstance(frame, Image.Image):
        b64 = pil_to_base64(frame)
    elif isinstance(frame, str):
        b64 = frame  # assume already base64-encoded
    else:
        raise TypeError(f"Unsupported frame type: {type(frame)}. Use PIL Image or base64 str.")

    return types.Part.from_bytes(
        data=base64.b64decode(b64),
        mime_type="image/jpeg",
    )


# ---------------------------------------------------------------------------
# Core analysis function
# ---------------------------------------------------------------------------

def analyze_frame(
    frame: "Image.Image | str",
    context_text: str,
    api_key: Optional[str] = None,
) -> dict:
    """Analyze a video frame + social media context for piracy risk.

    Args:
        frame: A PIL Image object OR a base64-encoded JPEG string representing
               a single video frame to analyze.
        context_text: The social media post text (tweet, caption, etc.) that
                      accompanied the video.
        api_key: Optional Gemini API key. Falls back to GEMINI_API_KEY env var.

    Returns:
        A dictionary with the following schema::

            {
                "classification": "Piracy" | "Transformative" | "Meme",
                "risk_score": 0-100,
                "reasoning": "brief explanation"
            }

    Raises:
        EnvironmentError: If no API key is configured.
        ValueError: If the Gemini response cannot be parsed as valid JSON.

    Example:
        >>> from PIL import Image
        >>> img = Image.open("frame.jpg")
        >>> result = analyze_frame(img, "Watch this amazing goal! #soccer")
        >>> print(result["classification"])  # e.g. "Transformative"
    """
    client = _get_client(api_key)
    image_part = _build_image_part(frame)
    text_part = (
        f'Social media post: "{context_text}"\n\n'
        "Analyze the attached video frame and the post context. "
        "Classify and score the piracy risk."
    )

    logger.info("Sending frame to Gemini %s for analysis...", MODEL_NAME)
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[image_part, text_part],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                response_mime_type="application/json",
                response_schema=ContentAnalysis,
                temperature=0.1,
                max_output_tokens=512,
            ),
        )
    except Exception as exc:
        logger.error("Gemini API call failed: %s", exc)
        raise

    raw_text = response.text.strip()
    logger.debug("Raw Gemini response: %s", raw_text)

    try:
        result = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse Gemini response as JSON: %s", raw_text)
        raise ValueError(f"Gemini returned non-JSON output: {raw_text!r}") from exc

    # Validate keys
    required = {"classification", "risk_score", "reasoning"}
    missing = required - result.keys()
    if missing:
        raise ValueError(f"Gemini response missing keys: {missing}. Got: {result}")

    logger.info(
        "Analysis complete -> classification=%s, risk_score=%s",
        result["classification"], result["risk_score"],
    )
    return result


# ---------------------------------------------------------------------------
# Batch helper
# ---------------------------------------------------------------------------

def analyze_multiple_frames(
    frames: list,
    context_text: str,
    api_key: Optional[str] = None,
    sample_interval: int = 1,
) -> list[dict]:
    """Analyze multiple frames and return aggregated results.

    Args:
        frames: List of (frame_index, PIL Image or base64) tuples.
        context_text: Social media post text.
        api_key: Optional Gemini API key.
        sample_interval: Analyze every N-th frame (default=1 = all frames).

    Returns:
        List of analysis dicts, each with an additional ``frame_index`` key.
    """
    results = []
    sampled = frames[::sample_interval]
    logger.info("Analyzing %d / %d frames...", len(sampled), len(frames))

    for idx, frame_data in sampled:
        try:
            result = analyze_frame(frame_data, context_text, api_key=api_key)
            result["frame_index"] = idx
            results.append(result)
        except Exception as exc:
            logger.warning("Skipping frame %d due to error: %s", idx, exc)

    return results


# ---------------------------------------------------------------------------
# Demo / self-test
# ---------------------------------------------------------------------------

def _create_demo_frame() -> Image.Image:
    """Create a synthetic 'sports broadcast' frame for demo purposes."""
    try:
        import numpy as np
        arr = np.zeros((360, 640, 3), dtype=np.uint8)
        arr[:, :] = [34, 139, 34]       # green pitch background
        arr[0:40, :] = [10, 10, 10]     # dark top bar (broadcast UI)
        arr[320:360, :] = [10, 10, 10]  # dark bottom bar
        return Image.fromarray(arr, mode="RGB")
    except ImportError:
        return Image.new("RGB", (640, 360), color=(34, 139, 34))


if __name__ == "__main__":
    print("=" * 60)
    print("SportsGuard AI -- Module C: Gemini Analyzer Demo")
    print("=" * 60)

    demo_frame = _create_demo_frame()
    demo_context = "Look at this crazy goal! #soccer #WorldCup"

    print(f"\nFrame size : {demo_frame.size}")
    print(f"Context    : {demo_context!r}")
    print("\nCalling Gemini API...\n")

    try:
        result = analyze_frame(demo_frame, demo_context)
        print("[OK] Analysis Result:")
        print(json.dumps(result, indent=2))
    except EnvironmentError as e:
        print(f"\n[WARN] API Key Error:\n{e}")
    except Exception as e:
        print(f"\n[ERROR] Analysis failed: {e}")

    print("\n" + "=" * 60)
    print("Done. Set GEMINI_API_KEY env var to run with a real key.")
    print("Get a free key at: https://aistudio.google.com/app/apikey")
    print("=" * 60)
