"""
Challenger 2 Empirical Stress Tests for Sub-Milestone M4: Agensi Agent Skill Packaging (SKILL.md).
"""
import os
import sys
import re
import json
import subprocess
import pytest
import jsonschema

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL_PATH = os.path.join(PROJECT_ROOT, "SKILL.md")


def read_skill():
    with open(SKILL_PATH, "r", encoding="utf-8") as f:
        return f.read()


class TestCodexJsonSchema:
    """Stress test 1: Validate Codex JSON Schema embedded in Runbook 3."""

    def test_extract_and_validate_codex_schema(self):
        content = read_skill()
        json_blocks = re.findall(r"```json\s*(\{.*?\})\s*```", content, re.DOTALL)
        assert len(json_blocks) >= 3, f"Expected at least 3 JSON blocks in Runbook 3, found {len(json_blocks)}"

        # Block 0: Tool Definition Schema
        tool_def = json.loads(json_blocks[0])
        assert "name" in tool_def
        assert tool_def["name"] == "generate_reddit_short"
        assert "parameters" in tool_def

        schema = tool_def["parameters"]
        # Validate schema itself using jsonschema Draft7Validator
        jsonschema.Draft7Validator.check_schema(schema)

        validator = jsonschema.Draft7Validator(schema)

        # Block 1: Sample Tool Call Arguments
        sample_call = json.loads(json_blocks[1])
        assert "arguments" in sample_call
        validator.validate(sample_call["arguments"])

    def test_schema_adversarial_rejections(self):
        """Ensure schema strictly rejects malformed or invalid agent invocations."""
        content = read_skill()
        json_blocks = re.findall(r"```json\s*(\{.*?\})\s*```", content, re.DOTALL)
        tool_def = json.loads(json_blocks[0])
        schema = tool_def["parameters"]
        validator = jsonschema.Draft7Validator(schema)

        # 1. Missing required 'mode'
        with pytest.raises(jsonschema.ValidationError) as exc:
            validator.validate({"subreddit": "AskReddit"})
        assert "'mode' is a required property" in str(exc.value)

        # 2. Invalid mode enum
        with pytest.raises(jsonschema.ValidationError):
            validator.validate({"mode": "sandbox"})

        # 3. Invalid tts_engine enum
        with pytest.raises(jsonschema.ValidationError):
            validator.validate({"mode": "local", "tts_engine": "pyttsx3"})

        # 4. Invalid subreddit enum
        with pytest.raises(jsonschema.ValidationError):
            validator.validate({"mode": "local", "subreddit": "memes"})

        # 5. Invalid type for fps (string instead of integer)
        with pytest.raises(jsonschema.ValidationError):
            validator.validate({"mode": "local", "fps": "60"})

        # 6. Invalid type for upload (string instead of boolean)
        with pytest.raises(jsonschema.ValidationError):
            validator.validate({"mode": "local", "upload": "false"})


class TestMarkdownIntegrity:
    """Stress test 2: Adversarial markdown syntax and safety checks."""

    def test_code_fences_perfectly_paired(self):
        content = read_skill()
        lines = content.splitlines()

        fence_lines = []
        for idx, line in enumerate(lines, 1):
            if line.strip().startswith("```"):
                fence_lines.append((idx, line.strip()))

        assert len(fence_lines) > 0, "No code fences found in SKILL.md"
        assert len(fence_lines) % 2 == 0, f"Unbalanced code fences found! Count: {len(fence_lines)}"

        # Check fence tags
        valid_tags = {"text", "bash", "markdown", "json"}
        for i in range(0, len(fence_lines), 2):
            open_idx, open_line = fence_lines[i]
            close_idx, close_line = fence_lines[i+1]
            tag = open_line[3:].strip()
            assert tag in valid_tags, f"Line {open_idx}: Unexpected or missing language tag '{tag}'"
            assert close_line == "```", f"Line {close_idx}: Closing fence should be exactly '```', got '{close_line}'"

    def test_backtick_balance_outside_fences(self):
        content = read_skill()
        lines = content.splitlines()

        in_fence = False
        odd_backtick_lines = []
        for idx, line in enumerate(lines, 1):
            if line.strip().startswith("```"):
                in_fence = not in_fence
                continue
            if not in_fence:
                # Count backticks on this line
                count = line.count("`")
                if count % 2 != 0:
                    odd_backtick_lines.append((idx, count, line))

        assert not odd_backtick_lines, f"Found lines with unclosed/odd backticks: {odd_backtick_lines}"

    def test_links_and_anchors_valid(self):
        content = read_skill()
        # Find all markdown links [text](url)
        links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", content)
        assert len(links) >= 2, "Expected markdown links in SKILL.md"

        for anchor_text, url in links:
            if url.startswith("http://") or url.startswith("https://"):
                assert "github.com" in url or "reddit" in url
            elif url.startswith("#"):
                # Internal anchor link
                anchor = url[1:].lower()
                # Verify that some heading in content matches
                headings = [re.sub(r"[^a-z0-9\- ]", "", h.lower()).replace(" ", "-")
                            for h in re.findall(r"^#+\s+(.+)$", content, re.MULTILINE)]
                assert any(anchor in h for h in headings), f"Broken internal anchor: {url}"

    def test_no_hang_or_blind_upload_instructions(self):
        content = read_skill()

        # Ensure --upload is never recommended without explicit warning
        upload_mentions = [m.start() for m in re.finditer(r"--upload", content)]
        assert len(upload_mentions) > 0, "--upload should be documented"

        # Check warnings in Cursor rules and CLI table
        assert "Do not use `--upload` unless `client_secrets.json` is confirmed" in content
        assert "Disabled by default (gated by --upload)" in content
        assert "Omit the `--upload` flag for local, test, or CI execution." in content


class TestEdgeCaseExecution:
    """Stress test 3: Edge case CLI execution tests."""

    def test_main_help_output_parity(self):
        cmd = [sys.executable, "src/main.py", "--help"]
        res = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True)
        assert res.returncode == 0
        help_out = res.stdout

        expected_flags = [
            "--local", "--test",
            "--audio",
            "--text",
            "--title",
            "--subreddit",
            "--tts-engine", "--tts",
            "--voice",
            "--upload",
            "--output",
            "--fps"
        ]
        for flag in expected_flags:
            assert flag in help_out, f"Flag {flag} missing from python src/main.py --help"

    def test_invalid_tts_engine_argparse_error(self):
        cmd = [sys.executable, "src/main.py", "--tts-engine", "invalid_engine"]
        res = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True)
        # Argparse error must return exit code 2
        assert res.returncode == 2, f"Expected returncode 2, got {res.returncode}"
        assert "invalid choice: 'invalid_engine'" in res.stderr
        assert "choose from" in res.stderr
        assert "auto" in res.stderr
        assert "edge-tts" in res.stderr
        assert "elevenlabs" in res.stderr

    def test_invalid_fps_argparse_error(self):
        cmd = [sys.executable, "src/main.py", "--fps", "not_a_number"]
        res = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True)
        assert res.returncode == 2
        assert "invalid int value: 'not_a_number'" in res.stderr
