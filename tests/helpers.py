"""
Test Helpers & Infrastructure Utilities for Reddit Shorts Automation E2E Suite.
Provides safe CLI invocation, isolated temporary directories, and dual-engine media probing.
"""

import os
import sys
import json
import shutil
import tempfile
import subprocess
from contextlib import contextmanager

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLI_ENTRYPOINT = os.path.join(PROJECT_ROOT, "src", "main.py")


def run_cli(args, timeout=360, env_overrides=None, cwd=PROJECT_ROOT):
    """
    Executes src/main.py via sys.executable with UTF-8 encoding flags,
    pipe deadlock prevention via background reader threads, and Windows process tree cleanup.
    
    Returns:
        subprocess.CompletedProcess with .returncode, .stdout, .stderr
    """
    cmd = [sys.executable, CLI_ENTRYPOINT] + [str(a) for a in args]
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    if env_overrides:
        env.update(env_overrides)

    p = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=cwd,
        env=env
    )
    try:
        stdout, stderr = p.communicate(timeout=timeout)
        return subprocess.CompletedProcess(cmd, p.returncode, stdout, stderr)
    except subprocess.TimeoutExpired:
        if sys.platform == "win32":
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(p.pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        else:
            p.kill()
        p.communicate()
        raise


@contextmanager
def isolated_output_dir():
    """
    Context manager that creates a temporary isolated output directory
    and recursively removes it upon context exit.
    """
    temp_dir = tempfile.mkdtemp(prefix="shorts_test_")
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


class MediaValidator:
    """
    Inspects and validates media files (MP4, MP3, GIF) using ffprobe
    with graceful fallback to MoviePy to ensure resilience.
    """

    @staticmethod
    def probe_video(file_path):
        """
        Probes an MP4 video file and returns a dictionary with resolution,
        duration, codecs, audio presence, and size.
        """
        if not os.path.exists(file_path):
            return {"valid": False, "error": f"Video file does not exist: {file_path}"}
        if os.path.getsize(file_path) < 10000:
            return {"valid": False, "error": f"Video file too small: {os.path.getsize(file_path)} bytes"}

        # 1. Primary: ffprobe JSON stream extraction
        ffprobe_bin = shutil.which("ffprobe")
        if ffprobe_bin:
            try:
                cmd = [
                    ffprobe_bin,
                    "-v", "quiet",
                    "-print_format", "json",
                    "-show_format",
                    "-show_streams",
                    file_path
                ]
                res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=15)
                if res.returncode == 0:
                    data = json.loads(res.stdout)
                    v_streams = [s for s in data.get("streams", []) if s.get("codec_type") == "video"]
                    a_streams = [s for s in data.get("streams", []) if s.get("codec_type") == "audio"]
                    if not v_streams:
                        return {"valid": False, "error": "No video stream found in media file"}
                    v = v_streams[0]
                    duration = float(data.get("format", {}).get("duration", v.get("duration", 0)))
                    return {
                        "valid": True,
                        "width": int(v.get("width", 0)),
                        "height": int(v.get("height", 0)),
                        "duration": duration,
                        "video_codec": v.get("codec_name"),
                        "has_audio": len(a_streams) > 0,
                        "audio_codec": a_streams[0].get("codec_name") if a_streams else None,
                        "size": int(data.get("format", {}).get("size", os.path.getsize(file_path)))
                    }
            except Exception:
                pass

        # 2. Fallback: MoviePy VideoFileClip
        try:
            from moviepy.editor import VideoFileClip
            clip = VideoFileClip(file_path)
            try:
                has_audio = clip.audio is not None and clip.audio.duration > 0
                return {
                    "valid": True,
                    "width": clip.w,
                    "height": clip.h,
                    "duration": clip.duration,
                    "video_codec": "unknown",
                    "has_audio": has_audio,
                    "audio_codec": "unknown",
                    "size": os.path.getsize(file_path)
                }
            finally:
                clip.close()
                if clip.audio is not None:
                    try:
                        clip.audio.close()
                    except Exception:
                        pass
        except Exception as e:
            return {"valid": False, "error": f"MoviePy probe failed: {e}"}

    @staticmethod
    def probe_audio(file_path):
        """
        Probes an MP3 audio file and returns codec, duration, sample rate,
        channels, and size.
        """
        if not os.path.exists(file_path):
            return {"valid": False, "error": f"Audio file does not exist: {file_path}"}
        if os.path.getsize(file_path) < 1000:
            return {"valid": False, "error": f"Audio file too small: {os.path.getsize(file_path)} bytes"}

        # 1. Primary: ffprobe JSON stream extraction
        ffprobe_bin = shutil.which("ffprobe")
        if ffprobe_bin:
            try:
                cmd = [
                    ffprobe_bin,
                    "-v", "quiet",
                    "-print_format", "json",
                    "-show_format",
                    "-show_streams",
                    file_path
                ]
                res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=15)
                if res.returncode == 0:
                    data = json.loads(res.stdout)
                    a_streams = [s for s in data.get("streams", []) if s.get("codec_type") == "audio"]
                    if not a_streams:
                        return {"valid": False, "error": "No audio stream found in media file"}
                    a = a_streams[0]
                    duration = float(data.get("format", {}).get("duration", a.get("duration", 0)))
                    return {
                        "valid": True,
                        "codec": a.get("codec_name"),
                        "duration": duration,
                        "sample_rate": int(a.get("sample_rate", 0)),
                        "channels": int(a.get("channels", 1)),
                        "size": int(data.get("format", {}).get("size", os.path.getsize(file_path)))
                    }
            except Exception:
                pass

        # 2. Fallback: MoviePy AudioFileClip
        try:
            from moviepy.editor import AudioFileClip
            clip = AudioFileClip(file_path)
            try:
                return {
                    "valid": True,
                    "codec": "unknown",
                    "duration": clip.duration,
                    "sample_rate": clip.fps,
                    "channels": clip.nchannels,
                    "size": os.path.getsize(file_path)
                }
            finally:
                clip.close()
        except Exception as e:
            return {"valid": False, "error": f"MoviePy audio probe failed: {e}"}
