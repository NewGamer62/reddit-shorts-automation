# 🏷️ GitHub Repository Metadata & Configuration Guide

**Target Repository**: [`NewGamer62/reddit-shorts-automation`](https://github.com/NewGamer62/reddit-shorts-automation)  
**Standard Compliance**: Strictly conforms to `portfolio_github_standards.md` (< 350 characters, targeted topics, professional portfolio presentation).

---

## 1. Metadata Values

### 📝 About Description
- **Character Count**: 270 characters (Strictly < 350 limit)
- **Language**: English
- **Content**:
```text
End-to-end Python pipeline automating viral Reddit story video generation (YouTube Shorts, TikTok, Reels). Integrates OpenAI Whisper word-sync subtitles, Edge-TTS & ElevenLabs voiceover, Playwright Reddit card rendering, MoviePy assembly, and YouTube Data API v3 upload.
```

### 🏷️ Repository Topics (15 Targeted Topics)
All topics adhere to GitHub naming conventions (lowercase alphanumeric and hyphens):

| # | Topic | Category / Relevance |
|---|---|---|
| 1 | `python` | Primary development language (Python 3.10+) |
| 2 | `automation` | Autonomous batch generation pipeline |
| 3 | `reddit` | Content sourcing from viral subreddits |
| 4 | `youtube-shorts` | Primary target vertical video format |
| 5 | `video-generation` | Core functional domain |
| 6 | `video-automation` | End-to-end pipeline automation |
| 7 | `elevenlabs` | High-fidelity neural voice synthesis engine |
| 8 | `edge-tts` | Zero-cost Microsoft Edge Neural voiceover fallback |
| 9 | `whisper` | OpenAI Whisper word-level karaoke subtitle alignment |
| 10 | `moviepy` | Video compositing and vertical 9:16 60 FPS cropping |
| 11 | `playwright` | Headless Chromium DOM snapshot of dark-mode Reddit cards |
| 12 | `content-creation` | Content creator and creator economy toolchain |
| 13 | `tiktok-bot` | Cross-platform vertical video distribution |
| 14 | `agensi` | Agensi skill marketplace distribution |
| 15 | `agent-skill` | Standardized AI agent skill interface (`SKILL.md`) |

---

## 2. Automated Execution Script

A turnkey PowerShell script is bundled in `scripts/update_github_metadata.ps1`:

```powershell
# Run with an explicit personal access token (PAT)
.\scripts\update_github_metadata.ps1 -Token "ghp_yourPersonalAccessTokenHere"

# Or set GITHUB_TOKEN in your environment:
$env:GITHUB_TOKEN = "ghp_yourPersonalAccessTokenHere"
.\scripts\update_github_metadata.ps1
```

---

## 3. Multi-Format Execution Commands & Fallbacks

If the automated script is not used, choose from any of the following standard execution methods:

### Method A: GitHub CLI (`gh`)
*Requires `gh` CLI installed and authenticated (`gh auth login`).*

```bash
gh repo edit NewGamer62/reddit-shorts-automation \
  --description "End-to-end Python pipeline automating viral Reddit story video generation (YouTube Shorts, TikTok, Reels). Integrates OpenAI Whisper word-sync subtitles, Edge-TTS & ElevenLabs voiceover, Playwright Reddit card rendering, MoviePy assembly, and YouTube Data API v3 upload." \
  --add-topic python,automation,reddit,youtube-shorts,video-generation,video-automation,elevenlabs,edge-tts,whisper,moviepy,playwright,content-creation,tiktok-bot,agensi,agent-skill
```

---

### Method B: cURL / Bash REST API
*Replace `<YOUR_GITHUB_PAT>` with a Personal Access Token containing `repo` scope.*

```bash
# 1. Update Repository Description (PATCH)
curl -L \
  -X PATCH \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer <YOUR_GITHUB_PAT>" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  https://api.github.com/repos/NewGamer62/reddit-shorts-automation \
  -d '{"description":"End-to-end Python pipeline automating viral Reddit story video generation (YouTube Shorts, TikTok, Reels). Integrates OpenAI Whisper word-sync subtitles, Edge-TTS & ElevenLabs voiceover, Playwright Reddit card rendering, MoviePy assembly, and YouTube Data API v3 upload."}'

# 2. Update Repository Topics (PUT)
curl -L \
  -X PUT \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer <YOUR_GITHUB_PAT>" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  https://api.github.com/repos/NewGamer62/reddit-shorts-automation/topics \
  -d '{"names":["python","automation","reddit","youtube-shorts","video-generation","video-automation","elevenlabs","edge-tts","whisper","moviepy","playwright","content-creation","tiktok-bot","agensi","agent-skill"]}'
```

---

### Method C: Windows PowerShell (`Invoke-RestMethod`)

```powershell
$token = "<YOUR_GITHUB_PAT>"
$headers = @{
    "Authorization"        = "Bearer $token"
    "Accept"               = "application/vnd.github+json"
    "X-GitHub-Api-Version" = "2022-11-28"
    "User-Agent"           = "PowerShell-Repo-Metadata-Updater"
}

# 1. Update Description
$descBody = @{
    description = "End-to-end Python pipeline automating viral Reddit story video generation (YouTube Shorts, TikTok, Reels). Integrates OpenAI Whisper word-sync subtitles, Edge-TTS & ElevenLabs voiceover, Playwright Reddit card rendering, MoviePy assembly, and YouTube Data API v3 upload."
} | ConvertTo-Json -Compress

$descResponse = Invoke-RestMethod -Uri "https://api.github.com/repos/NewGamer62/reddit-shorts-automation" `
    -Headers $headers -Method Patch -Body $descBody -ContentType "application/json"

Write-Host "Description successfully updated to: $($descResponse.description)" -ForegroundColor Green

# 2. Update Topics
$topicsBody = @{
    names = @(
        "python", "automation", "reddit", "youtube-shorts", "video-generation",
        "video-automation", "elevenlabs", "edge-tts", "whisper", "moviepy",
        "playwright", "content-creation", "tiktok-bot", "agensi", "agent-skill"
    )
} | ConvertTo-Json -Compress

$topicsResponse = Invoke-RestMethod -Uri "https://api.github.com/repos/NewGamer62/reddit-shorts-automation/topics" `
    -Headers $headers -Method Put -Body $topicsBody -ContentType "application/json"

Write-Host "Topics successfully updated: $($topicsResponse.names -join ', ')" -ForegroundColor Green
```

---

### Method D: GitHub Web UI (Zero-Tooling Fallback)

1. Open your browser and navigate to:  
   [`https://github.com/NewGamer62/reddit-shorts-automation`](https://github.com/NewGamer62/reddit-shorts-automation)
2. In the right-hand sidebar under **About**, click the gear icon (⚙️ **Edit repository details**).
3. In the **Description** field, paste:
   ```text
   End-to-end Python pipeline automating viral Reddit story video generation (YouTube Shorts, TikTok, Reels). Integrates OpenAI Whisper word-sync subtitles, Edge-TTS & ElevenLabs voiceover, Playwright Reddit card rendering, MoviePy assembly, and YouTube Data API v3 upload.
   ```
4. In the **Topics** field, add each of the 15 topics:
   `python`, `automation`, `reddit`, `youtube-shorts`, `video-generation`, `video-automation`, `elevenlabs`, `edge-tts`, `whisper`, `moviepy`, `playwright`, `content-creation`, `tiktok-bot`, `agensi`, `agent-skill`.
5. Ensure **Include in the home page** checks are configured as desired.
6. Click **Save changes**.

---

## 4. Verification

To verify that the repository metadata is live and publicly accessible:

```powershell
$repo = Invoke-RestMethod -Uri "https://api.github.com/repos/NewGamer62/reddit-shorts-automation" -Headers @{"Accept"="application/vnd.github+json"}
Write-Host "Current Description : $($repo.description)"
Write-Host "Current Topics      : $($repo.topics -join ', ')"
```
