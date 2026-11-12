"""
Empirical verification and stress testing of SKILL.md.
Validates YAML frontmatter, flag parity with src/main.py, JSON schema in Runbook 3,
and markdown structural integrity.
"""
import os
import sys
import json
import yaml
import re
import subprocess
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL_PATH = os.path.join(PROJECT_ROOT, "SKILL.md")


def load_frontmatter():
    with open(SKILL_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    parts = content.split("---", 2)
    assert len(parts) >= 3, "SKILL.md must have valid frontmatter enclosed in ---"
    data = yaml.safe_load(parts[1])
    return data, parts[2]


def test_frontmatter_required_fields():
    """Verify all required metadata fields exist and are well-typed."""
    fm, _ = load_frontmatter()
    required_keys = [
        "name", "version", "description", "author", "homepage",
        "repository", "license", "tags", "compatibility", "triggers",
        "inputs", "outputs"
    ]
    for key in required_keys:
        assert key in fm, f"Missing required frontmatter key: {key}"

    assert isinstance(fm["name"], str) and len(fm["name"]) > 0
    assert isinstance(fm["version"], str) and len(fm["version"]) > 0
    assert isinstance(fm["description"], str) and len(fm["description"]) > 10
    assert isinstance(fm["author"], str) and len(fm["author"]) > 0
    assert isinstance(fm["license"], str) and len(fm["license"]) > 0
    assert isinstance(fm["tags"], list) and len(fm["tags"]) >= 3
    assert isinstance(fm["compatibility"], dict)
    assert "python" in fm["compatibility"]
    assert "platforms" in fm["compatibility"]
    assert "agents" in fm["compatibility"]


def test_frontmatter_triggers_non_empty():
    """Verify triggers list exists and contains actionable intent phrases."""
    fm, _ = load_frontmatter()
    triggers = fm.get("triggers", [])
    assert isinstance(triggers, list), "Triggers must be a list"
    assert len(triggers) >= 5, f"Expected at least 5 trigger phrases, got {len(triggers)}"
    for t in triggers:
        assert isinstance(t, str) and len(t.strip()) > 0


def test_frontmatter_inputs_and_outputs():
    """Verify inputs and outputs dictionaries are well-formed."""
    fm, _ = load_frontmatter()
    inputs = fm.get("inputs", {})
    outputs = fm.get("outputs", {})
    assert isinstance(inputs, dict) and len(inputs) >= 5
    assert isinstance(outputs, dict) and len(outputs) >= 3

    for inp_name, inp_def in inputs.items():
        assert "type" in inp_def, f"Input {inp_name} missing 'type'"
        assert "description" in inp_def, f"Input {inp_name} missing 'description'"

    for out_name, out_def in outputs.items():
        assert "type" in out_def, f"Output {out_name} missing 'type'"
        assert "description" in out_def, f"Output {out_name} missing 'description'"


def test_cli_flags_parity_with_main_py():
    """Verify all CLI flags in python src/main.py --help match SKILL.md Section 5 table."""
    cmd = [sys.executable, "src/main.py", "--help"]
    res = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True)
    assert res.returncode == 0, f"--help failed: {res.stderr}"

    help_text = res.stdout

    # Parse options from argparse output (excluding built-in --help)
    cli_flags = set(re.findall(r"(--[a-zA-Z0-9\-]+)", help_text)) - {"--help"}
    assert len(cli_flags) >= 8, f"Too few CLI flags detected: {cli_flags}"

    with open(SKILL_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Verify every CLI flag from --help is documented in SKILL.md
    missing_flags = []
    for flag in cli_flags:
        if flag not in content:
            missing_flags.append(flag)

    assert not missing_flags, f"The following CLI flags are not documented in SKILL.md: {missing_flags}"


def test_markdown_sections_presence():
    """Verify all mandatory sections are present in SKILL.md."""
    _, body = load_frontmatter()
    expected_sections = [
        "## 1. Overview & Value Proposition",
        "## 2. When to Use & Trigger Conditions",
        "## 3. Progressive Disclosure Architecture",
        "## 4. Dedicated Agent Runbooks",
        "### Runbook 1: Claude Code Agent Execution",
        "### Runbook 2: Cursor (Composer & Agent Mode Rules)",
        "### Runbook 3: OpenAI Codex & Tool-Calling Agents",
        "## 5. Full CLI Reference",
        "## 6. Environment Variables & Fallback Architecture",
        "## 7. Troubleshooting & Error Recovery Guide for Agents",
        "## 8. Author & License Information"
    ]
    for sec in expected_sections:
        assert sec in body, f"Missing section in SKILL.md: {sec}"


def test_runbook_json_schemas():
    """Verify JSON schema and tool invocation payloads in Runbook 3 are valid JSON."""
    with open(SKILL_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Find JSON blocks
    json_blocks = re.findall(r"```json\s*(\{.*?\})\s*```", content, re.DOTALL)
    assert len(json_blocks) >= 3, f"Expected at least 3 JSON blocks in Runbook 3, found {len(json_blocks)}"

    for i, j_str in enumerate(json_blocks):
        try:
            parsed = json.loads(j_str)
            assert isinstance(parsed, dict)
        except Exception as e:
            pytest.fail(f"Invalid JSON in block {i}: {e}\nContent:\n{j_str}")


def test_code_fences_balance():
    """Ensure all markdown code fences are properly opened and closed."""
    with open(SKILL_PATH, "r", encoding="utf-8") as f:
        lines = f.readlines()

    open_fence = False
    fence_count = 0
    for idx, line in enumerate(lines, 1):
        if line.strip().startswith("```"):
            fence_count += 1
            open_fence = not open_fence

    assert fence_count > 0, "No code fences found in SKILL.md"
    assert not open_fence, f"Unbalanced code fence detected in SKILL.md (total count: {fence_count})"
