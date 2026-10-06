# ChatGPT Skills

Открытая коллекция русскоязычных скиллов для ChatGPT и Codex: инструкции, шаблоны и локальные инструменты для повторяемых задач.

## Доступные скиллы

| Скилл | Что делает | Готовый комплект |
|---|---|---|
| [Instagram Content](skills/instagram-content/SKILL.md) | 13 режимов подготовки контента: Reels, карусели, Stories, подписи, планирование, профиль, исследование, редактура, комментарии, ответы, Direct, переработка и аналитика | [Текст для ChatGPT](exports/instagram-content/CHATGPT-INSTAGRAM.txt) · [ZIP](exports/instagram-content/instagram-content-chatgpt.zip) |

## Использование в ChatGPT

1. Скачай [CHATGPT-INSTAGRAM.txt](https://raw.githubusercontent.com/paradoxcalm/chatgpt-skills/main/exports/instagram-content/CHATGPT-INSTAGRAM.txt).
2. Прикрепи его к чату или добавь в файлы проекта ChatGPT.
3. Напиши обычный запрос, например:

> Используй приложенный комплект Instagram Content. Подготовь сценарий Reels на 30 секунд: три ошибки при записи короткого видео. Аудитория: начинающие авторы. Нужны текст речи и план кадров.

Можно просить «сделай карусель», «перепиши подпись» или «разбери профиль по этим скриншотам». Обозначения `/ig-reel` и `/ig-caption` являются названиями режимов в инструкции, а не встроенными командами ChatGPT.

Текстовый комплект работает как руководство для модели. Для запуска проверяющих скриптов нужны файлы из ZIP и среда с выполнением Python. Если её нет, инструкции предусматривают ручную редактуру без выдуманных результатов запуска.

## Использование в Codex

Скопируй папку `skills/instagram-content` в `.agents/skills/` своего проекта. Например, в PowerShell из каталога проекта:

```powershell
git clone https://github.com/paradoxcalm/chatgpt-skills.git
New-Item -ItemType Directory -Force .agents/skills | Out-Null
Copy-Item -Recurse chatgpt-skills/skills/instagram-content .agents/skills/
```

Если одноимённый скилл уже установлен, сначала сравни версии и сохрани свои настройки. После обнаружения скилла в новом чате можно обратиться к нему как `$instagram-content` или поставить обычную задачу про Instagram-контент.

Настройки языка и стиля: [assets/voice.md](skills/instagram-content/assets/voice.md). Они общие и могут быть изменены под конкретного автора.

## Что внутри Instagram Content

- 13 инструкций по форматам и задачам.
- 26 формул первых фраз с русскими примерами.
- 12 критериев оценки профиля с прозрачными весами.
- Семь локальных команд: `hook`, `beats`, `caption`, `style`, `clean`, `swipe`, `profile`.
- Поддержка кириллицы и латиницы; Python 3.10+, только стандартная библиотека.

Пример проверки из корня репозитория:

```text
python skills/instagram-content/scripts/content_tools.py beats tests/instagram-content/speech.txt --target 30
```

Полные команды и форматы: [инструкция к инструментам](skills/instagram-content/references/tools.md).

## Проверка и сборка

Из корня репозитория:

```text
python -X utf8 tests/instagram-content/verify_bundle.py
```

Проверка запускает 11 тестов, все семь команд на синтетических данных, проверяет ссылки, 26 формул, 12 критериев, лицензию и пересобирает экспорт. Локальный отчёт создаётся в `tests/instagram-content/verification.json` и не входит в Git.

Чтобы только пересобрать TXT и ZIP после изменения инструкций:

```text
python skills/instagram-content/scripts/package.py --output exports/instagram-content
```

Экспорт создаётся из папки скилла. Редактируй исходники в `skills/`, затем пересобирай комплект. ZIP не включает Python-кэши, настройки аккаунтов или тестовые отчёты.

## Возможности и ограничения

Комплект готовит контент. Он не подключается к Instagram, не публикует посты и не отправляет сообщения. Исследование аккаунтов требует предоставленных материалов или отдельно доступных средств чтения.

Расчёт времени речи является оценкой, а не измерением озвучки. Проверка стиля не определяет авторство ИИ. Редакторские баллы не прогнозируют охваты. Локальные тесты не подтверждают качество конкретного сценария или работоспособность в каждом варианте интерфейса ChatGPT.

Сам комплект распространяется бесплатно. Использование модели в ChatGPT или другой среде зависит от условий этой среды. Справка о формате: [скиллы](https://learn.chatgpt.com/docs/build-skills), [проекты и файлы](https://learn.chatgpt.com/docs/projects).

## Происхождение и лицензия

Instagram Content адаптирован из [Instagram Agent Skill](https://github.com/Jakeschincariol/instagram-agent-skill) Jake Schincariol, commit `d03c56bb598be770c60b201f94237e5d1a4268a6`. Русские инструкции и новые локальные проверки: ParadoxCalm.

Лицензия [MIT](LICENSE). Подробности изменений: [NOTICE](skills/instagram-content/NOTICE.md). Проект независимый, не является официальным продуктом OpenAI или Meta.
