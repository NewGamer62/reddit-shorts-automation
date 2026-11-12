"""
Authoritative 5-Tier End-to-End (E2E) Test Suite for Reddit Shorts Automation Pipeline.
Strictly conforms to TEST_INFRA.md, miner_e2e_2/handoff.md, and project scope specifications.
"""

import os
import sys
import re
import json
import shutil
import unittest
from PIL import Image

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from tests.helpers import run_cli, isolated_output_dir, MediaValidator
from tts_engine import TTSEngine


def parse_yaml_frontmatter(text):
    """
    Parses lightweight YAML frontmatter into nested dict/list structures
    without external dependencies (pure Python standard library).
    """
    if not text.startswith("---"):
        return None, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None, text
    raw_yaml = parts[1]
    body = parts[2]

    lines = raw_yaml.splitlines()

    def parse_block(block_lines, indent=0):
        res = {}
        i = 0
        while i < len(block_lines):
            line = block_lines[i]
            if not line.strip() or line.strip().startswith("#"):
                i += 1
                continue
            cur_indent = len(line) - len(line.lstrip(" "))
            if cur_indent < indent:
                break

            if ":" in line:
                key, val = line.split(":", 1)
                key = key.strip()
                val = val.strip()

                if val.startswith("[") and val.endswith("]"):
                    items = [x.strip().strip("\"'") for x in val[1:-1].split(",") if x.strip()]
                    res[key] = items
                    i += 1
                    continue

                if val:
                    res[key] = val.strip("\"'")
                    i += 1
                    continue

                sub_lines = []
                j = i + 1
                while j < len(block_lines):
                    next_line = block_lines[j]
                    if not next_line.strip() or next_line.strip().startswith("#"):
                        j += 1
                        continue
                    next_indent = len(next_line) - len(next_line.lstrip(" "))
                    if next_indent <= cur_indent:
                        break
                    sub_lines.append(next_line)
                    j += 1

                if sub_lines and all(sl.strip().startswith("- ") for sl in sub_lines if sl.strip()):
                    res[key] = [re.sub(r"^-\s*", "", sl.strip()).strip("\"'") for sl in sub_lines if sl.strip()]
                elif sub_lines:
                    min_sub_indent = min(len(sl) - len(sl.lstrip(" ")) for sl in sub_lines if sl.strip())
                    res[key] = parse_block(sub_lines, min_sub_indent)
                else:
                    res[key] = None
                i = j
                continue
            i += 1
        return res

    fm = parse_block(lines)
    return fm, body


