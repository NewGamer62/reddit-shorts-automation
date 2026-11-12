"""
Generate optimized demo.gif for GitHub README and portfolio presentation.
Extracts a short, crisp snippet of the rendered vertical short video using FFmpeg.
"""

import os
import subprocess
import sys


def generate_demo_gif(
    video_path="output/final_video_AITAH.mp4",
    output_gif="docs/demo.gif",
    duration=3.5,
    fps=12,
    width=320,
    height=568,
    start_time="00:00:00",
    max_colors=128,
    bayer_scale=4,
):
    """
    Renders an optimized, animated GIF using FFmpeg two-pass palette generation.

    Args:
        video_path (str): Path to the source MP4 video.
        output_gif (str): Destination path for the generated GIF.
        duration (float): Duration in seconds to extract.
        fps (int): Frame rate of the output GIF.
        width (int): Pixel width (320 for 9:16 vertical shorts).
        height (int): Pixel height (568 for 9:16 vertical shorts).
        start_time (str): Timestamp offset in HH:MM:SS.
        max_colors (int): Palette color depth (128 for optimal compression).
        bayer_scale (int): Dither scale for Bayer dithering.

    Returns:
        bool: True if generation succeeded and file size < 5 MB, False otherwise.
    """
    if not os.path.exists(video_path):
        candidates = []
        if os.path.exists("output") and os.path.isdir("output"):
            try:
                candidates = [
                    os.path.join("output", f)
                    for f in os.listdir("output")
                    if f.endswith(".mp4")
                ]
                candidates.sort(key=os.path.getsize, reverse=True)
            except (FileNotFoundError, OSError):
                candidates = []
        if not candidates:
            print(f"Error: No source video found at {video_path} or in output/")
            return False
        video_path = candidates[0]
        print(f"Using fallback source video: {video_path}")

    parent_dir = os.path.dirname(output_gif)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)

    filter_complex = (
        f"fps={fps},scale={width}:{height}:flags=lanczos,split[s0][s1];"
        f"[s0]palettegen=max_colors={max_colors}:stats_mode=diff[p];"
        f"[s1][p]paletteuse=dither=bayer:bayer_scale={bayer_scale}:diff_mode=rectangle"
    )

    cmd = [
        "ffmpeg",
        "-y",
        "-ss",
        str(start_time),
        "-t",
        str(duration),
        "-i",
        video_path,
        "-vf",
        filter_complex,
        "-loop",
        "0",
        output_gif,
    ]

    print(
        f"Generating optimized GIF: {output_gif} ({width}x{height} @ {fps}fps, {duration}s)..."
    )
    print(f"Command: {' '.join(cmd)}")

    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError:
        print("Error: 'ffmpeg' executable not found in system PATH.")
        return False

    if res.returncode == 0 and os.path.exists(output_gif):
        file_size_bytes = os.path.getsize(output_gif)
        size_mb = file_size_bytes / (1024 * 1024)
        print(f"Success! {output_gif} generated: {size_mb:.2f} MB ({file_size_bytes} bytes).")
        if size_mb > 5.0:
            print(f"Warning: GIF size exceeds 5 MB threshold ({size_mb:.2f} MB).")
            return False
        return True
    else:
        stderr_msg = res.stderr.decode("utf-8", errors="ignore")
        print(f"FFmpeg failed with return code {res.returncode}:\n{stderr_msg}")
        return False


if __name__ == "__main__":
    success = generate_demo_gif()
    sys.exit(0 if success else 1)
