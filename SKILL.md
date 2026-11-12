---
name: reddit-shorts-automation
version: 1.0.0
description: "Automated end-to-end video creation pipeline that converts Reddit stories into 9:16 vertical shorts (YouTube Shorts, TikTok, Reels) with voiceover, Reddit card render, karaoke subtitles, and gameplay background. Supports zero-friction local execution (free edge-tts) and production cloud mode (ElevenLabs, YouTube API)."
author: "Noa Gaillard (NewGamer62)"
homepage: "https://github.com/NewGamer62/reddit-shorts-automation"
repository: "https://github.com/NewGamer62/reddit-shorts-automation"
license: "MIT"
tags:
  - video-generation
  - reddit
  - youtube-shorts
  - automation
  - tts
  - whisper
  - moviepy
  - playwright
  - edge-tts
  - elevenlabs
  - agensi-skill
compatibility:
  python: ">=3.10"
  platforms:
    - windows
    - linux
    - macos
  agents:
    - claude-code
    - cursor
    - codex
    - agensi
    - antigravity
triggers:
  - "generate a reddit short video"
  - "create a youtube short from reddit"
  - "turn this story into a vertical video"
  - "run reddit shorts automation"
  - "make a tiktok/reel from r/AskReddit, r/AITAH, or custom text"
  - "create a 9:16 video with karaoke subtitles"
  - "produce vertical video with edge-tts or audio voiceover"
inputs:
  mode:
    type: string
    enum: [local, production]
    default: "local"
    description: "Execution mode: 'local' runs without API keys (free edge-tts or direct audio, skips YouTube upload). 'production' uses ElevenLabs and uploads to YouTube."
  subreddit:
    type: string
    enum: [AITAH, AskReddit, TrueOffMyChest, custom]
    default: "AskReddit"
    description: "Target subreddit to scrape or select sample story from."
  text:
    type: string
    required: false
    description: "Optional custom story text. Bypasses Reddit scraping when provided."
  title:
    type: string
    required: false
    description: "Optional custom title for the Reddit card."
  author:
    type: string
    default: "u/StoryTeller"
    description: "Username displayed on the generated Reddit card."
  audio:
    type: string
    required: false
    description: "Optional path to a pre-recorded audio file (.mp3). Bypasses Reddit scraping and TTS generation entirely."
  tts_engine:
    type: string
    enum: [auto, edge-tts, elevenlabs]
    default: "auto"
    description: "TTS engine to use. 'edge-tts' requires no API key. 'auto' uses ElevenLabs if available, falling back to edge-tts."
  voice:
    type: string
    required: false
    description: "Voice identifier override for TTS engine (e.g. en-US-ChristopherNeural, en-US-JennyNeural)."
  output_dir:
    type: string
    default: "output"
    description: "Destination folder for generated MP4 video and metadata JSON."
  fps:
    type: integer
    default: 30
    description: "Video framerate (default: 30 fps, supports 60 fps)."
outputs:
  video_path:
    type: string
    description: "Path to the generated 1080x1920 MP4 video in the output directory."
  metadata_path:
    type: string
    description: "Path to generated JSON metadata containing title, description, and hashtags."
  card_path:
    type: string
    description: "Path to generated transparent Reddit card PNG."
  duration:
    type: number
    description: "Duration of the rendered video in seconds."
---

# Reddit Shorts Automation — Agensi Agent Skill Specification

## 1. Overview & Value Proposition

`reddit-shorts-automation` is an autonomous end-to-end media generation pipeline engineered to convert Reddit stories and custom narrative texts into high-engagement 9:16 vertical shorts (YouTube Shorts, TikTok, Instagram Reels).

### Value Proposition
- **Full Production Automation**: Eliminates 45–90 minutes of manual editing per video (scraping, voiceover recording, typography layout, subtitle alignment, background slicing, and SEO metadata).
- **Zero-Friction Local Execution**: Operates out of the box with zero external credentials, zero API secrets, and zero paid services via Microsoft Edge Neural TTS (`edge-tts`) and offline fallback stories.
- **Frame-Accurate Subtitle Synchronization**: Powered by OpenAI Whisper (`base`) to extract millisecond-accurate word timestamps for high-energy karaoke animations.
- **Production-Grade Reliability**: Defensive fallbacks for Reddit HTTP 403 blocks, missing gameplay clips (procedural dark `ColorClip`), dynamic ImageMagick discovery across Windows/macOS/Linux, and missing font resilience.
- **First-Class Agent Standard**: Adheres to the Agensi Agent Skill specification, allowing AI agents (Claude Code, Cursor, Codex, Agensi, Antigravity) to safely discover, plan, execute, and verify video creation tasks non-interactively.