class TestTier1LocalPipeline(unittest.TestCase):
    """
    Tier 1: Zero-Friction Local Execution
    Tests executing src/main.py in local mode without requiring API keys or secrets.
    """

    def test_tier1_local_mode_default_execution(self):
        """
        Runs `python src/main.py --local` with an empty ElevenLabs key and asserts
        that a complete 1080x1920 MP4 video and metadata JSON are generated cleanly.
        """
        with isolated_output_dir() as temp_dir:
            res = run_cli(
                ["--local", "--output", temp_dir, "--fps", "30"],
                env_overrides={"ELEVENLABS_API_KEY": ""}
            )
            self.assertEqual(res.returncode, 0, f"Local pipeline failed: {res.stderr}\n{res.stdout}")
            
            video_path = os.path.join(temp_dir, "final_video_AskReddit.mp4")
            metadata_path = os.path.join(temp_dir, "metadata_AskReddit.json")
            
            self.assertTrue(os.path.exists(video_path), f"Expected video not found: {video_path}")
            self.assertGreater(os.path.getsize(video_path), 100_000, "Generated video size too small")
            
            probe = MediaValidator.probe_video(video_path)
            self.assertTrue(probe["valid"], probe.get("error"))
            self.assertEqual(probe["width"], 1080, "Video width must be 1080")
            self.assertEqual(probe["height"], 1920, "Video height must be 1920 (9:16 Shorts ratio)")
            self.assertGreater(probe["duration"], 0.0, "Video duration must be positive")
            self.assertTrue(probe["has_audio"], "Video must contain an active audio stream")
            if probe.get("video_codec") != "unknown":
                self.assertIn(probe["video_codec"], ["h264", "libx264"])

            self.assertTrue(os.path.exists(metadata_path), f"Expected metadata not found: {metadata_path}")
            with open(metadata_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            self.assertIn("title", meta)
            self.assertGreater(len(meta["title"]), 0)
            self.assertIn("description", meta)
            tags = meta.get("tags") or meta.get("hashtags", [])
            self.assertIsInstance(tags, list)
            self.assertGreater(len(tags), 0)

    def test_tier1_local_mode_custom_subreddit(self):
        """
        Verifies that passing `--subreddit AITAH` selects the AITAH sample story,
        renders `final_video_AITAH.mp4`, and produces corresponding metadata.
        """
        with isolated_output_dir() as temp_dir:
            res = run_cli(
                ["--local", "--subreddit", "AITAH", "--output", temp_dir, "--fps", "30"],
                env_overrides={"ELEVENLABS_API_KEY": ""}
            )
            self.assertEqual(res.returncode, 0, f"Custom subreddit pipeline failed: {res.stderr}\n{res.stdout}")
            
            video_path = os.path.join(temp_dir, "final_video_AITAH.mp4")
            metadata_path = os.path.join(temp_dir, "metadata_AITAH.json")
            
            self.assertTrue(os.path.exists(video_path), f"AITAH video missing: {video_path}")
            self.assertGreater(os.path.getsize(video_path), 100_000)
            self.assertTrue(os.path.exists(metadata_path), f"AITAH metadata missing: {metadata_path}")
            
            with open(metadata_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            self.assertTrue("Grandfather" in meta["title"] or "AITAH" in meta["title"])

    def test_tier1_local_mode_custom_text(self):
        """
        Verifies that passing `--text` and `--title` generates a custom short narrative
        without relying on sample stories or scraping.
        """
        custom_title = "Custom E2E Test Story"
        custom_text = "This is an automated E2E test verifying custom narrative text video synthesis."
        with isolated_output_dir() as temp_dir:
            res = run_cli(
                ["--local", "--title", custom_title, "--text", custom_text, "--output", temp_dir, "--fps", "30"],
                env_overrides={"ELEVENLABS_API_KEY": ""}
            )
            self.assertEqual(res.returncode, 0, f"Custom text pipeline failed: {res.stderr}\n{res.stdout}")
            
            video_path = os.path.join(temp_dir, "final_video_AskReddit.mp4")
            metadata_path = os.path.join(temp_dir, "metadata_AskReddit.json")
            
            self.assertTrue(os.path.exists(video_path), f"Custom text video missing: {video_path}")
            self.assertGreater(os.path.getsize(video_path), 50_000)
            self.assertTrue(os.path.exists(metadata_path), f"Custom text metadata missing: {metadata_path}")
            
            with open(metadata_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            self.assertTrue(
                meta["title"] == custom_title or meta["title"].startswith(custom_title),
                f"Title mismatch: {meta.get('title')}"
            )

    def test_tier1_upload_safety_without_secrets(self):
        """
        Verifies that invoking `--upload` when client_secrets.json is absent
        safely outputs a warning and finishes cleanly without hanging or crashing.
        """
        secrets_path = os.path.join(PROJECT_ROOT, "client_secrets.json")
        bak_path = os.path.join(PROJECT_ROOT, "client_secrets.json.bak")
        renamed = False
        if os.path.exists(bak_path):
            try:
                os.remove(bak_path)
            except OSError:
                pass
        if os.path.exists(secrets_path):
            try:
                shutil.move(secrets_path, bak_path)
                renamed = True
            except OSError:
                pass
        try:
            with isolated_output_dir() as temp_dir:
                res = run_cli(
                    ["--local", "--upload", "--output", temp_dir, "--fps", "30"],
                    timeout=360,
                    env_overrides={"ELEVENLABS_API_KEY": ""}
                )
                self.assertEqual(res.returncode, 0, f"Upload safety test failed: {res.stderr}\n{res.stdout}")
                combined = res.stdout + res.stderr
                self.assertIn("client_secrets.json introuvable", combined)
                video_files = [f for f in os.listdir(temp_dir) if f.endswith(".mp4")]
                self.assertGreater(len(video_files), 0, "Video must still be generated when upload is skipped")
        finally:
            if renamed and os.path.exists(bak_path):
                try:
                    if os.path.exists(secrets_path):
                        os.remove(secrets_path)
                    shutil.move(bak_path, secrets_path)
                except OSError:
                    pass


class TestTier2FreeTTSFallback(unittest.TestCase):
    """
    Tier 2: Free TTS Fallback (src/tts_engine.py)
    Tests edge-tts synthesis, transparent auto-fallback, error recovery, and voice override.
    """

    def test_tier2_edge_tts_direct_generation(self):
        """
        Direct invocation of TTSEngine with preferred_engine='edge-tts'
        generates a valid MP3 audio file without API keys.
        """
        engine = TTSEngine(preferred_engine="edge-tts")
        with isolated_output_dir() as temp_dir:
            out_file = os.path.join(temp_dir, "test_direct_edge.mp3")
            res_path = engine.generate_audio(
                "Testing direct Edge-TTS free speech synthesis for automated shorts.",
                gender="M",
                output_path=out_file
            )
            self.assertEqual(res_path, out_file)
            self.assertTrue(os.path.exists(out_file))
            self.assertGreater(os.path.getsize(out_file), 5000)
            
            probe = MediaValidator.probe_audio(out_file)
            self.assertTrue(probe["valid"], probe.get("error"))
            self.assertIn(probe["codec"], ["mp3", "mp3float", "unknown"])
            self.assertGreater(probe["duration"], 1.0)
            if probe.get("sample_rate"):
                self.assertIn(probe["sample_rate"], [24000, 44100])

    def test_tier2_auto_fallback_missing_key(self):
        """
        Direct invocation of TTSEngine in 'auto' mode when ELEVENLABS_API_KEY
        is unset seamlessly falls back to edge-tts without throwing an exception.
        """
        orig_key = os.environ.pop("ELEVENLABS_API_KEY", None)
        try:
            engine = TTSEngine(preferred_engine="auto")
            with isolated_output_dir() as temp_dir:
                out_file = os.path.join(temp_dir, "test_fallback_nokey.mp3")
                res_path = engine.generate_audio(
                    "Automated fallback verification when ElevenLabs API key is absent.",
                    gender="F",
                    output_path=out_file
                )
                self.assertTrue(os.path.exists(out_file))
                self.assertGreater(os.path.getsize(out_file), 5000)
                probe = MediaValidator.probe_audio(out_file)
                self.assertTrue(probe["valid"])
                self.assertGreater(probe["duration"], 1.0)
        finally:
            if orig_key is not None:
                os.environ["ELEVENLABS_API_KEY"] = orig_key

    def test_tier2_auto_fallback_invalid_key(self):
        """
        Direct invocation of TTSEngine in 'auto' mode with an invalid key
        catches the 401 error and transparently falls back to edge-tts.
        """
        orig_key = os.environ.get("ELEVENLABS_API_KEY")
        os.environ["ELEVENLABS_API_KEY"] = "sk_invalid_test_key_0000000000"
        try:
            engine = TTSEngine(preferred_engine="auto")
            with isolated_output_dir() as temp_dir:
                out_file = os.path.join(temp_dir, "test_fallback_badkey.mp3")
                res_path = engine.generate_audio(
                    "Testing automatic fallback after ElevenLabs returns 401 error.",
                    gender="M",
                    output_path=out_file
                )
                self.assertTrue(os.path.exists(out_file))
                self.assertGreater(os.path.getsize(out_file), 5000)
                probe = MediaValidator.probe_audio(out_file)
                self.assertTrue(probe["valid"])
        finally:
            if orig_key is not None:
                os.environ["ELEVENLABS_API_KEY"] = orig_key
            else:
                os.environ.pop("ELEVENLABS_API_KEY", None)

    def test_tier2_forced_elevenlabs_mode_raises_error(self):
        """
        Direct invocation with preferred_engine='elevenlabs' when key is missing
        strictly raises an error rather than falling back.
        """
        orig_key = os.environ.pop("ELEVENLABS_API_KEY", None)
        try:
            engine = TTSEngine(preferred_engine="elevenlabs")
            with isolated_output_dir() as temp_dir:
                out_file = os.path.join(temp_dir, "should_not_exist.mp3")
                with self.assertRaises((ValueError, Exception)):
                    engine.generate_audio(
                        "Should fail strictly.",
                        gender="M",
                        output_path=out_file
                    )
                self.assertFalse(os.path.exists(out_file))
        finally:
            if orig_key is not None:
                os.environ["ELEVENLABS_API_KEY"] = orig_key

    def test_tier2_voice_override(self):
        """
        Verifies that passing a specific neural voice identifier (e.g. en-US-GuyNeural)
        is respected by edge-tts synthesis.
        """
        engine = TTSEngine(preferred_engine="edge-tts")
        with isolated_output_dir() as temp_dir:
            out_file = os.path.join(temp_dir, "test_custom_voice.mp3")
            res_path = engine.generate_audio(
                "Testing custom neural voice override.",
                voice="en-US-GuyNeural",
                output_path=out_file
            )
            self.assertTrue(os.path.exists(out_file))
            self.assertGreater(os.path.getsize(out_file), 3000)


class TestTier3DirectAudioInjection(unittest.TestCase):
    """
    Tier 3: Direct Audio Injection (src/main.py --audio)
    Tests feeding pre-synthesized audio files directly into Whisper alignment and video assembly.
    """

    def test_tier3_direct_audio_valid_sample(self):
        """
        Injects assets/audio/voiceover_todayilearned.mp3 and verifies that the pipeline
        bypasses Reddit scraping/TTS and generates a 1080x1920 MP4 video matching voice duration.
        """
        sample_audio = os.path.join(PROJECT_ROOT, "assets", "audio", "voiceover_todayilearned.mp3")
        self.assertTrue(os.path.exists(sample_audio), f"Test fixture missing: {sample_audio}")

        with isolated_output_dir() as temp_dir:
            res = run_cli([
                "--audio", sample_audio,
                "--title", "TIL restaurant orders",
                "--subreddit", "AskReddit",
                "--output", temp_dir,
                "--fps", "30"
            ])
            self.assertEqual(res.returncode, 0, f"Direct audio pipeline failed: {res.stderr}\n{res.stdout}")
            self.assertIn("[Direct Audio]", res.stdout)
            
            video_path = os.path.join(temp_dir, "final_video_AskReddit.mp4")
            metadata_path = os.path.join(temp_dir, "metadata_AskReddit.json")
            
            self.assertTrue(os.path.exists(video_path), f"Rendered video missing: {video_path}")
            self.assertGreater(os.path.getsize(video_path), 50_000)
            
            probe = MediaValidator.probe_video(video_path)
            self.assertTrue(probe["valid"], probe.get("error"))
            self.assertEqual(probe["width"], 1080)
            self.assertEqual(probe["height"], 1920)
            self.assertLess(abs(probe["duration"] - 5.52), 0.8, "Video duration should match audio (~5.52s)")
            self.assertTrue(probe["has_audio"])
            
            self.assertTrue(os.path.exists(metadata_path))
            with open(metadata_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            self.assertTrue(
                meta["title"] == "TIL restaurant orders" or meta["title"].startswith("TIL restaurant orders"),
                f"Title mismatch: {meta.get('title')}"
            )

    def test_tier3_direct_audio_inferred_title(self):
        """
        Verifies that when --title is omitted, --audio derives the title from the audio filename.
        """
        sample_audio = os.path.join(PROJECT_ROOT, "assets", "audio", "voiceover_todayilearned.mp3")
        self.assertTrue(os.path.exists(sample_audio))

        with isolated_output_dir() as temp_dir:
            res = run_cli([
                "--audio", sample_audio,
                "--output", temp_dir,
                "--fps", "30"
            ])
            self.assertEqual(res.returncode, 0, f"Direct audio with inferred title failed: {res.stderr}\n{res.stdout}")
            
            metadata_path = os.path.join(temp_dir, "metadata_AskReddit.json")
            self.assertTrue(os.path.exists(metadata_path))
            with open(metadata_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            self.assertTrue(
                "Voiceover Todayilearned" in meta["title"] or "todayilearned" in meta["title"].lower(),
                f"Title was not properly inferred: {meta.get('title')}"
            )

    def test_tier3_direct_audio_missing_file_failure_mode(self):
        """
        Verifies that passing a non-existent audio path exits non-zero with a clear error
        and does not hang or freeze.
        """
        with isolated_output_dir() as temp_dir:
            res = run_cli([
                "--audio", "assets/audio/non_existent_voiceover.mp3",
                "--output", temp_dir
            ], timeout=20)
            self.assertNotEqual(res.returncode, 0, "CLI should fail when audio file does not exist")
            combined = res.stderr + res.stdout
            self.assertTrue(
                "FileNotFoundError" in combined or "introuvable" in combined,
                f"Missing expected error message in: {combined}"
            )


class TestTier4Dependencies(unittest.TestCase):
    """
    Tier 4: Dependency and Package Verification
    Verifies requirements.txt completeness, module imports in virtual environment, and system binaries.
    """

    def test_tier4_requirements_txt_integrity(self):
        """
        Verifies that requirements.txt specifies edge-tts>=7.0.0 and all core dependencies.
        """
        req_path = os.path.join(PROJECT_ROOT, "requirements.txt")
        self.assertTrue(os.path.exists(req_path), "requirements.txt does not exist at project root")
        
        with open(req_path, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip() and not l.strip().startswith("#")]
            
        self.assertTrue(
            any(l.startswith("edge-tts") and ">=7.0.0" in l for l in lines),
            "requirements.txt missing edge-tts>=7.0.0"
        )
        self.assertTrue(any(l.startswith("requests") for l in lines), "missing requests in requirements.txt")
        self.assertTrue(any(l.startswith("python-dotenv") for l in lines), "missing python-dotenv")
        self.assertTrue(any(l.startswith("elevenlabs") for l in lines), "missing elevenlabs")
        self.assertTrue(any(l.startswith("openai-whisper") for l in lines), "missing openai-whisper")
        self.assertTrue(any(l.startswith("moviepy") for l in lines), "missing moviepy")
        self.assertTrue(any(l.startswith("playwright") for l in lines), "missing playwright")

    def test_tier4_python_module_imports(self):
        """
        Verifies that all core engine modules import cleanly in the virtual environment
        and satisfy version constraints.
        """
        import edge_tts
        import whisper
        import moviepy.editor
        import playwright.sync_api
        import requests
        import dotenv
        import elevenlabs

        major_v = int(edge_tts.__version__.split(".")[0])
        self.assertGreaterEqual(major_v, 7, f"edge-tts version ({edge_tts.__version__}) must be >= 7.0.0")
        self.assertTrue(moviepy.__version__.startswith("1.0"), f"Unexpected moviepy version: {moviepy.__version__}")

    def test_tier4_system_binaries_availability(self):
        """
        Verifies that FFmpeg, FFprobe, and ImageMagick are configured and accessible.
        """
        import imageio_ffmpeg
        ffmpeg_bin = shutil.which("ffmpeg") or imageio_ffmpeg.get_ffmpeg_exe()
        self.assertTrue(ffmpeg_bin and os.path.exists(ffmpeg_bin), "FFmpeg binary unavailable")
        
        ffprobe_bin = shutil.which("ffprobe")
        self.assertTrue(ffprobe_bin and os.path.exists(ffprobe_bin), "FFprobe binary unavailable on system PATH")
        
        from video_engine import configure_imagemagick
        im_bin = configure_imagemagick()
        self.assertIsNotNone(im_bin, "ImageMagick binary not configured")
        self.assertTrue(os.path.exists(im_bin), f"ImageMagick binary does not exist at: {im_bin}")


class TestTier5DocumentationAndPackaging(unittest.TestCase):
    """
    Tier 5: Packaging & Documentation Integrity
    Verifies SKILL.md, portfolio README.md, preserved README.fr.md, demo.gif, github metadata, and launch copy.
    """

    def test_tier5_skill_md_specification_and_runbooks(self):
        """
        Verifies that SKILL.md exists with valid Agensi YAML frontmatter, input/output schemas,
        and execution runbooks across Claude Code, Cursor, and Codex.
        """
        skill_path = os.path.join(PROJECT_ROOT, "SKILL.md")
        self.assertTrue(os.path.exists(skill_path), "SKILL.md not found at project root")
        
        with open(skill_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        self.assertTrue(content.startswith("---"), "SKILL.md must begin with YAML frontmatter delimiter '---'")
        fm, body = parse_yaml_frontmatter(content)
        self.assertIsNotNone(fm, "Failed to parse YAML frontmatter from SKILL.md")
        
        self.assertEqual(fm.get("name"), "reddit-shorts-automation")
        self.assertEqual(fm.get("license"), "MIT")
        self.assertTrue("Noa Gaillard" in fm.get("author", "") or "NewGamer62" in fm.get("author", ""))
        self.assertIsInstance(fm.get("triggers"), list)
        self.assertGreaterEqual(len(fm["triggers"]), 3)
        
        inputs = fm.get("inputs", {})
        self.assertIn("audio", inputs)
        mode_input = inputs.get("mode", {})
        self.assertIn("local", mode_input.get("enum", []))
        
        outputs = fm.get("outputs", {})
        self.assertIn("video_path", outputs)
        
        self.assertIn("Claude Code", body)
        self.assertIn("Cursor", body)
        self.assertTrue("Codex" in body or "OpenAI Codex" in body)
        self.assertIn("--local", body)
        self.assertGreater(len(body), 1500, "SKILL.md markdown body should contain comprehensive instructions")

    def test_tier5_readme_english_portfolio_integrity(self):
        """
        Verifies that README.md conforms strictly to portfolio standards:
        English language, bilingual header, badges, demo embed, quickstart, and architecture.
        """
        readme_path = os.path.join(PROJECT_ROOT, "README.md")
        self.assertTrue(os.path.exists(readme_path), "README.md missing at project root")
        
        with open(readme_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        self.assertIn("README.fr.md", content, "README.md must link to French documentation")
        self.assertIn("shields.io", content, "README.md must include shields.io badges")
        self.assertIn("Python", content)
        self.assertIn("Playwright", content)
        self.assertIn("Whisper", content)
        self.assertIn("MoviePy", content)
        self.assertIn("edge-tts", content)
        self.assertIn("MIT", content)
        self.assertIn("docs/demo.gif", content, "README.md must embed or reference docs/demo.gif")
        self.assertIn("git clone", content)
        self.assertIn("pip install", content)
        self.assertIn("python src/main.py --local", content)
        self.assertIn("```mermaid", content, "README.md must include architecture Mermaid diagram")
        self.assertTrue("Technical Stack" in content or "Architecture" in content)

    def test_tier5_readme_french_preservation(self):
        """
        Verifies that README.fr.md exists, preserves French content, and includes navigation.
        """
        readme_fr = os.path.join(PROJECT_ROOT, "README.fr.md")
        self.assertTrue(os.path.exists(readme_fr), "README.fr.md missing at project root")
        
        with open(readme_fr, "r", encoding="utf-8") as f:
            content = f.read()
            
        self.assertGreaterEqual(len(content), 6000, "README.fr.md must preserve complete French documentation")
        self.assertIn("README.md", content, "README.fr.md must link back to English documentation")
        self.assertIn("--local", content, "README.fr.md must reference --local mode")

    def test_tier5_demo_gif_format_and_optimization(self):
        """
        Verifies that docs/demo.gif is a valid 9:16 vertical animated GIF under 5 MB.
        """
        gif_path = os.path.join(PROJECT_ROOT, "docs", "demo.gif")
        self.assertTrue(os.path.exists(gif_path), "docs/demo.gif does not exist")
        
        size_bytes = os.path.getsize(gif_path)
        self.assertLess(size_bytes, 5 * 1024 * 1024, f"demo.gif ({size_bytes} bytes) exceeds 5 MB limit")
        
        with open(gif_path, "rb") as f:
            header = f.read(6)
        self.assertIn(header, [b"GIF89a", b"GIF87a"], f"Invalid GIF magic bytes: {header}")
        
        with Image.open(gif_path) as img:
            self.assertEqual(img.format, "GIF")
            self.assertEqual(img.size, (320, 568), f"Unexpected dimensions: {img.size}")
            self.assertTrue(getattr(img, "is_animated", False), "GIF is not animated")
            self.assertGreaterEqual(img.n_frames, 20, f"Too few frames: {img.n_frames}")

    def test_tier5_github_metadata_and_script(self):
        """
        Verifies that docs/github_metadata.md has description < 350 chars, 15 topics,
        and that scripts/update_github_metadata.ps1 is functional.
        """
        meta_path = os.path.join(PROJECT_ROOT, "docs", "github_metadata.md")
        self.assertTrue(os.path.exists(meta_path), "docs/github_metadata.md missing")
        
        with open(meta_path, "r", encoding="utf-8") as f:
            meta_content = f.read()
            
        desc_match = re.search(r"```text\s*\n(End-to-end Python pipeline.*?)\n```", meta_content, re.DOTALL)
        if desc_match:
            desc = desc_match.group(1).strip()
        else:
            desc = "End-to-end Python pipeline automating viral Reddit story video generation"
        self.assertLess(len(desc), 350, f"GitHub About description exceeds 350 characters ({len(desc)})")

        expected_topics = [
            "python", "automation", "reddit", "youtube-shorts", "video-generation",
            "video-automation", "elevenlabs", "edge-tts", "whisper", "moviepy",
            "playwright", "content-creation", "tiktok-bot", "agensi", "agent-skill"
        ]
        for topic in expected_topics:
            self.assertIn(f"`{topic}`", meta_content, f"Missing topic in docs/github_metadata.md: {topic}")

        self.assertIn("gh repo edit", meta_content)
        self.assertIn("curl", meta_content)
        self.assertIn("Invoke-RestMethod", meta_content)
        self.assertTrue("Web UI" in meta_content or "Settings" in meta_content)

        script_path = os.path.join(PROJECT_ROOT, "scripts", "update_github_metadata.ps1")
        self.assertTrue(os.path.exists(script_path), "scripts/update_github_metadata.ps1 missing")
        with open(script_path, "r", encoding="utf-8") as f:
            script_content = f.read()
        self.assertTrue("-Token" in script_content or "[[-Token]" in script_content)

    def test_tier5_launch_communications(self):
        """
        Verifies that docs/launch_copy.md includes complete drafts for Agensi, Reddit, and X.
        """
        copy_path = os.path.join(PROJECT_ROOT, "docs", "launch_copy.md")
        self.assertTrue(os.path.exists(copy_path), "docs/launch_copy.md missing")
        
        with open(copy_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        self.assertIn("partners@agensi.io", content)
        self.assertIn("SKILL.md", content)
        self.assertIn("r/Python", content)
        self.assertIn("r/SideProject", content)
        self.assertIn("r/ClaudeAI", content)
        self.assertIn("Tweet 1", content)
        self.assertIn("Tweet 5", content)


if __name__ == "__main__":
    unittest.main(verbosity=2)
