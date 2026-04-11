#!/usr/bin/env python3
"""
SportsGuard AI — Gemini Content Analyzer (Module C)
Classifies video frames + social-media context as Piracy, Transformative,
or Meme using Google Gemini 2.0 Flash.

Merged version:
  - Backend's ``analyze_content()`` API signature (used by app.py)
  - Member 2's ``google-genai`` SDK with Pydantic schema enforcement
  - Graceful fallback when API key is missing or SDK unavailable

Usage (library):
    from gemini_analyzer import analyze_content
    result = analyze_content(pil_image, "tweet text", api_key="...")

Usage (CLI):
    python gemini_analyzer.py --text "Full IPL match free download!"
"""

import base64
import json
import logging
import os
import time
from io import BytesIO
from typing import Any, Dict, Optional, Union

import numpy as np
from PIL import Image

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s — %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("gemini_analyzer")

# ---------------------------------------------------------------------------
# Model & prompt configuration
# ---------------------------------------------------------------------------
MODEL_NAME = "gemini-2.0-flash"

SYSTEM_PROMPT = """\
You are **SportsGuard AI**, a digital-rights compliance engine for sports content.

Given a video frame **and** social-media post text, classify the content usage
into exactly one of three categories and assign a piracy risk score (0-100).

| Category        | Description                                                               |
|-----------------|---------------------------------------------------------------------------|
| **Piracy**      | Clean, unedited broadcast footage. No overlays, no commentary, no         |
|                 | watermarks added by the uploader. Promotional language encouraging         |
|                 | watching the full match outside official channels. High resolution.        |
| **Transformative** | Analysis graphics, telestration overlays, picture-in-picture with       |
|                 | commentator face-cam, educational / tactical breakdowns, slow-motion       |
|                 | with analysis text. This is typically fair use.                           |
| **Meme**        | Heavy editing, reaction images, meme text overlays, low resolution by     |
|                 | design, surreal / humorous intent, fan-art mashups. Also fair use.        |

### Decision rules
- If the frame shows CLEAN broadcast footage with scoreboard graphics that are
  part of the ORIGINAL feed (not added by the user), and the text promotes
  "watch free" / "full match" / piracy keywords → **Piracy** (risk 70-100).
- If the frame contains ADDITIONAL overlays, arrows, circles, or the text
  discusses tactics / strategy — it is **Transformative** (risk 10-50).
- If the image is heavily edited, cropped into a meme template, or paired
  with humorous / reaction text → **Meme** (risk 0-30).
- When uncertain, lean toward the LESS restrictive classification.

### Output rules
Return ONLY valid JSON — no markdown fences, no explanation outside the JSON.
"""

# ---------------------------------------------------------------------------
# Default fallback when everything fails
# ---------------------------------------------------------------------------
DEFAULT_RESPONSE: Dict[str, Any] = {
    "classification": "Unknown",
    "risk_score": 50,
    "reasoning": "API error — unable to classify.",
}

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _to_pil(frame: Union[Image.Image, np.ndarray]) -> Image.Image:
    """Normalise input to a PIL RGB Image."""
    if isinstance(frame, np.ndarray):
        if frame.ndim == 2:
            return Image.fromarray(frame).convert("RGB")
        return Image.fromarray(frame[..., ::-1])  # BGR → RGB
    return frame.convert("RGB") if frame.mode != "RGB" else frame


def _pil_to_base64(image: Image.Image, fmt: str = "JPEG") -> str:
    """Convert a PIL Image to a base64-encoded string."""
    buffer = BytesIO()
    image.save(buffer, format=fmt)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


# Public alias — used by verify_member2.py and other scripts
pil_to_base64 = _pil_to_base64


def _create_demo_frame(width: int = 320, height: int = 240) -> Image.Image:
    """
    Create a synthetic broadcast-style frame for testing/demo purposes.
    Returns a PIL RGB Image resembling a cricket broadcast with a
    green pitch background and a dark scoreboard bar.
    """
    arr = np.zeros((height, width, 3), dtype=np.uint8)
    arr[:, :] = [34, 139, 34]      # green pitch
    arr[0:30, :] = [10, 10, 10]    # broadcast scoreboard bar
    return Image.fromarray(arr, mode="RGB")


