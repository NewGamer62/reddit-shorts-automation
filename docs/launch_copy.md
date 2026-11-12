# 🚀 Launch Communications & Agensi Partnership Copy

This document contains publication-ready launch copy for the **Reddit Shorts Automation Pipeline & Agent Skill** across multiple developer communities, social platforms, and partnership channels.

---

## 1. Formal Agensi Team Reply Draft

- **Recipient**: Reply directly to the Agensi outreach email thread
- **Sender**: Noa Gaillard (`@NewGamer62`)
- **Subject**: `Re: Reddit Shorts Automation Pipeline — Agensi Agent Skill Packaging & Distribution`

```text
Hi Agensi Team,

Thank you for reaching out regarding the distribution of the Reddit Shorts Automation Pipeline on the Agensi skill marketplace!

We are excited to confirm that the repository has now been officially packaged as an Agensi-native Agent Skill (`SKILL.md`), adhering fully to your progressive disclosure specification and standardized YAML frontmatter schema.

Key technical capabilities of this release:
1. Zero-Friction Autonomous Execution: Alongside high-fidelity ElevenLabs neural narration, the pipeline includes a zero-cost local fallback powered by Microsoft Edge Neural TTS (`edge-tts`) and bundled test assets. Agents running in sandboxed or CI environments can generate complete 1080x1920 60 FPS videos out of the box without requiring API keys or payment tokens.
2. Direct Audio Injection: Agents can pass pre-recorded voiceovers directly via `--audio`, enabling modular composition with any upstream voice, translation, or audio generator.
3. Multi-Agent Runbooks: Comprehensive execution runbooks and function-calling schemas are included for Claude Code, Cursor, and OpenAI Codex.
4. Production-Grade Assembly: Playwright-powered headless DOM dark-mode Reddit card rendering, OpenAI Whisper millisecond-accurate word karaoke subtitles, and MoviePy vertical compositing.

The official repository and skill packaging are live:
- Repository: https://github.com/NewGamer62/reddit-shorts-automation
- Skill Specification: https://github.com/NewGamer62/reddit-shorts-automation/blob/main/SKILL.md
- Demo Media: https://github.com/NewGamer62/reddit-shorts-automation/blob/main/docs/demo.gif

We would be thrilled to have this featured in the Agensi catalog. Please let us know if you need any additional metadata, webhook endpoints, or test fixtures for marketplace ingestion.

Best regards,

Noa Gaillard
GitHub: @NewGamer62
```

---

## 2. Reddit Community Launch Drafts

### 2.1 Subreddit: `r/Python`
- **Flair**: `Project` / `Showcase`
- **Title**: `I built an open-source automated video pipeline combining MoviePy, Whisper, Playwright, and edge-tts for zero-cost Shorts generation`

```markdown
Hey r/Python!

Automating vertical video production (YouTube Shorts, TikToks, Reels) with Python is notoriously tricky: MoviePy text clips frequently choke on ImageMagick paths, audio transcription timestamps drift, and capturing dynamic web cards requires clumsy browser hacks.

I built **Reddit Shorts Automation Pipeline**, a completely open-source batch pipeline that orchestrates the entire lifecycle from Reddit scraping to a finished 1080x1920 60 FPS MP4 video.

### 🛠️ How It Works Under the Hood
1. **Scraping & Content Moderation**: Requests fetches top threads from `r/AskReddit`, `r/AITAH`, or `r/TrueOffMyChest`, strips edits/links via regex, and runs text through a keyword blacklist to guarantee monetization safety.
2. **Headless DOM Card Rendering**: Uses **Playwright (Chromium)** to render a responsive, dark-mode Reddit card with custom fonts and exports a transparent PNG with zero background bleed.
3. **Dual TTS Engine**: Connects to ElevenLabs API v2, with an automatic zero-cost fallback to `edge-tts` (Microsoft Edge Neural TTS) so the pipeline runs locally without paid API keys.
4. **Millisecond Karaoke Subtitles**: Runs **OpenAI Whisper (`base`)** with `word_timestamps=True` to extract word start/end timings, generating dynamic, color-highlighted karaoke subtitle clips.
5. **Compositing**: MoviePy applies smart center-crop algorithms over 60 FPS vertical gameplay, mixes ambient soundtrack levels, and exports via `libx264`/`aac`.

### ⚡ Quickstart
```bash
git clone https://github.com/NewGamer62/reddit-shorts-automation.git
cd reddit-shorts-automation
pip install -r requirements.txt && playwright install chromium
python src/main.py --local
```

We also packaged it as an AI Agent Skill (`SKILL.md`) for Claude Code, Cursor, and Agensi.

Code is 100% MIT licensed: https://github.com/NewGamer62/reddit-shorts-automation

I’d love your feedback on MoviePy rendering performance and Whisper subtitle alignment!
```

