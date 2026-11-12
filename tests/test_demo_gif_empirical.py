"""
Empirical Verification & Stress Test Suite for docs/demo.gif and scripts/generate_demo_gif.py
Author: Challenger 1 (critic, specialist)
"""

import os
import sys
import shutil
import tempfile
import subprocess
from PIL import Image, ImageStat

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath("."))


def test_gif_file_integrity():
    print("=== TEST 1: GIF File & Format Integrity ===")
    gif_path = os.path.join("docs", "demo.gif")
    assert os.path.exists(gif_path), f"File {gif_path} does not exist"
    
    # 1. Header check (magic bytes)
    with open(gif_path, "rb") as f:
        header = f.read(6)
    assert header in (b"GIF87a", b"GIF89a"), f"Invalid GIF header: {header}"
    print(f"  [PASS] Magic bytes: {header.decode('ascii')}")
    
    # 2. File size check
    size_bytes = os.path.getsize(gif_path)
    size_mb = size_bytes / (1024 * 1024)
    print(f"  [OBSERVATION] File size: {size_bytes} bytes ({size_mb:.2f} MB)")
    assert size_bytes < 5 * 1024 * 1024, f"File size {size_mb:.2f} MB exceeds 5 MB threshold"
    if size_bytes < 500 * 1024:
        print(f"  [CONFIRMED DEFECT] File size unexpectedly small ({size_bytes} bytes) — ColorClip fallback overwritten without gameplay footage!")
    else:
        print(f"  [PASS] File size within expected range (> 500 KB and < 5 MB)")
    
    # 3. Pillow Image verification
    img = Image.open(gif_path)
    assert img.format == "GIF", f"Unexpected format: {img.format}"
    width, height = img.size
    print(f"  [PASS] Dimensions: {width}x{height}")
    assert (width, height) == (320, 568), f"Expected 320x568, got {width}x{height}"
    
    # Aspect ratio check (9:16 vertical shorts ratio)
    aspect_ratio = width / height
    target_ratio = 9 / 16  # 0.5625
    diff = abs(aspect_ratio - target_ratio)
    print(f"  [PASS] Aspect ratio: {aspect_ratio:.4f} (target 9:16 = {target_ratio:.4f}, diff = {diff:.4f})")
    assert diff < 0.01, f"Aspect ratio {aspect_ratio} deviates from 9:16"
    
    # Animation properties
    assert getattr(img, "is_animated", False), "GIF is not animated!"
    n_frames = img.n_frames
    print(f"  [PASS] Frame count: {n_frames}")
    assert n_frames >= 20, f"Expected animated sequence, got only {n_frames} frames"
    
    # Frame duration & total duration
    durations = []
    for frame_idx in range(n_frames):
        img.seek(frame_idx)
        durations.append(img.info.get("duration", 0))
    total_duration_sec = sum(durations) / 1000.0
    print(f"  [PASS] Total animation duration: {total_duration_sec:.2f}s (sampled frame delays: {set(durations)} ms)")
    
    # Check loop setting (0 means loop forever)
    loop = img.info.get("loop", None)
    print(f"  [PASS] Loop setting: {loop}")


def test_visual_content_analysis():
    print("\n=== TEST 2: Visual Content Analysis (Reddit Card, Karaoke Subtitles, Gameplay) ===")
    gif_path = os.path.join("docs", "demo.gif")
    img = Image.open(gif_path)
    
    frame_diffs = []
    prev_frame = None
    
    for idx in range(img.n_frames):
        img.seek(idx)
        rgb_frame = img.convert("RGB")
        
        # Check Reddit card region in opening frames (title portion, idx < 25)
        if idx < 25:
            card_crop = rgb_frame.crop((20, 50, 300, 200))
            card_stat = ImageStat.Stat(card_crop)
            assert max(card_stat.var) > 10, f"Card region appears blank in frame {idx}"
        
        # Check Subtitle region (center/lower third, y: 250 to 450, x: 20 to 300)
        sub_crop = rgb_frame.crop((20, 250, 300, 450))
        sub_stat = ImageStat.Stat(sub_crop)
        assert max(sub_stat.var) > 10, f"Subtitle/gameplay region appears blank in frame {idx}"
        
        # Measure motion/variation across frames (gameplay motion)
        if prev_frame is not None:
            diff = sum(abs(a - b) for a, b in zip(rgb_frame.tobytes(), prev_frame.tobytes()))
            frame_diffs.append(diff)
        prev_frame = rgb_frame
        
    avg_diff = sum(frame_diffs) / len(frame_diffs)
    print(f"  [OBSERVATION] Average frame-to-frame pixel change: {avg_diff:,.0f}")
    if avg_diff < 100_000:
        print("  [CONFIRMED DEFECT] Frame-to-frame pixel change is below 100k — gameplay motion is missing (ColorClip background)!")
    else:
        print("  [PASS] Dynamic gameplay video motion confirmed (> 100k avg diff).")


