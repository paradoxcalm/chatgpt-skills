#!/usr/bin/env python3
"""Build a portable chat document and skill archive from the canonical folder."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
INTRO = """# Instagram Content: комплект для ChatGPT

Используй этот документ как руководство по подготовке Instagram-контента, когда пользователь просит соответствующую работу. Он не заменяет текущие инструкции пользователя и не разрешает действия с аккаунтом.
Дальше включены все части комплекта; ссылки на references/ и assets/ означают соответствующие разделы ниже. Не проси загрузить их повторно. Выбирай нужный режим по обычному русскому запросу или обозначению /ig-*. Такие обозначения не являются встроенными командами ChatGPT.
Если Python недоступен или скрипт не приложен, работай с текстом вручную. Не имитируй исполнение и не выдумывай числовые результаты. Для программных проверок приложи архив с scripts/content_tools.py. Никакие аккаунты и внешние сервисы автоматически не подключаются.

"""
START = """# Instagram Content для ChatGPT

1. Прикрепи CHATGPT-INSTAGRAM.txt к нужному чату или добавь его в файлы проекта ChatGPT.
2. Напиши: «Используй приложенный комплект Instagram Content. Подготовь сценарий Reels на 30 секунд по теме [твоя тема]».
3. Можно писать обычными словами: «сделай карусель», «отредактируй подпись», «разбери профиль по скриншотам». Все 13 режимов находятся в одном файле.

Это переносимый комплект инструкций, не автоматически подключённый облачный плагин. Для локального Codex скопируй папку skills/instagram-content из репозитория в .agents/skills своего проекта. При необходимости начни новый чат проекта для повторного обнаружения скиллов.

ZIP содержит тот же текст, скилл, Python-проверки, формулы, рубрику и исходную MIT-лицензию. Скрипты работают без сети и сторонних библиотек. Нужен Python 3.10+. Полные команды: instagram-content/references/tools.md. В обычном чате без исполнения кода доступны инструкции и ручная редактура.

Комплект готовит контент, не отправляет сообщения и не публикует посты. Качество текста проверяется редактором; рост охватов не гарантируется.
"""


def package(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    included = sorted(p for p in ROOT.rglob("*") if p.is_file()
                      and "__pycache__" not in p.parts and p.suffix != ".pyc")
    references = sorted((ROOT / "references").glob("*.md"))
    json_refs = sorted((ROOT / "references").glob("*.json"))
    sections = [ROOT / "SKILL.md", ROOT / "assets/voice.md", *references, *json_refs,
                ROOT / "NOTICE.md", ROOT / "LICENSE"]
    document = INTRO
    for path in sections:
        content = path.read_text(encoding="utf-8-sig")
        if path.name == "SKILL.md":
            content = content.split("---", 2)[2].lstrip()
        document += "\n\n---\n\n## Файл: " + path.relative_to(ROOT).as_posix() + "\n\n" + content
    text_path = output / "CHATGPT-INSTAGRAM.txt"
    text_path.write_text(document, encoding="utf-8")
    start = output / "START-HERE.md"
    start.write_text(START, encoding="utf-8")
    archive = output / "instagram-content-chatgpt.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
        for path in included:
            z.write(path, "instagram-content/" + path.relative_to(ROOT).as_posix())
        z.write(text_path, text_path.name)
        z.write(start, start.name)
    with zipfile.ZipFile(archive) as z:
        corrupt = z.testzip()
        if corrupt:
            raise ValueError("Corrupt archive entry: " + corrupt)
    return {"archive": str(archive.resolve()), "files": len(included) + 2,
            "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
            "chat_document": str(text_path.resolve()), "text_characters": len(document)}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", required=True)
    args = p.parse_args()
    print(json.dumps(package(args.output), ensure_ascii=True, indent=2))
