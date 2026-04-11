#!/usr/bin/env python3
"""
SportsGuard AI — Synthetic Test Video Generator
Creates 4 visually distinct test videos for the classification pipeline:

  1. official_clip.mp4   — Clean broadcast-style (scoreboard, green pitch)
  2. piracy_clip.mp4     — Same content slightly cropped (simulates re-upload)
  3. transformative_clip.mp4 — Analysis overlays (arrows, circles, text)
  4. meme_clip.mp4        — Meme-style (bold text overlays, saturated colors)

Usage:
    python generate_test_videos.py          # Generates all 4 videos
    python generate_test_videos.py --only official  # Generate one
"""

import os
import sys
from pathlib import Path

import cv2
import numpy as np

OUTPUT_DIR = Path("test_data/videos")
FRAME_W, FRAME_H = 640, 360
FPS = 10


def _draw_pitch(frame: np.ndarray) -> np.ndarray:
    """Draw a stylized green cricket pitch background."""
    frame[:, :] = [34, 139, 34]  # green pitch
    # White boundary lines
    cv2.rectangle(frame, (30, 30), (610, 330), (255, 255, 255), 2)
    cv2.line(frame, (320, 30), (320, 330), (200, 200, 200), 1)
    # Pitch strip in center
    cv2.rectangle(frame, (290, 100), (350, 260), (194, 178, 128), -1)
    return frame


def _draw_scoreboard(frame: np.ndarray, idx: int) -> np.ndarray:
    """Draw a broadcast-style scoreboard overlay."""
    # Top bar
    cv2.rectangle(frame, (0, 0), (FRAME_W, 50), (15, 15, 40), -1)
    cv2.putText(frame, "MI vs CSK | IPL 2026", (10, 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    score = f"{145 + idx * 2}/{4 + idx // 10}"
    cv2.putText(frame, score, (10, 42),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 220, 255), 2)
    overs = f"Overs: {12 + idx // 6}.{idx % 6}"
    cv2.putText(frame, overs, (450, 42),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

    # Bottom bar — broadcaster logo
    cv2.rectangle(frame, (0, FRAME_H - 30), (FRAME_W, FRAME_H), (15, 15, 40), -1)
    cv2.putText(frame, "LIVE | Star Sports", (10, FRAME_H - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 180, 180), 1)
    return frame


def generate_official(n_frames: int = 30) -> str:
    """Official broadcast clip — clean scoreboard + green pitch."""
    path = str(OUTPUT_DIR / "official_clip.mp4")
    writer = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"mp4v"), FPS, (FRAME_W, FRAME_H))

    for i in range(n_frames):
        frame = np.zeros((FRAME_H, FRAME_W, 3), dtype=np.uint8)
        _draw_pitch(frame)
        _draw_scoreboard(frame, i)

        # Simulate slight camera movement
        shift_x = int(np.sin(i * 0.3) * 3)
        M = np.float32([[1, 0, shift_x], [0, 1, 0]])
        frame = cv2.warpAffine(frame, M, (FRAME_W, FRAME_H), borderValue=(34, 139, 34))

        writer.write(frame)
    writer.release()
    print(f"  [OK] {path} ({n_frames} frames)")
    return path


def generate_piracy(n_frames: int = 30) -> str:
    """Piracy clip — same broadcast content but cropped/resized (simulates raw re-upload)."""
    path = str(OUTPUT_DIR / "piracy_clip.mp4")
    writer = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"mp4v"), FPS, (FRAME_W, FRAME_H))

    for i in range(n_frames):
        frame = np.zeros((FRAME_H, FRAME_W, 3), dtype=np.uint8)
        _draw_pitch(frame)
        _draw_scoreboard(frame, i)

        shift_x = int(np.sin(i * 0.3) * 3)
        M = np.float32([[1, 0, shift_x], [0, 1, 0]])
        frame = cv2.warpAffine(frame, M, (FRAME_W, FRAME_H), borderValue=(34, 139, 34))

        # Crop 10% from each edge and resize back — simulates piracy
        crop_x, crop_y = FRAME_W // 10, FRAME_H // 10
        cropped = frame[crop_y:FRAME_H - crop_y, crop_x:FRAME_W - crop_x]
        frame = cv2.resize(cropped, (FRAME_W, FRAME_H), interpolation=cv2.INTER_LINEAR)

        # Add slight noise — re-encoding artifact
        noise = np.random.randint(-8, 8, frame.shape, dtype=np.int16)
        frame = np.clip(frame.astype(np.int16) + noise, 0, 255).astype(np.uint8)

        writer.write(frame)
    writer.release()
    print(f"  [OK] {path} ({n_frames} frames)")
    return path


