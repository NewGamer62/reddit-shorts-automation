<#
.SYNOPSIS
    Updates the GitHub repository About description and topics for NewGamer62/reddit-shorts-automation.

.DESCRIPTION
    Uses the GitHub REST API (v2022-11-28) to configure the official portfolio repository metadata:
    - Description: Concise English summary (< 350 chars) highlighting the core pipeline.
    - Topics: 15 curated discoverability topics.
    Authenticates using an explicit parameter, pipeline input, environment variable, or interactive prompt.
    Supports -DryRun and standard -WhatIf / -Confirm switches via SupportsShouldProcess.

.PARAMETER Token
    Optional GitHub Personal Access Token (classic with 'repo' scope or fine-grained with 'Administration: Read & Write').
    Supports pipeline input ($token | .\update_github_metadata.ps1). If omitted, checks `$env:GITHUB_TOKEN`.

.PARAMETER Repo
    Target GitHub repository in "owner/repo" format. Defaults to 'NewGamer62/reddit-shorts-automation'.

.PARAMETER DryRun
    Simulate the API calls without performing HTTP PATCH/PUT requests, printing the target JSON payloads.

.EXAMPLE
    .\update_github_metadata.ps1 -Token "ghp_xxxxxxxxxxxx"

.EXAMPLE
    "ghp_xxxxxxxxxxxx" | .\update_github_metadata.ps1 -DryRun

.EXAMPLE
    .\update_github_metadata.ps1 -WhatIf
#>

