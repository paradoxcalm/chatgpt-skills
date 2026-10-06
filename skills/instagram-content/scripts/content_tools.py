#!/usr/bin/env python3
"""Offline editorial helpers. Scores never predict reach or identify AI authorship."""
from __future__ import annotations

import argparse
import csv
import io
import json
import math
from pathlib import Path
import re
import sys
import unicodedata

ROOT = Path(__file__).resolve().parents[1]
WORD = re.compile(r"[^\W_]+(?:[.,]\d+)*(?:['’\-][^\W_]+)*", re.UNICODE)
STOCK = ("в современном мире", "ни для кого не секрет", "важно отметить", "это не просто",
         "вывести на новый уровень", "революционный", "раскрыть потенциал",
         "delve", "game changer", "in today's world", "unlock your potential")
WEAK = ("всем привет", "сегодня я расскажу", "в этом видео", "давайте поговорим",
        "stop scrolling", "hey guys", "in this video")


def words(text):
    return WORD.findall(unicodedata.normalize("NFC", text))


def positive(value):
    value = float(value)
    if not math.isfinite(value) or value <= 0:
        raise ValueError("Значение должно быть конечным числом больше нуля")
    return value


def hook(text, wpm=150):
    wpm = positive(wpm)
    tokens = words(text)
    if not tokens:
        raise ValueError("Нужен текст первой фразы")
    low = text.casefold().strip()
    notes = []
    if len(tokens) > 12:
        notes.append("Длинная первая фраза: проверь, можно ли раньше показать суть")
    if any(low.startswith(item) for item in WEAK):
        notes.append("Вводная фраза откладывает содержание")
    if not re.search(r"\d", text):
        notes.append("Чисел нет; конкретность оцени по смыслу, не добавляй выдуманные числа")
    return {"words": len(tokens), "characters": len(text),
            "estimated_seconds": round(len(tokens) * 60 / wpm, 2), "wpm": wpm,
            "notes": notes, "assessment": "Редакторские подсказки, не прогноз просмотров"}


def beats(text, wpm=150, target=None):
    wpm = positive(wpm)
    if target is not None:
        target = positive(target)
    rows, total = [], 0
    for line in text.splitlines():
        count = len(words(line))
        if not count:
            continue
        start = total * 60 / wpm
        total += count
        duration = count * 60 / wpm
        rows.append({"text": line.strip(), "words": count, "start": round(start, 2),
                     "end": round(total * 60 / wpm, 2), "duration": round(duration, 2),
                     "check_visual_change": duration > 4})
    if not rows:
        raise ValueError("Нужны строки произносимой речи")
    duration = total * 60 / wpm
    return {"words": total, "estimated_seconds": round(duration, 2), "wpm": wpm,
            "target_seconds": target,
            "over_target_seconds": round(duration - target, 2) if target is not None else None,
            "beats": rows,
            "limitation": "Оценка по словам. Паузы и чтение чисел не моделируются; замерь озвучку."}


def caption(text, preview=125, max_chars=2200, keywords=()):
    if preview < 1 or max_chars < 1:
        raise ValueError("Размеры должны быть больше нуля")
    low = text.casefold()
    hashtags = re.findall(r"(?<!\w)#[\w]+", text, re.UNICODE)
    return {"characters": len(text), "words": len(words(text)),
            "preview": text[:preview], "preview_characters": preview,
            "within_editorial_limit": len(text) <= max_chars, "editorial_limit": max_chars,
            "hashtags": hashtags,
            "missing_keywords": [k for k in keywords if k.casefold() not in low],
            "limitation": "Превью и лимит заданы для редакторской проверки; фактический интерфейс и лимиты не проверялись."}


def style(text):
    low = text.casefold()
    sentences = [s.strip() for s in re.split(r"[.!?]+|\n+", text) if words(s)]
    return {"words": len(words(text)), "characters": len(text),
            "stock_phrases": [s for s in STOCK if re.search(r"(?<!\w)" + re.escape(s) + r"(?!\w)", low)],
            "em_dashes": text.count("—"),
            "invisible_characters": [{"codepoint": f"U+{ord(c):04X}", "count": text.count(c)}
                                     for c in sorted(set(text)) if unicodedata.category(c) == "Cf"],
            "long_sentences": [s for s in sentences if len(words(s)) > 25],
            "assessment": "Проверка стиля. Символы и штампы не доказывают авторство или водяной знак ИИ."}


