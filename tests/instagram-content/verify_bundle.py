"""Repeatable offline verification. All samples are synthetic, not Instagram data."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import unittest
import zipfile

BASE = Path(__file__).resolve().parent
PROJECT = BASE.parents[1]
SKILL = PROJECT / "skills/instagram-content"
OUTPUT = PROJECT / "exports/instagram-content"


def main():
    suite = unittest.defaultTestLoader.discover(str(BASE), pattern="test_tools.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        return 1
    paths = list(SKILL.rglob("*.md"))
    for path in paths:
        for target in re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
            if not target.startswith(("http:", "https:", "#")):
                assert (path.parent / target).exists(), f"Broken reference {path}: {target}"
    modes = sorted((SKILL / "references").glob("ig-*.md"))
    assert len(modes) == 13
    hooks = json.loads((SKILL / "references/hooks-ru.json").read_text(encoding="utf-8"))["hooks"]
    assert len(hooks) == 26 and len({h["id"] for h in hooks}) == 26
    for hook in hooks:
        assert all(hook.get(key) for key in ("name", "template", "example", "screen", "use", "avoid"))
    rubric = json.loads((SKILL / "references/profile-rubric.json").read_text(encoding="utf-8"))["criteria"]
    assert len(rubric) == 12 and sum(r["points"] for r in rubric) == 100
    source_license = PROJECT / "LICENSE"
    assert source_license.read_bytes() == (SKILL / "LICENSE").read_bytes()
    profile_file = BASE / "profile-synthetic.json"
    profile_file.write_text(json.dumps({"criteria": {rubric[0]["id"]: {
        "score": 6, "evidence": "Синтетический пример для проверки калькулятора"}}}, ensure_ascii=False), encoding="utf-8")
    results = {}
    for command in ("hook", "beats", "caption", "style", "clean", "swipe", "profile"):
        source = BASE / "speech.txt"
        if command == "swipe":
            source = BASE / "captured.tsv"
        if command == "profile":
            source = profile_file
        before = source.read_bytes()
        call = [sys.executable, str(SKILL / "scripts/content_tools.py"), command, str(source)]
        if command == "beats":
            call.extend(["--target", "30"])
        run = subprocess.run(call, capture_output=True, encoding="utf-8")
        assert run.returncode == 0, run.stderr
        results[command] = json.loads(run.stdout)
        assert before == source.read_bytes(), "Input was changed"
    bundle = subprocess.run([sys.executable, str(SKILL / "scripts/package.py"), "--output", str(OUTPUT)],
                            capture_output=True, encoding="utf-8")
    assert bundle.returncode == 0, bundle.stderr
    metadata = json.loads(bundle.stdout)
    with zipfile.ZipFile(metadata["archive"]) as z:
        assert z.testzip() is None
        assert not any("__pycache__" in n or n.endswith(".pyc") for n in z.namelist())
        for mode in modes:
            assert "instagram-content/references/" + mode.name in z.namelist()
        assert "instagram-content/scripts/content_tools.py" in z.namelist()
        document = z.read("CHATGPT-INSTAGRAM.txt").decode("utf-8")
        for mode in modes:
            assert "## Файл: references/" + mode.name in document
        assert "Copyright (c) 2026 Jake Schincariol" in document
    report = {"date": "2026-10-06", "unit_tests_passed": result.testsRun,
              "modes": len(modes), "hook_formulas": len(hooks), "profile_criteria": len(rubric),
              "license_preserved": True, "references_resolve": True,
              "cli_results": results, "package": metadata,
              "scope": "Offline synthetic fixtures. No cloud installation, Instagram connection or live performance test."}
    (BASE / "verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"tests": result.testsRun, "modes": len(modes), "hooks": len(hooks),
                      "cli_commands": len(results), "archive_sha256": metadata["sha256"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
