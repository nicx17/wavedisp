import subprocess
from pathlib import Path

import cv2
import numpy as np

VIDEO_URL = "https://www.youtube.com/watch?v=FtutLA63Cp8"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_BIN = PROJECT_ROOT / "backend" / "bad_apple.bin"
TEMP_VIDEO = PROJECT_ROOT / "temp_bad_apple.mp4"


def download_video():
    if not TEMP_VIDEO.exists():
        print("Downloading high-quality Bad Apple video...")
        subprocess.run(
            [
                "yt-dlp",
                "-f",
                "bestvideo[height<=480][ext=mp4]+bestaudio/best[height<=480][ext=m4a]/best",
                "--merge-output-format",
                "mp4",
                "-o",
                str(TEMP_VIDEO),
                VIDEO_URL,
            ],
            check=True,
        )


def process_video():
    print(f"Processing video into {OUTPUT_BIN}...")
    cap = cv2.VideoCapture(str(TEMP_VIDEO))
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    print(f"Total frames: {frame_count}, FPS: {fps}")

    OUTPUT_BIN.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_BIN, "wb") as f:
        count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Convert to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            h, w = gray.shape

            # Center crop to 1:1 aspect ratio
            size = min(h, w)
            y_off = (h - size) // 2
            x_off = (w - size) // 2
            cropped = gray[y_off : y_off + size, x_off : x_off + size]

            # Resize to 64x64
            resized = cv2.resize(cropped, (64, 64), interpolation=cv2.INTER_AREA)

            # Threshold to pure black and white (0 or 1)
            # Use Otsu's thresholding for optimal separation
            _, bw = cv2.threshold(resized, 0, 1, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # Pack 64x64 array of 0s and 1s into bits (512 bytes per frame)
            packed = np.packbits(bw.flatten())
            f.write(packed.tobytes())

            count += 1
            if count % 500 == 0:
                print(f"Processed {count}/{frame_count} frames")

    cap.release()
    print(f"Done! Wrote {count} frames to {OUTPUT_BIN}.")


if __name__ == "__main__":
    download_video()
    process_video()