def clean(text):
    # Keep URLs, code, emoji sequences and zero-width joiners.
    # Only isolated prose em-dashes and two accidental characters are changed.
    protected = re.compile(r"```[\s\S]*?```|`[^`\n]*`|https?://\S+")
    changes = []

    def prose(part):
        for char, replacement, name in (("\ufeff", "", "BOM"), ("\u200b", "", "zero-width space")):
            n = part.count(char)
            if n:
                changes.append({"change": name, "count": n})
                part = part.replace(char, replacement)
        part, n = re.subn(r"[ \t]+—[ \t]+", ", ", part)
        if n:
            changes.append({"change": "Отдельное длинное тире заменено запятой; проверь грамматику", "count": n})
        return part

    out, last = [], 0
    for match in protected.finditer(text):
        out.extend((prose(text[last:match.start()]), match.group()))
        last = match.end()
    out.append(prose(text[last:]))
    return {"text": "".join(out), "changes": changes,
            "note": "Механическая правка, не окончательная редактура. Исходный файл не меняется."}


def swipe(text):
    reader = csv.DictReader(io.StringIO(text.lstrip("\ufeff")), delimiter="\t")
    required = {"account", "median", "views", "hook"}
    if not required.issubset(reader.fieldnames or []):
        raise ValueError("TSV требует столбцы account, median, views, hook")
    rows, skipped = [], []
    for line, row in enumerate(reader, 2):
        try:
            median = positive(row.get("median", ""))
            views = float(row.get("views", ""))
            if not math.isfinite(views) or views < 0:
                raise ValueError("views должно быть конечным неотрицательным числом")
            account = (row.get("account") or "").strip()
            if not account or not (row.get("hook") or "").strip():
                raise ValueError("Нужны account и hook")
            rows.append({"account": account, "views": views, "median": median,
                         "multiple": round(views / median, 3), "hook": row["hook"],
                         "url": row.get("url") or None, "observed_at": row.get("observed_at") or None,
                         "source_verified": False})
        except (ValueError, TypeError) as exc:
            skipped.append({"line": line, "reason": str(exc)})
    rows.sort(key=lambda r: r["views"] / r["median"], reverse=True)
    return {"ranked": rows, "skipped": skipped, "sample_size": len(rows),
            "accounts": len({r["account"] for r in rows}),
            "limitation": "Расчёт по предоставленным данным; подлинность, даты и медианы не проверялись. Связь не доказывает причину."}


def profile(data):
    if not isinstance(data, dict):
        raise ValueError("JSON профиля должен быть объектом")
    rubric = json.loads((ROOT / "references/profile-rubric.json").read_text(encoding="utf-8-sig"))
    if isinstance(rubric, dict):
        rubric = rubric["criteria"]
    if sum(item["points"] for item in rubric) != 100:
        raise ValueError("Сумма весов рубрики должна быть 100")
    supplied = data.get("criteria", data)
    if not isinstance(supplied, dict):
        raise ValueError("criteria должен быть объектом")
    unknown = set(supplied) - {item["id"] for item in rubric}
    if unknown:
        raise ValueError("Неизвестные критерии: " + ", ".join(sorted(unknown)))
    earned, assessed, rows = 0, 0, []
    for item in rubric:
        value = supplied.get(item["id"])
        if value is None:
            rows.append({"id": item["id"], "status": "нет данных", "max": item["points"]})
            continue
        if not isinstance(value, dict) or not str(value.get("evidence", "")).strip():
            raise ValueError("Оценка требует evidence: " + item["id"])
        score = value.get("score")
        if isinstance(score, bool) or not isinstance(score, (int, float)) or not math.isfinite(score) or not 0 <= score <= item["points"]:
            raise ValueError("Оценка вне диапазона: " + item["id"])
        earned += score
        assessed += item["points"]
        rows.append({"id": item["id"], "score": score, "max": item["points"], "evidence": value["evidence"]})
    return {"earned": earned, "assessed_max": assessed, "total_out_of_100": earned if assessed == 100 else None,
            "criteria": rows, "limitation": "Редакторская рубрика; подтверждение наблюдений выполняет пользователь или агент."}


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("hook", "beats", "caption", "style", "clean", "swipe", "profile"):
        child = sub.add_parser(name)
        child.add_argument("input", help="UTF-8 file, or - for stdin")
        if name in ("hook", "beats"):
            child.add_argument("--wpm", type=float, default=150)
        if name == "beats":
            child.add_argument("--target", type=float)
        if name == "caption":
            child.add_argument("--preview", type=int, default=125)
            child.add_argument("--max-chars", type=int, default=2200)
            child.add_argument("--keywords", default="", help="Comma-separated editorial keywords")
    args = parser.parse_args()
    try:
        text = sys.stdin.read() if args.input == "-" else Path(args.input).read_text(encoding="utf-8-sig")
        if args.command == "hook":
            result = hook(text, args.wpm)
        elif args.command == "beats":
            result = beats(text, args.wpm, args.target)
        elif args.command == "caption":
            result = caption(text, args.preview, args.max_chars, [s.strip() for s in args.keywords.split(",") if s.strip()])
        elif args.command == "profile":
            result = profile(json.loads(text))
        else:
            result = globals()[args.command](text)
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
