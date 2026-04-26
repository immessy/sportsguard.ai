from __future__ import annotations

from pathlib import Path

import cv2
import imagehash
from PIL import Image


def _frame_positions(frame_count: int) -> list[int]:
    if frame_count <= 0:
        return [0, 1, 2]
    if frame_count == 1:
        return [0, 0, 0]
    if frame_count == 2:
        return [0, 1, 1]
    return [0, frame_count // 2, frame_count - 1]


def extract_and_hash_video(video_path: str) -> list[str]:
    video_file = Path(video_path)
    if not video_file.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")

    capture = cv2.VideoCapture(str(video_file))
    if not capture.isOpened():
        raise ValueError(f"Unable to open video: {video_path}")

    hashes: list[str] = []

    try:
        frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        for frame_index in _frame_positions(frame_count):
            capture.set(cv2.CAP_PROP_POS_FRAMES, max(frame_index, 0))
            success, frame = capture.read()
            if not success or frame is None:
                continue

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_image = Image.fromarray(rgb_frame)
            hashes.append(str(imagehash.phash(frame_image)))
    finally:
        capture.release()

    if not hashes:
        raise ValueError(f"No frames could be extracted from: {video_path}")

    while len(hashes) < 3:
        hashes.append(hashes[-1])

    return hashes[:3]


def hash_image(image_path: str) -> str:
    image_file = Path(image_path)
    if not image_file.exists():
        raise FileNotFoundError(f"Image not found: {image_path}")

    with Image.open(image_file) as image:
        return str(imagehash.phash(image.convert("RGB")))


def compare_hashes(hash1: str, hash2: str) -> int:
    return imagehash.hex_to_hash(hash1) - imagehash.hex_to_hash(hash2)
