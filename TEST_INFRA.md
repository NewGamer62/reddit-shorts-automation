# Test Infrastructure & Runner Architecture

This document specifies the test philosophy, architecture, runner execution, media validation, and Windows subprocess safety governance for the **Reddit Shorts Automation** pipeline and Agensi Agent Skill.

---

## 1. Test Philosophy & Design Principles

The end-to-end (E2E) test suite is architected around five foundational principles:

1. **Opaque-Box & Requirement-Driven**:
   Tests interact with the pipeline strictly through its public CLI interfaces (`python src/main.py ...`) and documented module contracts (`src/tts_engine.py`). Tests observe terminal exit codes, standard streams, and output artifacts rather than mocking internal functions.
2. **Zero Test Dependencies**:
   The test runner and assertion harnesses rely exclusively on the Python standard library (`unittest`, `subprocess`, `tempfile`, `json`, `shutil`). No external test packages (such as `pytest`) are required to execute the full suite, preserving zero-friction local execution.
3. **Zero Process Zombies**:
   Every subprocess spawned by the test runner enforces a strict wall-clock timeout (30 seconds for static checks, 180 seconds for video rendering). On Windows, process tree cleanup (`taskkill /F /T /PID <pid>`) is triggered automatically on timeout expiration to eliminate orphaned ffmpeg, playwright, or python processes.
4. **Total Test Isolation**:
   Tests that produce media artifacts utilize isolated temporary workspaces via `tempfile.mkdtemp(prefix="shorts_test_")`. Media outputs and metadata JSON files are rendered into disposable directories, preventing pollution of the repository working tree, avoiding race conditions, and preserving git status cleanliness.
5. **Triple Runner Interoperability**:
   Test cases are authored as standard `unittest.TestCase` classes. The suite executes seamlessly via:
   - Direct standalone invocation: `python tests/test_e2e.py`
   - Standard library discovery: `python -m unittest discover -s tests -p "test_*.py"`
   - Third-party test runners (e.g. `pytest tests/`) if installed in external CI/CD pipelines.

---

## 2. Test Architecture & Directory Layout

The testing infrastructure is organized under `tests/` at the project root:

```text
Project206/
├── TEST_INFRA.md             # Authoritative test infrastructure and architecture specification
├── tests/
│   ├── __init__.py           # Package indicator for module discovery
│   ├── helpers.py            # CLI subprocess runner, directory isolator, and MediaValidator
│   └── test_e2e.py           # Unified 5-Tier E2E test suite (21 test cases across 5 Tiers)
```

### Module Responsibilities:
- **`tests/helpers.py`**:
  - `run_cli(args, timeout=180, env_overrides=None, cwd=PROJECT_ROOT)`: Safe subprocess launcher with UTF-8 encoding flags, pipe deadlock avoidance, and zombie cleanup.
  - `isolated_output_dir()`: Context manager creating and tearing down isolated temporary directories.
  - `MediaValidator`: Dual-engine media inspection class utilizing `ffprobe` JSON stream parsing with graceful fallback to MoviePy `VideoFileClip` / `AudioFileClip`.
- **`tests/test_e2e.py`**:
  - Implements the complete 5-Tier test taxonomy across dedicated `unittest.TestCase` classes.

---

## 3. The 5 Test Tiers

The test suite validates the full lifecycle across five structured tiers:

```
+-------------------------------------------------------------------------------+
|                             5-TIER TEST TAXONOMY                              |
+-------------------------------------------------------------------------------+
| Tier 1: Zero-Friction Local Execution                                         |
|         - Default local execution (offline story, edge-tts, ColorClip, 30fps) |
|         - Custom subreddit targeting (AITAH sample story & drama music)       |
|         - Custom text override (--text narrative synthesis)                   |
|         - YouTube upload safety gate without secrets                          |
+-------------------------------------------------------------------------------+
| Tier 2: Free TTS Fallback (src/tts_engine.py)                                 |
|         - Direct Edge-TTS neural speech synthesis                             |
|         - Transparent auto-fallback when ELEVENLABS_API_KEY is unset          |
|         - Auto-fallback recovery when ElevenLabs returns 401 Unauthorized     |
|         - Strict ElevenLabs mode failure assertion                            |
|         - Custom neural voice identifier override                             |
+-------------------------------------------------------------------------------+
| Tier 3: Direct Audio Injection (src/main.py --audio)                          |
|         - Pre-recorded voiceover injection (bypasses Reddit & TTS)            |
|         - Title inference from audio filename                                 |
|         - Missing audio file diagnostic failure mode                          |
+-------------------------------------------------------------------------------+
| Tier 4: Dependency and Package Verification                                   |
|         - requirements.txt integrity (edge-tts>=7.0.0, moviepy, whisper, etc.)|
|         - Virtual environment runtime package imports                         |
|         - External system binaries availability (FFmpeg, FFprobe, ImageMagick)|
+-------------------------------------------------------------------------------+
| Tier 5: Packaging & Documentation Integrity                                   |
|         - SKILL.md Agensi YAML frontmatter, schemas & agent runbooks          |
|         - README.md English portfolio standards (badges, quickstart, diagram) |
|         - README.fr.md French documentation preservation                      |
|         - docs/demo.gif 9:16 vertical format, animation, and < 5MB ceiling    |
|         - docs/github_metadata.md (< 350 chars, 15 topics) & update script    |
|         - docs/launch_copy.md (Agensi, Reddit r/Python, r/SideProject, X)     |
+-------------------------------------------------------------------------------+
```

