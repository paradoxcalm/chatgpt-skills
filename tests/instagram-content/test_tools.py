import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills/instagram-content"
spec = importlib.util.spec_from_file_location("content_tools", SKILL / "scripts/content_tools.py")
tools = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tools)


class EditorialToolsTests(unittest.TestCase):
    def test_unicode_and_compound_words(self):
        self.assertEqual(tools.words("Ёжик идёт café AI-помощник 3.5"), ["Ёжик", "идёт", "café", "AI-помощник", "3.5"])

    def test_cyrillic_timing(self):
        report = tools.beats("Один два три\nЧетыре пять", 60, 10)
        self.assertEqual(report["words"], 5)
        self.assertEqual(report["estimated_seconds"], 5)
        self.assertEqual(report["beats"][1]["start"], 3)
        self.assertEqual(report["over_target_seconds"], -5)

    def test_bad_rates_and_empty_speech(self):
        for rate in (0, -1, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                tools.beats("Привет", rate)
        with self.assertRaises(ValueError):
            tools.beats("\n 🙂")

    def test_hook_russian_opener(self):
        self.assertTrue(any("Вводная" in n for n in tools.hook("Всем привет, сегодня поговорим про модели")["notes"]))

    def test_caption_keywords_and_unicode(self):
        report = tools.caption("Локальная МОДЕЛЬ #ИИ", preview=5, keywords=["модель", "облако"])
        self.assertEqual(report["preview"], "Локал")
        self.assertEqual(report["missing_keywords"], ["облако"])
        self.assertEqual(report["hashtags"], ["#ИИ"])

    def test_style_flags_no_authorship_score(self):
        report = tools.style("В современном мире модель — помощник.")
        self.assertEqual(report["stock_phrases"], ["в современном мире"])
        self.assertEqual(report["em_dashes"], 1)
        self.assertNotIn("score", report)

    def test_clean_preserves_emoji_code_urls_and_numbers(self):
        source = "\ufeffТест — 42.5% 👨‍👩‍👧\n`код — пример` https://example.test/a—b\n```\nx — y\n```"
        clean = tools.clean(source)["text"]
        self.assertIn("Тест, 42.5% 👨‍👩‍👧", clean)
        self.assertIn("`код — пример`", clean)
        self.assertIn("https://example.test/a—b", clean)
        self.assertIn("x — y", clean)
        self.assertEqual(tools.clean(clean)["text"], clean)

    def test_swipe_ranking_and_invalid_rows(self):
        source = "account\tmedian\tviews\thook\na\t1000\t9000\tПример а\nb\t100\t1000\tПример б\nc\t0\t12\tОшибка\nd\t2\tNaN\tОшибка"
        report = tools.swipe(source)
        self.assertEqual([r["account"] for r in report["ranked"]], ["b", "a"])
        self.assertEqual(report["ranked"][0]["multiple"], 10)
        self.assertEqual(len(report["skipped"]), 2)
        self.assertFalse(report["ranked"][0]["source_verified"])

    def test_profile_missing_is_unknown(self):
        report = tools.profile({"criteria": {}})
        self.assertIsNone(report["total_out_of_100"])
        self.assertEqual(report["assessed_max"], 0)

    def test_profile_full_and_range(self):
        rubric = json.loads((SKILL / "references/profile-rubric.json").read_text(encoding="utf-8"))["criteria"]
        full = {r["id"]: {"score": r["points"], "evidence": "Синтетический тест"} for r in rubric}
        self.assertEqual(tools.profile(full)["total_out_of_100"], 100)
        full[rubric[0]["id"]]["score"] = 101
        with self.assertRaises(ValueError):
            tools.profile(full)

    def test_cli_utf8_and_bad_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "речь.txt"
            path.write_text("Один два три", encoding="utf-8")
            call = [sys.executable, str(SKILL / "scripts/content_tools.py"), "beats", str(path), "--wpm", "60"]
            ok = subprocess.run(call, capture_output=True, encoding="utf-8")
            self.assertEqual(ok.returncode, 0, ok.stderr)
            self.assertEqual(json.loads(ok.stdout)["estimated_seconds"], 3)
            bad = subprocess.run(call[:-1] + ["0"], capture_output=True, encoding="utf-8")
            self.assertEqual(bad.returncode, 2)
            self.assertIn("error", json.loads(bad.stderr))


if __name__ == "__main__":
    unittest.main(verbosity=2)