def generate_transformative(n_frames: int = 20) -> str:
    """Transformative clip — analysis overlays: arrows, circles, text boxes."""
    path = str(OUTPUT_DIR / "transformative_clip.mp4")
    writer = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"mp4v"), FPS, (FRAME_W, FRAME_H))

    for i in range(n_frames):
        frame = np.zeros((FRAME_H, FRAME_W, 3), dtype=np.uint8)
        _draw_pitch(frame)

        # Analysis title bar (custom, not broadcast)
        cv2.rectangle(frame, (0, 0), (FRAME_W, 40), (40, 40, 100), -1)
        cv2.putText(frame, "TACTICAL ANALYSIS: Bumrah's Yorker Sequence",
                    (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 100), 1)

        # Draw analysis arrows
        arrow_start = (200 + i * 5, 200)
        arrow_end = (320 + i * 3, 150 - i * 2)
        cv2.arrowedLine(frame, arrow_start, arrow_end, (0, 0, 255), 3, tipLength=0.3)

        # Draw highlighting circles
        cv2.circle(frame, (320, 180), 30 + i, (255, 255, 0), 2)
        cv2.circle(frame, (400, 200), 20, (0, 255, 255), 2)

        # Analysis text box
        cv2.rectangle(frame, (10, FRAME_H - 80), (300, FRAME_H - 10), (0, 0, 0), -1)
        cv2.rectangle(frame, (10, FRAME_H - 80), (300, FRAME_H - 10), (255, 255, 100), 1)
        cv2.putText(frame, "Line: Full + Yorker", (20, FRAME_H - 55),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)
        cv2.putText(frame, f"Speed: {145 + i}kph", (20, FRAME_H - 35),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1)
        cv2.putText(frame, "Result: WICKET!", (20, FRAME_H - 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 1)

        # Slow-mo indicator
        cv2.putText(frame, "0.5x SLOW MOTION", (FRAME_W - 200, FRAME_H - 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)

        writer.write(frame)
    writer.release()
    print(f"  [OK] {path} ({n_frames} frames)")
    return path


def generate_meme(n_frames: int = 15) -> str:
    """Meme clip — bold text overlays, saturated colors, reaction template."""
    path = str(OUTPUT_DIR / "meme_clip.mp4")
    writer = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*"mp4v"), FPS, (FRAME_W, FRAME_H))

    meme_texts_top = [
        "POV: DHONI WALKS IN AT 160/5",
        "WHEN THE UMPIRE SAYS",
        "ME WATCHING MY TEAM",
    ]
    meme_texts_bottom = [
        "AND YOU'RE A CSK FAN",
        "\"THAT'S OUT\" (IT WASN'T)",
        "LOSE ANOTHER MATCH",
    ]

    for i in range(n_frames):
        frame = np.zeros((FRAME_H, FRAME_W, 3), dtype=np.uint8)

        # Exaggerated color background — meme aesthetic
        hue_shift = (i * 15) % 180
        frame[:, :] = [hue_shift, 200, 200]
        frame = cv2.cvtColor(frame, cv2.COLOR_HSV2BGR)

        # Low-res feel — add block noise
        block = np.random.randint(0, 30, (FRAME_H // 8, FRAME_W // 8, 3), dtype=np.uint8)
        block = cv2.resize(block, (FRAME_W, FRAME_H), interpolation=cv2.INTER_NEAREST)
        frame = cv2.addWeighted(frame, 0.85, block, 0.15, 0)

        # White top bar with meme text
        cv2.rectangle(frame, (0, 0), (FRAME_W, 60), (255, 255, 255), -1)
        top_text = meme_texts_top[i % len(meme_texts_top)]
        cv2.putText(frame, top_text, (20, 42),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)

        # White bottom bar with meme text
        cv2.rectangle(frame, (0, FRAME_H - 60), (FRAME_W, FRAME_H), (255, 255, 255), -1)
        bot_text = meme_texts_bottom[i % len(meme_texts_bottom)]
        cv2.putText(frame, bot_text, (20, FRAME_H - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)

        # Emoji-like circle face in center
        center = (FRAME_W // 2, FRAME_H // 2)
        cv2.circle(frame, center, 60, (0, 220, 255), -1)
        cv2.circle(frame, center, 60, (0, 180, 220), 3)
        # Eyes
        cv2.circle(frame, (center[0] - 20, center[1] - 15), 8, (0, 0, 0), -1)
        cv2.circle(frame, (center[0] + 20, center[1] - 15), 8, (0, 0, 0), -1)
        # Mouth
        if i % 3 == 0:
            cv2.ellipse(frame, (center[0], center[1] + 20), (25, 15), 0, 0, 180, (0, 0, 0), 2)
        else:
            cv2.ellipse(frame, (center[0], center[1] + 15), (25, 15), 0, 180, 360, (0, 0, 0), 2)

        # Watermark
        cv2.putText(frame, "@cricket_memes_daily", (FRAME_W - 220, FRAME_H - 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 255), 1)

        writer.write(frame)
    writer.release()
    print(f"  [OK] {path} ({n_frames} frames)")
    return path


def main():
    print("=" * 60)
    print("SportsGuard AI — Test Video Generator")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    targets = sys.argv[1:] if len(sys.argv) > 1 else ["official", "piracy", "transformative", "meme"]

    generators = {
        "official": generate_official,
        "piracy": generate_piracy,
        "transformative": generate_transformative,
        "meme": generate_meme,
    }

    for name in targets:
        name = name.lstrip("-").replace("-only", "").strip()
        if name in generators:
            print(f"\nGenerating: {name}")
            generators[name]()
        else:
            print(f"  [SKIP] Unknown target: {name}")

    print(f"\n{'=' * 60}")
    print(f"Done. Videos saved to: {OUTPUT_DIR.resolve()}")
    print("=" * 60)


if __name__ == "__main__":
    main()