---

## 4. Execution Commands

### 4.1 Standalone Script Runner (Recommended)
Executes directly with verbose formatting using the project virtual environment:
```powershell
.\.venv\Scripts\python.exe tests/test_e2e.py
```

### 4.2 Standard Unittest Discovery
Runs standard test discovery across the `tests/` directory:
```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
```

### 4.3 Running Specific Test Tiers or Methods
To run an individual tier or test case:
```powershell
# Run only Tier 2 (Free TTS):
.\.venv\Scripts\python.exe -m unittest tests.test_e2e.TestTier2FreeTTSFallback -v

# Run a specific test:
.\.venv\Scripts\python.exe -m unittest tests.test_e2e.TestTier3DirectAudioInjection.test_tier3_direct_audio_valid_sample -v
```

---

## 5. Media Validation Criteria

Automated assertions probe generated audio and video files using `MediaValidator`:

| Media Type | Criterion | Target Specification | Validation Method |
|------------|-----------|----------------------|-------------------|
| **Video** | Resolution & Aspect Ratio | `1080x1920` (9:16 vertical shorts format) | `ffprobe` stream stream[0].width/height |
| **Video** | Video Codec | `h264` or `libx264` | `ffprobe` stream[0].codec_name |
| **Video** | Duration | `> 0.0s` (matches voiceover within 0.7s) | `ffprobe` format.duration |
| **Video** | Audio Stream | Stereo/Mono `aac` or `mp4a` | `ffprobe` stream[1].codec_name |
| **Video** | File Size | `> 100,000` bytes (non-empty playable MP4) | `os.path.getsize(path)` |
| **Audio** | Codec | `mp3` | `ffprobe` stream[0].codec_name |
| **Audio** | Duration | `> 1.0s` | `ffprobe` format.duration |
| **Audio** | Sample Rate | `24000` Hz or `44100` Hz | `ffprobe` stream[0].sample_rate |
| **GIF** | Magic Bytes | `GIF89a` or `GIF87a` | File header (first 6 bytes) |
| **GIF** | File Size Ceiling | `< 5,242,880` bytes (< 5 MB) | `os.path.getsize(path)` |
| **GIF** | Dimensions | `320x568` (9:16 aspect ratio) | Pillow `Image.open` / `ffprobe` |
| **GIF** | Animation | Multi-frame (`nb_frames >= 20`) | Pillow `is_animated` / `n_frames` |

---

## 6. Windows Quirks & Subprocess Safety Governance

Running video generation pipelines and subprocesses on Windows presents four known failure modes that the test infrastructure explicitly mitigates:

1. **Console Codepage & Emoji Crashes (`UnicodeDecodeError` / `UnicodeEncodeError`)**:
   - *Problem*: The pipeline outputs terminal status messages with Unicode emojis (`🎤`, `🎬`, `✅`, `🎉`). Default Windows console codepages (e.g. `cp1252` or `cp850`) crash when decoding non-ASCII characters through subprocess pipes.
   - *Mitigation*: `run_cli` injects `PYTHONIOENCODING=utf-8` and `PYTHONUTF8=1` into `os.environ`, and sets `encoding="utf-8", errors="replace"` in `subprocess.run()`.
2. **OS Pipe Buffer Deadlocks**:
   - *Problem*: Whisper and MoviePy stream continuous progress bars and logging to `stdout` and `stderr`. On Windows, the OS pipe buffer is limited to 64 KB. Unbuffered synchronous reading or piping without active draining deadlocks the process when the buffer fills.
   - *Mitigation*: `run_cli` uses `subprocess.run(..., capture_output=True, text=True)`. This implementation internally uses asynchronous background reader threads that continuously drain OS buffers via `communicate()`.
3. **Subprocess Timeout & Zombie Process Prevention**:
   - *Problem*: If an external tool (e.g. Playwright or FFmpeg) hangs, waiting indefinitely paralyzes the test suite and locks file handles.
   - *Mitigation*: Explicit timeouts (30s for static checks, 180s for rendering) are enforced. Upon `TimeoutExpired`, `run_cli` on Windows executes `taskkill /F /T /PID <pid>` to force-terminate the entire process tree.
4. **MoviePy WinError 32 File Locking**:
   - *Problem*: On Windows, open read handles on `.mp4` or `.mp3` files prevent deletion or modification, raising `PermissionError: [WinError 32] The process cannot access the file because it is being used by another process`.
   - *Mitigation*: In `MediaValidator`, every MoviePy instance (`VideoFileClip`, `AudioFileClip`) is wrapped in strict `try ... finally: clip.close()` blocks to release all OS file locks immediately.
