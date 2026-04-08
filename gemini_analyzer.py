#!/usr/bin/env python3
"""
SportsGuard AI — Gemini Analyzer (Module C)
Uses Google Gemini 2.0 Flash for multimodal content-usage classification.

The analyzer accepts a video frame image and social-media context text,
then returns a structured JSON classification:
  - "Piracy"        → raw, unedited re-uploads
  - "Transformative" → tactical analysis, commentary overlays
  - "Meme"          → fan content, reaction templates, fair use

Usage:
    from gemini_analyzer import analyze_content
    result = analyze_content(pil_image, "Check out this IPL catch!", api_key="...")
"""

import json
import logging
import os
import time
from typing import Any, Dict, Optional, Union

import numpy as np
from PIL import Image

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s — %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("gemini_analyzer")

# ---------------------------------------------------------------------------
# Optimal system prompt for Gemini 2.0 Flash
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """\
You are SportsGuard AI — a specialised content-moderation classifier for \
sports broadcasting. You will be given:

1. A single video frame (image) from social media.
2. The post's text / caption / metadata.

Your job is to classify how the content is being used. Think step-by-step:

### Classification categories
| Category        | Indicators                                                                 |
|-----------------|----------------------------------------------------------------------------|
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
  "watch free" / "full match" / piracy keywords → **Piracy**.
- If the frame contains ADDITIONAL overlays, arrows, circles, or the text
  discusses tactics / strategy — it is **Transformative**.
- If the image is heavily edited, cropped into a meme template, or paired
  with humorous / reaction text → **Meme**.
- When uncertain, lean toward the LESS restrictive classification.

### Output rules
Return ONLY valid JSON — no markdown fences, no explanation outside the JSON.
"""

# The JSON schema we enforce via Gemini's response_schema feature
RESPONSE_SCHEMA = {
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
    model_name: str = "gemini-2.0-flash",
) -> Dict[str, Any]:
    """
    Classify a video frame + social-media text via Google Gemini.

    Parameters
    ----------
    frame_image : PIL.Image.Image or numpy.ndarray
        A single video frame.
    context_text : str
        The accompanying social-media post text / caption.
    api_key : str, optional
        Gemini API key.  Falls back to the ``GEMINI_API_KEY`` env var.
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
    api_key = api_key or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        log.error("No Gemini API key provided. Returning default response.")
        return dict(DEFAULT_RESPONSE)

    # Late import so the rest of the module loads even without the SDK
    try:
        import google.generativeai as genai
    except ImportError:
        log.error("google-generativeai package not installed. Returning default.")
        return dict(DEFAULT_RESPONSE)

    # Configure SDK
    genai.configure(api_key=api_key)

    # Prepare the image
    pil_image = _to_pil(frame_image)

    # Build the user prompt (image + text context)
    user_prompt = (
        f"Social media post text: \"{context_text}\"\n\n"
        "Analyze the attached image frame together with the post text above.\n"
        "Classify the content usage and return JSON with keys: "
        "classification, risk_score, reasoning."
    )

    # Retry loop
    last_error: Optional[Exception] = None
    for attempt in range(1, max_retries + 1):
        try:
            log.info("Gemini API call attempt %d/%d …", attempt, max_retries)

            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=SYSTEM_PROMPT,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    response_schema=RESPONSE_SCHEMA,
                    temperature=0.2,   # low temperature for classification
                    max_output_tokens=512,
                ),
            )

            response = model.generate_content(
                [pil_image, user_prompt],
                request_options={"timeout": timeout},
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
# Example / CLI
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
        # Create a dummy 320×240 black image
        img = Image.new("RGB", (320, 240), color=(0, 0, 0))

    result = analyze_content(img, args.text, api_key=args.api_key)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