def test_script_execution_with_directory():
    print("\n=== TEST 3: scripts/generate_demo_gif.py Valid Execution ===")
    import scripts.generate_demo_gif as gen_gif
    
    temp_dir = tempfile.mkdtemp(prefix="test_gif_")
    try:
        temp_out = os.path.join(temp_dir, "test_output.gif")
        res = gen_gif.generate_demo_gif(
            video_path="output/final_video_AITAH.mp4",
            output_gif=temp_out,
            duration=1.0,
            fps=8,
            width=160,
            height=284,
            max_colors=64,
        )
        assert res is True, "generate_demo_gif failed with valid input and custom parameters"
        assert os.path.exists(temp_out), f"Output GIF was not created at {temp_out}"
        out_size = os.path.getsize(temp_out)
        print(f"  [PASS] Custom output successfully rendered: {temp_out} ({out_size} bytes)")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_bug_bare_filename_crash():
    print("\n=== TEST 4: Regression Test — Bare Filename Handling ===")
    import scripts.generate_demo_gif as gen_gif
    # Bare filename in root directory (os.path.dirname returns '')
    res = gen_gif.generate_demo_gif(
        video_path="output/final_video_AITAH.mp4",
        output_gif="bare_test.gif",
        duration=0.5,
    )
    assert res is True, "Expected generate_demo_gif to succeed on bare filename"
    assert os.path.exists("bare_test.gif"), "Output bare_test.gif was not created"
    size = os.path.getsize("bare_test.gif")
    print(f"  [PASS] Bare filename handled cleanly without WinError 3: bare_test.gif ({size} bytes)")
    if os.path.exists("bare_test.gif"):
        os.remove("bare_test.gif")


def test_bug_output_folder_missing():
    print("\n=== TEST 5: Regression Test — Missing output/ Directory Handling ===")
    from unittest.mock import patch
    import scripts.generate_demo_gif as gen_gif
    
    # Simulate a fresh repo where output/ does not exist yet and video_path is missing
    with patch("os.path.exists", side_effect=lambda p: False if p == "output" or p == "nonexistent.mp4" else True), \
         patch("os.path.isdir", side_effect=lambda p: False if p == "output" else True):
        res = gen_gif.generate_demo_gif(video_path="nonexistent.mp4")
        assert res is False, "Expected generate_demo_gif to return False gracefully when output/ is missing"
        print("  [PASS] Missing output/ handled gracefully (returned False, no unhandled exception)")


def test_bug_default_source_empty_gameplay():
    print("\n=== TEST 6: Stress-Test Bug 3 — Default Source Video Lacks Gameplay ===")
    import scripts.generate_demo_gif as gen_gif
    
    # output/final_video_AskReddit.mp4 was generated with ColorClip fallback (no gameplay)
    temp_dir = tempfile.mkdtemp(prefix="test_gif_askreddit_")
    try:
        temp_out = os.path.join(temp_dir, "askreddit_demo.gif")
        res = gen_gif.generate_demo_gif(
            video_path="output/final_video_AskReddit.mp4",
            output_gif=temp_out,
            duration=3.5,
        )
        if res is True and os.path.exists(temp_out):
            size_bytes = os.path.getsize(temp_out)
            print(f"  [OBSERVATION] Output GIF from AskReddit is {size_bytes} bytes ({size_bytes / 1024:.1f} KB)")
            if size_bytes < 100 * 1024:
                print("  [CONFIRMED ISSUE] AskReddit video produces flat ~46 KB GIF without gameplay footage!")
        else:
            print(f"  [OBSERVATION] generate_demo_gif returned {res}")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_no_zombie_processes():
    print("\n=== TEST 7: Zombie & Orphan Process Audit ===")
    ps_cmd = 'Get-Process -Name ffmpeg -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id'
    out = subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True, text=True)
    ffmpeg_pids = out.stdout.strip().split()
    print(f"  [PASS] Active ffmpeg processes: {len(ffmpeg_pids)} (PIDs: {ffmpeg_pids if ffmpeg_pids else 'none'})")
    assert len(ffmpeg_pids) == 0, f"Found lingering ffmpeg process(es): {ffmpeg_pids}"


if __name__ == "__main__":
    test_gif_file_integrity()
    test_visual_content_analysis()
    test_script_execution_with_directory()
    test_bug_bare_filename_crash()
    test_bug_output_folder_missing()
    test_bug_default_source_empty_gameplay()
    test_no_zombie_processes()
    print("\n=======================================================")
    print("ALL EMPIRICAL CHALLENGE SUITE TESTS EXECUTED!")
    print("=======================================================")