def _validate_response(data: Dict[str, Any]) -> Dict[str, Any]:
    """Sanity-check and coerce the response dict."""
    classification = data.get("classification", "Unknown")
    if classification not in ("Piracy", "Transformative", "Meme"):
        classification = "Unknown"

    risk_score = int(data.get("risk_score", 50))
    risk_score = max(0, min(100, risk_score))

    reasoning = str(data.get("reasoning", ""))

    return {
        "classification": classification,
        "risk_score": risk_score,
        "reasoning": reasoning,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def analyze_content(
    frame_image: Union[Image.Image, np.ndarray],
    context_text: str,
    api_key: Optional[str] = None,
    *,
    max_retries: int = 3,
    timeout: float = 10.0,
    model_name: str = MODEL_NAME,
) -> Dict[str, Any]:
    """
    Classify a video frame + social-media text via Google Gemini.

    Uses the current ``google-genai`` SDK (``genai.Client``).

    Parameters
    ----------
    frame_image : PIL.Image.Image or numpy.ndarray
        A single video frame.
    context_text : str
        The accompanying social-media post text / caption.
    api_key : str, optional
        Gemini API key.  Falls back to ``GEMINI_API_KEY`` env var.
    max_retries : int
        Retry count for transient API errors (default 3).
    timeout : float
        Per-request timeout in seconds (default 10).
    model_name : str
        Which Gemini model to call (default ``gemini-2.0-flash``).

    Returns
    -------
    dict
        ``{"classification": str, "risk_score": int, "reasoning": str}``
    """
    # Resolve API key
    api_key = (
        api_key
        or os.environ.get("GEMINI_API_KEY")
        or os.environ.get("GOOGLE_API_KEY")
    )
    if not api_key:
        log.error("No Gemini API key provided. Returning default response.")
        return dict(DEFAULT_RESPONSE)

    # Late import so the rest of the module loads even without the SDK
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        log.error("google-genai package not installed. Returning default.")
        return dict(DEFAULT_RESPONSE)

    # Build the client
    client = genai.Client(api_key=api_key)

    # Prepare the image
    pil_image = _to_pil(frame_image)
    b64 = _pil_to_base64(pil_image)
    image_part = types.Part.from_bytes(
        data=base64.b64decode(b64),
        mime_type="image/jpeg",
    )

    # Build the user prompt
    user_prompt = (
        f'Social media post text: "{context_text}"\n\n'
        "Analyze the attached video frame together with the post text above.\n"
        "Classify the content usage and return JSON with keys: "
        "classification, risk_score, reasoning."
    )

    # JSON response schema for structured output
    response_schema = {
        "type": "object",
        "properties": {
            "classification": {
                "type": "string",
                "enum": ["Piracy", "Transformative", "Meme"],
            },
            "risk_score": {
                "type": "integer",
                "minimum": 0,
                "maximum": 100,
            },
            "reasoning": {
                "type": "string",
            },
        },
        "required": ["classification", "risk_score", "reasoning"],
    }

    # Retry loop with exponential back-off
    last_error: Optional[Exception] = None
    for attempt in range(1, max_retries + 1):
        try:
            log.info("Gemini API call attempt %d/%d …", attempt, max_retries)

            response = client.models.generate_content(
                model=model_name,
                contents=[image_part, user_prompt],
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    response_schema=response_schema,
                    temperature=0.1,
                    max_output_tokens=512,
                ),
            )

            # Parse the JSON text
            raw_text = response.text.strip()
            data = json.loads(raw_text)
            validated = _validate_response(data)

            log.info(
                "Classification: %s | Risk: %d | %s",
                validated["classification"],
                validated["risk_score"],
                validated["reasoning"][:80],
            )
            return validated

        except json.JSONDecodeError as exc:
            log.warning("Attempt %d: Invalid JSON from Gemini — %s", attempt, exc)
            last_error = exc
        except Exception as exc:
            log.warning("Attempt %d: Gemini API error — %s", attempt, exc)
            last_error = exc

        # Back off before retry
        time.sleep(min(2 ** attempt, 8))

    log.error("All %d Gemini attempts failed. Last error: %s", max_retries, last_error)
    return dict(DEFAULT_RESPONSE)


# ---------------------------------------------------------------------------
# Convenience alias — keeps backward-compatibility with Member 2's branch
# ---------------------------------------------------------------------------

def analyze_frame(
    frame: Union[Image.Image, "str"],
    context_text: str,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Thin wrapper around ``analyze_content`` that also accepts base64 strings.

    This preserves the original ``analyze_frame()`` API from the
    ``abhinav/dev-ai`` branch for any code that still references it.
    """
    if isinstance(frame, str):
        # Decode base64 string to PIL Image
        image_data = base64.b64decode(frame)
        frame = Image.open(BytesIO(image_data)).convert("RGB")
    return analyze_content(frame, context_text, api_key=api_key)


# ---------------------------------------------------------------------------
# CLI / smoke test
# ---------------------------------------------------------------------------

def main() -> None:
    """Quick smoke test with a blank image (requires a valid API key)."""
    import argparse

    parser = argparse.ArgumentParser(description="SportsGuard Gemini Analyzer")
    parser.add_argument("--image", help="Path to a test image file")
    parser.add_argument("--text", default="Full IPL match free download link!", help="Post text")
    parser.add_argument("--api-key", default=None, help="Gemini API key")
    args = parser.parse_args()

    if args.image:
        img = Image.open(args.image).convert("RGB")
    else:
        # Create a dummy 320×240 green-field frame
        arr = np.zeros((240, 320, 3), dtype=np.uint8)
        arr[:, :] = [34, 139, 34]  # green pitch
        arr[0:30, :] = [10, 10, 10]  # broadcast bar
        img = Image.fromarray(arr, mode="RGB")

    result = analyze_content(img, args.text, api_key=args.api_key)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