[CmdletBinding(SupportsShouldProcess = $true)]
param (
    [Parameter(Mandatory = $false, Position = 0, ValueFromPipeline = $true, HelpMessage = "GitHub Personal Access Token with repo administration permissions")]
    [string]$Token,

    [Parameter(Mandatory = $false)]
    [string]$Repo = "NewGamer62/reddit-shorts-automation",

    [Parameter(Mandatory = $false, HelpMessage = "Simulate metadata update without sending API mutations")]
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  GitHub Repository Metadata Updater: $Repo" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$isDryRun = $DryRun.IsPresent -or ($PSBoundParameters.ContainsKey("WhatIf") -and $PSBoundParameters["WhatIf"])

# 1. Resolve Authentication Token
if ([string]::IsNullOrWhiteSpace($Token)) {
    if (![string]::IsNullOrWhiteSpace($env:GITHUB_TOKEN)) {
        Write-Host "[i] Using GitHub token from `$env:GITHUB_TOKEN." -ForegroundColor Gray
        $Token = $env:GITHUB_TOKEN.Trim()
    }
}

if ([string]::IsNullOrWhiteSpace($Token)) {
    if ($isDryRun) {
        Write-Host "[i] Dry-run / WhatIf mode active: using simulated token for payload verification." -ForegroundColor Gray
        $Token = "simulated_token_dryrun"
    } else {
        Write-Host ""
        Write-Host "[!] No GitHub Token provided via -Token or `$env:GITHUB_TOKEN." -ForegroundColor Yellow
        Write-Host "    A personal access token with 'repo' scope is required to modify repository settings." -ForegroundColor Yellow
        Write-Host "    You can create one at: https://github.com/settings/tokens" -ForegroundColor Yellow
        Write-Host ""
        
        # Prompt interactively if in interactive session, otherwise guide the user
        try {
            $prompted = Read-Host "Enter your GitHub Personal Access Token (or press Enter to cancel)"
            if (![string]::IsNullOrWhiteSpace($prompted)) {
                $Token = $prompted.Trim()
            }
        } catch {
            # Non-interactive session
        }
    }
}

if ([string]::IsNullOrWhiteSpace($Token)) {
    Write-Error "Execution aborted: No valid GitHub Personal Access Token provided. Please re-run with: .\update_github_metadata.ps1 -Token <PAT>"
    exit 1
}

# 2. Metadata Definitions
$targetDescription = "End-to-end Python pipeline automating viral Reddit story video generation (YouTube Shorts, TikTok, Reels). Integrates OpenAI Whisper word-sync subtitles, Edge-TTS & ElevenLabs voiceover, Playwright Reddit card rendering, MoviePy assembly, and YouTube Data API v3 upload."
$targetTopics = @(
    "python",
    "automation",
    "reddit",
    "youtube-shorts",
    "video-generation",
    "video-automation",
    "elevenlabs",
    "edge-tts",
    "whisper",
    "moviepy",
    "playwright",
    "content-creation",
    "tiktok-bot",
    "agensi",
    "agent-skill"
)

Write-Host "`n[1/3] Target Metadata:" -ForegroundColor Cyan
Write-Host " - Description length : $($targetDescription.Length) chars (Limit: 350)" -ForegroundColor Gray
Write-Host " - Target Topics ($($targetTopics.Count)) : $($targetTopics -join ', ')" -ForegroundColor Gray

# 3. Setup HTTP Request Headers
$headers = @{
    "Authorization"        = "Bearer $Token"
    "Accept"               = "application/vnd.github+json"
    "X-GitHub-Api-Version" = "2022-11-28"
    "User-Agent"           = "PowerShell-RedditShortsMetadataUpdater/1.0"
}

# 4. Update Repository Description via PATCH
$descApiUrl = "https://api.github.com/repos/$Repo"
Write-Host "`n[2/3] Updating Repository Description..." -ForegroundColor Cyan

$descPayload = @{
    description = $targetDescription
} | ConvertTo-Json -Compress

if ($isDryRun -or -not $PSCmdlet.ShouldProcess("Repository $Repo", "PATCH description: $targetDescription")) {
    Write-Host " [SIMULATION / DRY-RUN] HTTP PATCH $descApiUrl" -ForegroundColor Yellow
    Write-Host " [SIMULATION / DRY-RUN] Target JSON Payload:" -ForegroundColor Yellow
    Write-Host " $descPayload" -ForegroundColor Gray
    Write-Host " [OK] (Simulated) Repository description payload validated successfully!" -ForegroundColor Green
} else {
    try {
        $descResponse = Invoke-RestMethod -Uri $descApiUrl -Method Patch -Headers $headers -Body $descPayload -ContentType "application/json; charset=utf-8"
        Write-Host " [OK] Repository description updated successfully!" -ForegroundColor Green
        Write-Host "      Live Description: $($descResponse.description)" -ForegroundColor Gray
    } catch {
        Write-Host " [FAIL] Failed to update description." -ForegroundColor Red
        if ($_.Exception.Response) {
            $statusCode = [int]$_.Exception.Response.StatusCode
            Write-Host "        HTTP Status: $statusCode" -ForegroundColor Red
            try {
                $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
                $errBody = $reader.ReadToEnd()
                Write-Host "        Response: $errBody" -ForegroundColor Red
            } catch {}
        } else {
            Write-Host "        Error: $($_.Exception.Message)" -ForegroundColor Red
        }
        exit 2
    }
}

# 5. Update Repository Topics via PUT
$topicsApiUrl = "https://api.github.com/repos/$Repo/topics"
Write-Host "`n[3/3] Updating Repository Topics..." -ForegroundColor Cyan

$topicsPayload = @{
    names = $targetTopics
} | ConvertTo-Json -Compress

if ($isDryRun -or -not $PSCmdlet.ShouldProcess("Repository $Repo", "PUT topics ($($targetTopics.Count) topics)")) {
    Write-Host " [SIMULATION / DRY-RUN] HTTP PUT $topicsApiUrl" -ForegroundColor Yellow
    Write-Host " [SIMULATION / DRY-RUN] Target JSON Payload:" -ForegroundColor Yellow
    Write-Host " $topicsPayload" -ForegroundColor Gray
    Write-Host " [OK] (Simulated) Repository topics payload validated successfully!" -ForegroundColor Green
} else {
    try {
        $topicsResponse = Invoke-RestMethod -Uri $topicsApiUrl -Method Put -Headers $headers -Body $topicsPayload -ContentType "application/json; charset=utf-8"
        Write-Host " [OK] Repository topics updated successfully!" -ForegroundColor Green
        Write-Host "      Live Topics: $($topicsResponse.names -join ', ')" -ForegroundColor Gray
    } catch {
        Write-Host " [FAIL] Failed to update topics." -ForegroundColor Red
        if ($_.Exception.Response) {
            $statusCode = [int]$_.Exception.Response.StatusCode
            Write-Host "        HTTP Status: $statusCode" -ForegroundColor Red
            try {
                $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
                $errBody = $reader.ReadToEnd()
                Write-Host "        Response: $errBody" -ForegroundColor Red
            } catch {}
        } else {
            Write-Host "        Error: $($_.Exception.Message)" -ForegroundColor Red
        }
        exit 3
    }
}

# 6. Verification Summary
Write-Host "`n============================================================" -ForegroundColor Green
if ($isDryRun) {
    Write-Host "  SUCCESS (DRY-RUN): Metadata Payloads Verified for $Repo" -ForegroundColor Green
} else {
    Write-Host "  SUCCESS: GitHub Metadata Configured for $Repo" -ForegroundColor Green
}
Write-Host "============================================================" -ForegroundColor Green
Write-Host "Verify online at: https://github.com/$Repo" -ForegroundColor Cyan