---

### 2.2 Subreddit: `r/SideProject`
- **Flair**: `Side Project`
- **Title**: `Show SideProject: Turn Reddit stories into complete vertical TikTok/Shorts videos automatically with zero API costs`

```markdown
Hey everyone!

If you've ever tried running a faceless "storytime" TikTok or YouTube Shorts channel, you know the grind: finding good stories, recording voiceovers, designing Reddit cards, manually timing karaoke subtitles word-by-word in Premiere or CapCut, slicing gameplay, and uploading. It takes 1-2 hours per video.

I built an open-source tool that does the whole process in **30 seconds with 1 command**:

👉 **Reddit Shorts Automation Pipeline**

### 🌟 Key Features
- 🎙️ **Zero API Cost Option**: Uses free Microsoft Edge Neural voices (`edge-tts`) or high-end ElevenLabs voices.
- 🎨 **Authentic Reddit Cards**: Generated via headless browser with dark-mode styling and transparent backgrounds.
- 📝 **Auto Karaoke Subtitles**: Frame-accurate word-by-word highlighted captions powered by OpenAI Whisper.
- 🎮 **Gameplay Backgrounds**: Seamless vertical 9:16 compositing at 60 FPS.
- 🚀 **Local Mode**: Works 100% offline or locally without entering credit cards or API keys.

Check out the demo GIF and grab the code:  
GitHub: https://github.com/NewGamer62/reddit-shorts-automation

Would love your thoughts and suggestions on new features!
```

---

### 2.3 Subreddit: `r/ClaudeAI`
- **Flair**: `Tools / Workflow`
- **Title**: `Packaging a video generation engine as an agent skill (Claude Code / Agensi / Cursor) with zero-friction local execution`

```markdown
Hi r/ClaudeAI,

One of the biggest frustrations when giving AI coding agents (like Claude Code, Cursor, or Codex) tools to create media is "environment friction": agents fail because external APIs require paid keys, OAuth prompts block headless execution, or dependencies are missing.

We just published **Reddit Shorts Automation**, packaged as an autonomous Agent Skill (`SKILL.md`) designed specifically to solve this problem.

### 🤖 Why It's Built for Agents
- **Zero-Friction Local Execution**: Agents can run `python src/main.py --local` without any API keys, using built-in `edge-tts` and local asset fallbacks. No blockers during automated runs.
- **Direct Audio Injection**: Agents can pass custom audio files via `--audio` to chain the video engine with any other tool.
- **Progressive Disclosure**: Full execution runbooks for Claude Code, Cursor, and Codex are specified in `SKILL.md` with explicit input/output schemas.
- **Non-Interactive Safety**: Automatically disables OAuth browser popups when running in agent mode.

Try giving this prompt to Claude Code in the repo:
> "Run reddit shorts automation in local mode for r/AITAH and verify the resulting MP4 in output/."

Check out the `SKILL.md` and repository here:  
https://github.com/NewGamer62/reddit-shorts-automation
```

---

## 3. X (Twitter) Viral Launch Thread (5 Tweets)

### Tweet 1: Hook & Video Demo
```text
Creating faceless TikToks and YouTube Shorts from Reddit stories takes 1-2 hours per video.

I built an open-source pipeline that automates the entire workflow in 30 seconds — 100% free with zero API keys required. 🎬👇

[Attach docs/demo.gif]
```

### Tweet 2: Architecture & Under the Hood
```text
Here is the stack under the hood:
🔍 Scraping: requests + regex moderation blacklist
🎨 Cards: Headless Chromium DOM render (Playwright)
🎙️ Voice: Free edge-tts fallback or ElevenLabs v2
📝 Subtitles: OpenAI Whisper word-level karaoke sync
✂️ Montage: MoviePy 1080x1920 @ 60 FPS vertical crop
```

### Tweet 3: Zero-Friction Local Execution
```text
Most video automation tools require expensive API subscriptions.

This pipeline runs completely locally out-of-the-box:
1. Clone repo
2. pip install -r requirements.txt
3. python src/main.py --local

Your HD vertical short is rendered in seconds. ⚡
```

### Tweet 4: Agensi & AI Agent Skill Integration
```text
We also packaged this as an official @agensi_io Agent Skill (`SKILL.md`).

AI agents in Claude Code, Cursor, or Codex can autonomously generate videos from Reddit threads or custom text prompts without human intervention. 🤖
```

### Tweet 5: Call to Action & Open Source Link
```text
100% open-source under MIT license.

⭐ Star the repo on GitHub:
https://github.com/NewGamer62/reddit-shorts-automation

Contributions and feedback welcome! RTs appreciated! 🔁
```
