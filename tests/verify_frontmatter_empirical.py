import sys
import os
import re
import subprocess
import yaml

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL_PATH = os.path.join(PROJECT_ROOT, "SKILL.md")

with open(SKILL_PATH, "r", encoding="utf-8") as f:
    content = f.read()

parts = content.split("---", 2)
assert len(parts) >= 3, "Frontmatter not properly bounded by ---"
fm = yaml.safe_load(parts[1])

print("=== YAML FRONTMATTER VERIFICATION ===")
required_fields = [
    "name", "version", "description", "author", "homepage",
    "repository", "license", "tags", "compatibility", "triggers",
    "inputs", "outputs"
]
for req in required_fields:
    assert req in fm, f"Missing required field: {req}"
    print(f"  [OK] Field present: {req}")

assert isinstance(fm["name"], str) and fm["name"] == "reddit-shorts-automation"
assert isinstance(fm["version"], str)
assert isinstance(fm["description"], str) and len(fm["description"]) > 20
assert isinstance(fm["author"], str)
assert isinstance(fm["homepage"], str)
assert isinstance(fm["repository"], str)
assert isinstance(fm["license"], str)
assert isinstance(fm["tags"], list) and len(fm["tags"]) > 0
assert isinstance(fm["compatibility"], dict)
assert "python" in fm["compatibility"]
assert "platforms" in fm["compatibility"]
assert "agents" in fm["compatibility"]
assert isinstance(fm["triggers"], list) and len(fm["triggers"]) > 0

print(f"  [OK] Triggers list has {len(fm['triggers'])} triggers:")
for t in fm["triggers"]:
    print(f"       - {t}")

assert isinstance(fm["inputs"], dict)
assert isinstance(fm["outputs"], dict)

# Check all input field specifications
for inp_name, inp_def in fm["inputs"].items():
    assert "type" in inp_def, f"Input {inp_name} missing 'type'"
    assert "description" in inp_def, f"Input {inp_name} missing 'description'"
    print(f"  [OK] Input definition: {inp_name} (type: {inp_def['type']})")

# Check all output field specifications
for out_name, out_def in fm["outputs"].items():
    assert "type" in out_def, f"Output {out_name} missing 'type'"
    assert "description" in out_def, f"Output {out_name} missing 'description'"
    print(f"  [OK] Output definition: {out_name} (type: {out_def['type']})")

print("\n=== CLI HELP PARITY CHECK ===")
res = subprocess.run([sys.executable, "src/main.py", "--help"], cwd=PROJECT_ROOT, capture_output=True, text=True)
assert res.returncode == 0, f"src/main.py --help returned non-zero code: {res.stderr}"
cli_flags = set(re.findall(r"(--[a-zA-Z0-9\-]+)", res.stdout)) - {"--help"}
print(f"  Detected CLI flags in src/main.py: {sorted(cli_flags)}")

table_section = parts[2].split("## 5. Full CLI Reference")[1].split("## 6.")[0]
for flag in cli_flags:
    assert flag in table_section, f"Flag {flag} missing in SKILL.md Section 5 table!"
    print(f"  [OK] CLI flag {flag} documented in Section 5 table")

print("\n🎉 ALL YAML FRONTMATTER AND CLI PARITY CHECKS PASSED EMPIRICALLY!")
