"""
Empirical Stress & Edge-Case Harness for scripts/generate_demo_gif.py (Iteration 2)
Author: Challenger 1 (critic, specialist)
"""

import os
import sys
import shutil
import tempfile
import subprocess
from unittest.mock import patch

sys.path.insert(0, os.path.abspath("."))
import scripts.generate_demo_gif as gen_gif


def test_deep_nested_output_directory():
    print("--- STRESS TEST 1: Deep Nested Output Directory ---")
    temp_dir = tempfile.mkdtemp(prefix="test_deep_")
    try:
        nested_out = os.path.join(temp_dir, "a", "b", "c", "d", "demo.gif")
        res = gen_gif.generate_demo_gif(
            video_path="output/final_video_AITAH.mp4",
            output_gif=nested_out,
            duration=0.5,
            fps=8,
            width=160,
            height=284,
        )
        assert res is True, "Deep nested output generation failed"
        assert os.path.exists(nested_out), "Nested output file does not exist"
        print(f"  [PASS] Deep nested directory auto-created: {nested_out}")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_absolute_output_path():
    print("--- STRESS TEST 2: Absolute Path Output ---")
    temp_dir = tempfile.mkdtemp(prefix="test_abs_")
    try:
        abs_out = os.path.abspath(os.path.join(temp_dir, "absolute_demo.gif"))
        res = gen_gif.generate_demo_gif(
            video_path=os.path.abspath("output/final_video_AITAH.mp4"),
            output_gif=abs_out,
            duration=0.5,
            fps=8,
            width=160,
            height=284,
        )
        assert res is True, "Absolute path output generation failed"
        assert os.path.exists(abs_out), "Absolute output file does not exist"
        print(f"  [PASS] Absolute path handled cleanly: {abs_out}")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_corrupt_video_file_graceful_failure():
    print("--- STRESS TEST 3: Corrupt Video File (0 bytes) Graceful Handling ---")
    temp_dir = tempfile.mkdtemp(prefix="test_corrupt_")
    try:
        corrupt_mp4 = os.path.join(temp_dir, "corrupt.mp4")
        with open(corrupt_mp4, "wb") as f:
            f.write(b"NOT_A_VALID_MP4_HEADER")
        
        target_gif = os.path.join(temp_dir, "out.gif")
        res = gen_gif.generate_demo_gif(
            video_path=corrupt_mp4,
            output_gif=target_gif,
            duration=0.5,
        )
        assert res is False, "Expected False for corrupt video input"
        assert not os.path.exists(target_gif), "Corrupt input should not produce a valid output GIF"
        print("  [PASS] Corrupt video correctly rejected by FFmpeg and returns False without unhandled exception")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_missing_ffmpeg_binary_mock():
    print("--- STRESS TEST 4: Missing FFmpeg Binary Graceful Handling ---")
    with patch("subprocess.run", side_effect=FileNotFoundError("ffmpeg not found")):
        res = gen_gif.generate_demo_gif(video_path="output/final_video_AITAH.mp4")
        assert res is False, "Expected False when ffmpeg executable is missing"
        print("  [PASS] Missing FFmpeg binary handled gracefully with False return")


def test_size_ceiling_exceeded_guard():
    print("--- STRESS TEST 5: Size Ceiling Exceeded (> 5.0 MB) Guard ---")
    # Simulate a generated file that exceeds 5.0 MB
    with patch("subprocess.run") as mock_run, \
         patch("os.path.exists", return_value=True), \
         patch("os.path.getsize", return_value=6 * 1024 * 1024):
        mock_run.return_value.returncode = 0
        res = gen_gif.generate_demo_gif(
            video_path="output/final_video_AITAH.mp4",
            output_gif="fake_large.gif",
        )
        assert res is False, "Expected False when output exceeds 5 MB"
        print("  [PASS] Size threshold guard (> 5 MB) correctly triggers False return")


def test_candidate_sorting_by_size():
    print("--- STRESS TEST 6: Candidate Discovery Sorts by Size Descending ---")
    temp_dir = tempfile.mkdtemp(prefix="test_cand_")
    orig_cwd = os.getcwd()
    try:
        os.chdir(temp_dir)
        os.makedirs("output", exist_ok=True)
        # Create a tiny 100 byte mp4 and a larger 1000 byte mp4
        small_mp4 = os.path.join("output", "a_small.mp4")
        large_mp4 = os.path.join("output", "z_large.mp4")
        with open(small_mp4, "wb") as f:
            f.write(b"0" * 100)
        with open(large_mp4, "wb") as f:
            f.write(b"0" * 1000)
        
        # Call generate_demo_gif with nonexistent default
        # We patch subprocess.run to verify which candidate was passed to ffmpeg
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            # Let real os.path.getsize inspect the real temp files
            gen_gif.generate_demo_gif(video_path="output/default_missing.mp4", output_gif="demo.gif")
            called_cmd = mock_run.call_args[0][0]
            i_idx = called_cmd.index("-i")
            chosen_input = called_cmd[i_idx + 1]
            assert chosen_input == large_mp4, f"Expected largest candidate {large_mp4}, got {chosen_input}"
            print(f"  [PASS] Candidate discovery correctly picked largest candidate: {chosen_input}")
    finally:
        os.chdir(orig_cwd)
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_process_leak_audit():
    print("--- STRESS TEST 7: Process Lifecycle & Leak Check ---")
    ps_cmd = 'Get-Process -Name ffmpeg,python -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id'
    out = subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True, text=True)
    # Check that no orphan background ffmpeg process is hanging
    ps_ffmpeg = 'Get-Process -Name ffmpeg -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id'
    out_ff = subprocess.run(["powershell", "-Command", ps_ffmpeg], capture_output=True, text=True)
    ff_pids = out_ff.stdout.strip().split()
    assert len(ff_pids) == 0, f"Lingering FFmpeg processes detected: {ff_pids}"
    print("  [PASS] Zero orphan FFmpeg processes.")


if __name__ == "__main__":
    test_deep_nested_output_directory()
    test_absolute_output_path()
    test_corrupt_video_file_graceful_failure()
    test_missing_ffmpeg_binary_mock()
    test_size_ceiling_exceeded_guard()
    test_candidate_sorting_by_size()
    test_process_leak_audit()
    print("\n=======================================================")
    print("ALL ADVERSARIAL STRESS TESTS PASSED SUCCESSFULLY!")
    print("=======================================================")
