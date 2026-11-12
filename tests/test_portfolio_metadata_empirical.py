"""
Empirical verification suite for Portfolio Documentation, Media & Launch Communications (Iteration 2).
Tests:
- scripts/update_github_metadata.ps1 syntax and AST
- PowerShell execution modes (Pipeline + DryRun, Pipeline + WhatIf, Standalone DryRun)
- Metadata description length and topics integrity
- Documentation consistency across docs/github_metadata.md
- Markdown relative link integrity across README.md, README.fr.md, docs/
- Demo GIF specifications and size thresholds
"""

import os
import re
import json
import subprocess
import pytest
from PIL import Image

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_update_github_metadata_ast_syntax():
    """Verify scripts/update_github_metadata.ps1 has 0 AST parse errors."""
    ps_script = os.path.join(PROJECT_ROOT, "scripts", "update_github_metadata.ps1")
    assert os.path.isfile(ps_script), f"Missing script: {ps_script}"

    cmd = [
        "powershell",
        "-NoProfile",
        "-Command",
        f"& {{ $errors = $null; $tokens = $null; [System.Management.Automation.Language.Parser]::ParseFile('{ps_script}', [ref]$tokens, [ref]$errors); if ($errors.Count -gt 0) {{ $errors | ForEach-Object {{ Write-Error $_ }}; exit 1 }} }}"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, f"AST Syntax Errors detected:\n{res.stderr}"


def test_pipeline_input_with_dryrun():
    """Verify pipeline input with -DryRun exits with code 0 and displays simulated payloads."""
    cmd = [
        "powershell",
        "-NoProfile",
        "-Command",
        "& { 'ghp_test_token_12345' | .\\scripts\\update_github_metadata.ps1 -DryRun }"
    ]
    res = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True)
    assert res.returncode == 0, f"Pipeline DryRun failed:\n{res.stderr}\nOutput:\n{res.stdout}"
    assert "SIMULATION / DRY-RUN" in res.stdout
    assert "SUCCESS (DRY-RUN)" in res.stdout
    assert "https://api.github.com/repos/NewGamer62/reddit-shorts-automation" in res.stdout


def test_pipeline_input_with_whatif():
    """Verify pipeline input with -WhatIf exits with code 0 and triggers WhatIf simulation."""
    cmd = [
        "powershell",
        "-NoProfile",
        "-Command",
        "& { 'test_token' | .\\scripts\\update_github_metadata.ps1 -WhatIf }"
    ]
    res = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True)
    assert res.returncode == 0, f"Pipeline WhatIf failed:\n{res.stderr}\nOutput:\n{res.stdout}"
    assert "SIMULATION / DRY-RUN" in res.stdout
    assert "SUCCESS (DRY-RUN)" in res.stdout


def test_standalone_dryrun_without_token():
    """Verify standalone -DryRun exits with code 0 even if GITHUB_TOKEN is empty."""
    cmd = [
        "powershell",
        "-NoProfile",
        "-Command",
        "& { $env:GITHUB_TOKEN = ''; .\\scripts\\update_github_metadata.ps1 -DryRun }"
    ]
    res = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True)
    assert res.returncode == 0, f"Standalone DryRun failed:\n{res.stderr}\nOutput:\n{res.stdout}"
    assert "Dry-run / WhatIf mode active: using simulated token" in res.stdout
    assert "SUCCESS (DRY-RUN)" in res.stdout


def test_description_length_and_alignment():
    """Verify exact description string length is 270 chars (< 350) and docs/github_metadata.md states 270."""
    ps_path = os.path.join(PROJECT_ROOT, "scripts", "update_github_metadata.ps1")
    with open(ps_path, "r", encoding="utf-8") as f:
        ps_content = f.read()

    m = re.search(r'\$targetDescription\s*=\s*"([^"]+)"', ps_content)
    assert m, "Could not find $targetDescription in update_github_metadata.ps1"
    desc = m.group(1)

    exact_length = len(desc)
    assert exact_length == 270, f"Expected description length 270, got {exact_length}"
    assert exact_length < 350, f"Description exceeds 350 limit: {exact_length}"

    doc_path = os.path.join(PROJECT_ROOT, "docs", "github_metadata.md")
    with open(doc_path, "r", encoding="utf-8") as f:
        doc_content = f.read()

    assert desc in doc_content, "Description in script not found verbatim in docs/github_metadata.md"
    assert "270 characters" in doc_content, "docs/github_metadata.md does not state '270 characters'"
    assert "275 characters" not in doc_content, "docs/github_metadata.md still contains stale '275 characters' reference"