---

## 2. When to Use & Trigger Conditions

Autonomous agents should activate this skill when a user request matches any of the following intents:
- **Vertical Short Creation**: "Make a YouTube Short / TikTok from AskReddit", "Create a vertical video from this story".
- **Reddit Story Visualization**: "Scrape r/AITAH and make a video", "Turn this Reddit post into a video with subtitles".
- **Faceless Content Generation**: "Generate automated shorts with background gameplay and karaoke subtitles".
- **Local Media Pipeline Execution**: "Test video creation without API keys", "Generate a short using an existing voiceover audio file".

---

## 3. Progressive Disclosure Architecture

To optimize token efficiency and avoid context bloat in autonomous agent environments, this skill implements a 4-stage progressive disclosure workflow:

```text
[Stage 1: Discovery]
   Agent reads YAML frontmatter (inputs, outputs, triggers, compatibility)
        ↓
[Stage 2: Planning & Validation]
   Agent checks dependencies, selects execution mode (local vs production), and verifies assets
        ↓
[Stage 3: Execution]
   Agent invokes CLI non-interactively (`python src/main.py --local ...`) with structured flags
        ↓
[Stage 4: Verification & Handoff]
   Agent inspects output artifacts (`output/*.mp4`, `output/*.json`) and delivers result
```

1. **Discovery**: The agent matches user intent against `triggers` and scans `inputs` to construct the execution plan.
2. **Planning**: The agent verifies system prerequisites (Python runtime, FFmpeg, ImageMagick) and determines whether credentials exist for cloud mode or if zero-friction local mode is required.
3. **Execution**: The agent issues a single, deterministic CLI command passing verified parameters.
4. **Verification**: The agent confirms file creation, checks non-zero file sizes, parses the metadata JSON, and reports output paths back to the user or caller agent.

---

## 4. Dedicated Agent Runbooks

### Runbook 1: Claude Code Agent Execution

Claude Code agents running in terminal/bash environments should execute commands non-interactively.

#### Step 1: Verify Dependencies
```bash
python -c "import moviepy, playwright, whisper, edge_tts; print('Dependencies OK')"
```

#### Step 2: Zero-Friction Local Video Generation
Run generation using free neural TTS and offline sample stories:
```bash
python src/main.py --local --subreddit AskReddit
```
*Expected Output*:
- Video: `output/final_video_AskReddit.mp4`
- Metadata: `output/metadata_AskReddit.json`
- Card: `assets/audio/reddit_card_AskReddit.png`

#### Step 3: Custom Story Text Generation
Supply custom text and title directly:
```bash
python src/main.py --local --title "AITA for refusing to share my notes?" --text "In college, a classmate who never attended lectures demanded my semester notes. I politely declined, and now their friend group is calling me selfish." --subreddit AITAH
```

#### Step 4: Direct Pre-recorded Audio Injection
When the user supplies a pre-existing voiceover file:
```bash
python src/main.py --audio assets/audio/voiceover_todayilearned.mp3 --title "TIL restaurant orders" --subreddit AskReddit
```

#### Step 5: Verification & Verification Gate
Verify generated files and report status:
```bash
python -c "import os, json; v = 'output/final_video_AskReddit.mp4'; assert os.path.exists(v) and os.path.getsize(v) > 50000, 'Video missing or empty'; print('PASS: Generated video size:', os.path.getsize(v), 'bytes')"
```

---

### Runbook 2: Cursor (Composer & Agent Mode Rules)

To integrate this skill seamlessly with Cursor IDE, configure a project rule in `.cursor/rules/reddit-shorts-automation.mdc` or `.cursorrules`:

#### Configuration File: `.cursor/rules/reddit-shorts-automation.mdc`
```markdown
---
description: Automated Reddit shorts and 9:16 vertical video generation pipeline
globs: src/**/*.py, assets/**, output/**
alwaysApply: false
---

# Reddit Shorts Automation Agent Rules

- When requested to create, test, or generate vertical video shorts, always invoke `python src/main.py` via the terminal.
- Default to `--local` mode unless the user explicitly provides API credentials or requests cloud publication.
- Never block on interactive prompts. Do not use `--upload` unless `client_secrets.json` is confirmed and the user specifically requests YouTube upload.
- When generating custom stories, provide `--title` and `--text` arguments to bypass Reddit network scraping.
- If pre-recorded audio is available, use `--audio <path>` to skip TTS generation and accelerate rendering.
- Verify that output files are written to `output/final_video_<subreddit>.mp4` before responding.
```

#### Sample Cursor Composer Prompt Patterns
- `@reddit-shorts-automation Generate a local short from r/AskReddit using free edge-tts.`
- `@reddit-shorts-automation Assemble a 9:16 short using assets/audio/voiceover_todayilearned.mp3.`
- `@reddit-shorts-automation Render this custom story: title='Life Lesson' text='Always backup your code before refactoring.'`

---

### Runbook 3: OpenAI Codex & Tool-Calling Agents

For LLMs with native function-calling capabilities (OpenAI GPT-4o, Anthropic Claude Tool Use, Gemini Function Calling), provide the following JSON tool specification:

#### Function Definition Schema (JSON Schema)
```json
{
  "name": "generate_reddit_short",
  "description": "Generates an end-to-end 9:16 vertical short video from a Reddit post, custom text, or pre-recorded audio with voiceover, Reddit card render, karaoke subtitles, and background video.",
  "parameters": {
    "type": "object",
    "properties": {
      "mode": {
        "type": "string",
        "enum": ["local", "production"],
        "default": "local",
        "description": "Execution mode. 'local' requires zero API credentials (free edge-tts, offline story fallback, skips YouTube upload). 'production' uses ElevenLabs and uploads to YouTube."
      },
      "subreddit": {
        "type": "string",
        "enum": ["AskReddit", "AITAH", "TrueOffMyChest"],
        "default": "AskReddit",
        "description": "Subreddit to source or label the story from."
      },
      "title": {
        "type": "string",
        "description": "Custom title to display on the rendered Reddit card."
      },
      "text": {
        "type": "string",
        "description": "Custom story narrative text. When provided, Reddit web scraping is bypassed."
      },
      "audio": {
        "type": "string",
        "description": "Relative or absolute file path to a pre-recorded audio file (.mp3). When provided, both Reddit scraping and TTS synthesis are bypassed."
      },
      "tts_engine": {
        "type": "string",
        "enum": ["auto", "edge-tts", "elevenlabs"],
        "default": "auto",
        "description": "TTS provider. 'edge-tts' is 100% free and requires no API key. 'auto' falls back to edge-tts if ElevenLabs fails or is unconfigured."
      },
      "voice": {
        "type": "string",
        "description": "Optional neural voice override (e.g., 'en-US-ChristopherNeural', 'en-US-JennyNeural')."
      },
      "output": {
        "type": "string",
        "default": "output",
        "description": "Output directory for final MP4 and metadata JSON."
      },
      "fps": {
        "type": "integer",
        "default": 30,
        "description": "Video framerate (e.g. 30 or 60)."
      },
      "upload": {
        "type": "boolean",
        "default": false,
        "description": "Whether to publish to YouTube and send Discord webhook alerts. Requires client_secrets.json."
      }
    },
    "required": ["mode"]
  }
}
```

#### Tool Invocation Example (Local Mode)
```json
{
  "name": "generate_reddit_short",
  "arguments": {
    "mode": "local",
    "subreddit": "AITAH",
    "title": "AITAH for keeping my grandpa's vintage collection?",
    "text": "My grandfather left me his entire vintage tool and watch collection. My family insists we sell it to split the money, but I want to preserve his memory.",
    "tts_engine": "edge-tts"
  }
}
```

#### Expected Tool Output Response
```json
{
  "status": "success",
  "video_path": "output/final_video_AITAH.mp4",
  "metadata_path": "output/metadata_AITAH.json",
  "card_path": "assets/audio/reddit_card_AITAH.png",
  "resolution": "1080x1920",
  "fps": 30,
  "tts_engine_used": "edge-tts"
}
```

---

## 5. Full CLI Reference

`src/main.py` is the unified command-line entrypoint. It supports the following arguments:

| Flag | Short | Type | Default | Choices / Allowed Values | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `--local` | `--test` | flag | `False` | Boolean switch | Runs in zero-secret local mode with Edge-TTS, offline sample story fallback, and upload disabled. |
| `--audio` | - | string | `None` | Path to `.mp3` file | Path to pre-existing audio file (bypasses Reddit scraping and TTS synthesis). |
| `--text` | - | string | `None` | String | Custom story text (bypasses Reddit web scraping). |
| `--title` | - | string | `None` | String | Custom title displayed on the generated Reddit card. |
| `--subreddit` | - | string | `None` | e.g. `AskReddit`, `AITAH`, `TrueOffMyChest` | Target subreddit for story scraping or sample fallback selection. |
| `--tts-engine` | `--tts` | string | `None` (`auto` / `edge-tts`) | `auto`, `edge-tts`, `elevenlabs` | TTS engine selection. In `--local` mode, defaults to `edge-tts`. In production, defaults to `auto`. |
| `--voice` | - | string | `None` | String | Voice identifier override (e.g. `en-US-ChristopherNeural`, `en-US-JennyNeural`). |
| `--upload` | - | flag | `False` | Boolean switch | Explicitly enables YouTube Data API upload and Discord alert. Requires `client_secrets.json`. |
| `--output` | - | string | `None` (`output/`) | Directory path | Output directory for rendered videos and metadata files. |
| `--fps` | - | integer | `30` | `24`, `30`, `60` | Framerate for video compositing and export. |

---

## 6. Environment Variables & Fallback Architecture

### Environment Variables (`.env`)

| Variable | Required | Default | Purpose |
| :--- | :--- | :--- | :--- |
| `ELEVENLABS_API_KEY` | Optional | `None` | ElevenLabs API key for premium neural voiceover synthesis. If absent, pipeline defaults or falls back to free `edge-tts`. |
| `DISCORD_WEBHOOK_URL`| Optional | `None` | Discord webhook URL for publishing alerts when `--upload` is specified. |
| `IMAGEMAGICK_BINARY`  | Optional | Auto-detected | Explicit path to ImageMagick `magick.exe` (Windows) or `magick` binary (Unix). If not provided, dynamic system search detects standard installation directories. |

### Google OAuth Credentials
- `client_secrets.json`: Required **only** when `--upload` is passed to authenticate with the YouTube Data API v3. Never required in `--local` mode.

### Defensive Fallback Matrix

```text
┌───────────────────────────┬──────────────────────────────────────┬────────────────────────────────────────┐
│ Fragility Point           │ Failure Trigger                      │ Built-in Fallback Mechanism            │
├───────────────────────────┼──────────────────────────────────────┼────────────────────────────────────────┤
│ Reddit Scraper            │ HTTP 403 Forbidden / Rate Limiting   │ Curated SAMPLE_STORIES in src/main.py  │
│ ElevenLabs API            │ Missing key / 401 Unauthorized / 5xx │ Automatic switch to edge-tts           │
│ Gameplay Clips            │ assets/gameplay/ has no .mp4 clips   │ Procedural high-contrast ColorClip     │
│ Playwright Chromium       │ Headless browser not installed       │ Uses cached cards in assets/audio/     │
│ Subtitle Typography       │ Missing Komika Axis.ttf              │ Falls back to LEMONMILK-Bold.otf       │
│ ImageMagick Path          │ Hardcoded path missing               │ Dynamic glob + PATH resolution         │
│ YouTube OAuth             │ Interactive prompt in headless agent │ Disabled by default (gated by --upload)│
└───────────────────────────┴──────────────────────────────────────┴────────────────────────────────────────┘
```

---

## 7. Troubleshooting & Error Recovery Guide for Agents

When operating autonomously, agents should consult this decision matrix upon encountering non-zero exit codes or runtime exceptions:

| Error / Symptom | Root Cause | Automated Agent Recovery Action |
| :--- | :--- | :--- |
| `ApiError: status_code: 401 (ElevenLabs)` | Invalid or missing `ELEVENLABS_API_KEY`. | Re-run with `--tts-engine edge-tts` or `--local`. |
| `RuntimeError: Reddit returned status code 403` | Reddit unauthenticated scraping blocked. | Re-run with `--local` (uses curated sample story) or supply explicit `--text "..." --title "..."`. |
| `IndexError: Cannot choose from an empty sequence` | `assets/gameplay/` has no `.mp4` video files. | Video engine automatically uses dark `ColorClip`. If running a custom script, place a `.mp4` clip in `assets/gameplay/`. |
| `FileNotFoundError: client_secrets.json` | `--upload` was passed without OAuth credentials. | Omit the `--upload` flag for local, test, or CI execution. |
| `ImageMagick is not installed or not in PATH` | MoviePy cannot locate ImageMagick binary. | Set environment variable `IMAGEMAGICK_BINARY` or ensure ImageMagick is installed. In Windows: `C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe`. |
| `playwright._impl._errors.Error: Executable doesn't exist` | Chromium binary not installed for Playwright. | Run `playwright install chromium` in bash/terminal, or let `main.py` use pre-rendered card fallback. |
| `torch / whisper out of memory` | GPU VRAM exhausted. | Whisper uses the lightweight `base` model by default and executes reliably on CPU when CUDA is unavailable. |

---

## 8. Author & License Information

- **Author**: Noa Gaillard ([@NewGamer62](https://github.com/NewGamer62))
- **Standard**: Agensi Agent Skill Standard v1.0.0
- **Repository**: [https://github.com/NewGamer62/reddit-shorts-automation](https://github.com/NewGamer62/reddit-shorts-automation)
- **License**: MIT