def test_topics_integrity():
    """Verify 15 topics are defined, lowercase alphanumeric with hyphens, and match between script and doc."""
    ps_path = os.path.join(PROJECT_ROOT, "scripts", "update_github_metadata.ps1")
    with open(ps_path, "r", encoding="utf-8") as f:
        ps_content = f.read()

    m = re.search(r'\$targetTopics\s*=\s*@\((.*?)\)', ps_content, re.DOTALL)
    assert m, "Could not find $targetTopics in update_github_metadata.ps1"
    topics_raw = m.group(1)
    topics = re.findall(r'"([^"]+)"', topics_raw)

    assert len(topics) == 15, f"Expected 15 topics, got {len(topics)}"
    for topic in topics:
        assert re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", topic), f"Topic '{topic}' invalid slug format"
        assert len(topic) <= 50, f"Topic '{topic}' exceeds 50 char limit"

    doc_path = os.path.join(PROJECT_ROOT, "docs", "github_metadata.md")
    with open(doc_path, "r", encoding="utf-8") as f:
        doc_content = f.read()

    for topic in topics:
        assert f"`{topic}`" in doc_content, f"Topic `{topic}` not documented in docs/github_metadata.md"


def test_readme_relative_links():
    """Verify all relative links in README.md point to existing files."""
    readme_path = os.path.join(PROJECT_ROOT, "README.md")
    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Match [text](relative_url)
    link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
    # Match <img src="relative_url"
    img_pattern = re.compile(r'<img\s+[^>]*src="([^"]+)"')

    links = []
    for match in link_pattern.finditer(content):
        target = match.group(2)
        if not target.startswith("http://") and not target.startswith("https://") and not target.startswith("#"):
            clean_target = target.split("#")[0]
            if clean_target:
                links.append(clean_target)

    for match in img_pattern.finditer(content):
        target = match.group(1)
        if not target.startswith("http://") and not target.startswith("https://"):
            clean_target = target.split("#")[0]
            if clean_target:
                links.append(clean_target)

    assert len(links) > 0, "No relative links found in README.md"

    broken = []
    for link in links:
        full_path = os.path.join(PROJECT_ROOT, link.replace("/", os.sep))
        if not os.path.exists(full_path):
            broken.append(link)

    assert not broken, f"Broken relative links detected in README.md: {broken}"


def test_readme_fr_relative_links():
    """Verify all relative links in README.fr.md point to existing files."""
    readme_fr_path = os.path.join(PROJECT_ROOT, "README.fr.md")
    with open(readme_fr_path, "r", encoding="utf-8") as f:
        content = f.read()

    link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
    img_pattern = re.compile(r'<img\s+[^>]*src="([^"]+)"')

    links = []
    for match in link_pattern.finditer(content):
        target = match.group(2)
        if not target.startswith("http://") and not target.startswith("https://") and not target.startswith("#"):
            clean_target = target.split("#")[0]
            if clean_target:
                links.append(clean_target)

    for match in img_pattern.finditer(content):
        target = match.group(1)
        if not target.startswith("http://") and not target.startswith("https://"):
            clean_target = target.split("#")[0]
            if clean_target:
                links.append(clean_target)

    broken = []
    for link in links:
        full_path = os.path.join(PROJECT_ROOT, link.replace("/", os.sep))
        if not os.path.exists(full_path):
            broken.append(link)

    assert not broken, f"Broken relative links detected in README.fr.md: {broken}"


def test_demo_gif_specifications():
    """Verify docs/demo.gif exists, is < 5 MB, 320x568, and animated."""
    gif_path = os.path.join(PROJECT_ROOT, "docs", "demo.gif")
    assert os.path.isfile(gif_path), "docs/demo.gif does not exist"

    file_size = os.path.getsize(gif_path)
    assert file_size < 5 * 1024 * 1024, f"docs/demo.gif exceeds 5 MB: {file_size} bytes"
    assert file_size > 500 * 1024, f"docs/demo.gif suspiciously small: {file_size} bytes"

    with Image.open(gif_path) as im:
        assert getattr(im, "is_animated", False), "docs/demo.gif is not animated"
        assert im.n_frames >= 20, f"Too few frames in demo.gif: {im.n_frames}"
        assert im.size == (320, 568), f"Unexpected dimensions: {im.size}"
