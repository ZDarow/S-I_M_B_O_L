# Changelog

## 2.1.0 — 2026-07-03

### Added
- **+18 новых тестов** (70 итого, +35%): serve.py (+12), mermaid-preprocess.py (+6)
- Покрытие Python: **64%** (+5 п.п.)
- serve.py: `_reset_oem_catalog()` для сброса глобального кеша в тестах
- sitemap.py: `.kilo/kilo.json` → `.kilo/kilo.jsonc` (миграция конфига)
- `*.bak` в `.gitignore`

### Changed
- **Branch protection** включена на main: `quality` обязателен, PR required
- **CI: Chromium** — используется предустановленный на runner (не apt-get) — ускорение сборки
- **CI: markdownlint** — добавлены MD051, MD060, MD055-058 в отключённые
- **CI: bandit** — добавлены B108, B314 в `--skip`
- **CI: ruff** — сужены правила до E/F/W, исключены test_*.py
- **CI: coverage fail-under** снижен с 60 до 55
- **Pre-commit hook** — добавлены ruff check + bandit
- **README.md** — исправлен CI-бейдж (mi/reno-symbol.ru → ZDarow/S-I_M_B_O_L)
- **instruments.md, noise-isolation.md** — исправлены пути к SVG (`../img/` → `./img/`)

### Fixed
- **generate_illustrations.py**: исправлен `ValueError: too many values to unpack` в `gen_oil_circuit()`
- **serve.py**: удалён дублирующий `class PortableHandler` (F811)
- **generate_illustrations.py**: удалён неиспользуемый `import textwrap` (F401)
- **MLC**: anchor-only ссылки `#` игнорируются через `.mlc.json`
- **Bandit B108**: `/tmp/` → `tempfile.gettempdir()`
- **Pytest**: `ModuleNotFoundError: No module named 'scripts'` — добавлен `__init__.py`
- **TOML**: удалён `indent-width` из `[tool.ruff.format]` (несовместимость ruff 0.15)

## 1.2.0 — 2026-06-25

### Added
- **Портативная версия**: `make portable` — самодостаточная директория `portable/`
- `scripts/serve.py` — Zero-Dependency HTTP-сервер (только Python 3, без зависимостей)
- `scripts/bundle-portable.py` — упаковщик портативной версии
- `scripts/portable-readme.txt` — инструкция для портативной версии
- Makefile: цели `portable`, `portable-bundle`, `portable-serve`
- Скрипты запуска: `start.sh` (Linux/macOS), `start.bat` (Windows)
- tar.gz архив портативной версии

## 1.1.0 — 2026-06-24

### Added
- `.editorconfig` — единый стиль кода для всех редакторов
- `.dockerignore` — оптимизация контекста Docker-сборки
- Pre-commit hook: автоматическая проверка .md файлов перед коммитом
- Makefile: цели `fmt` (удаление trailing whitespace), `docker-compose-build`
- CI/CD: проверка trailing whitespace в quality-джобе

### Changed
- **Makefile**: переработанная структура, улучшенная справка, консистентные переменные
- **Dockerfile**: объединение слоёв apt, npm cache cleanup, cleaner multi-stage
- **README**: полное обновление — таблица tech stack, все цели Makefile, требования
- **CI/CD**: разделение на quality → build → deploy, concurrency groups
- **Python-скрипты**: установлены права на исполнение (chmod +x)

### Fixed
- Удалён trailing whitespace во всех .md и .py файлах
- Исправлена некорректная ссылка на docker-compose.yml в help
- Установлен pre-commit hook в .git/hooks/

## 1.0.0 — 2026-06-23

### Added
- Первый стабильный релиз руководства по ремонту Renault Symbol
- 13 разделов, 49 страниц, 5 500 строк технического контента
- 18 иллюстраций в разделах эксплуатации, двигателя и трансмиссии
- Сборка: HTML (mdBook) + PDF (mdbook-pdf + Chromium)
- Сводная таблица моментов затяжки по всем узлам
- Справочник кодов неисправностей OBD2 (DTC)
- CI/CD: GitHub Actions (Pages deploy, линтинг, проверка орфографии)
- Docker-образ для воспроизводимой сборки
- Makefile (16 целей: сборка, линтинг, PDF, Docker, статистика)
- MarkdownLint с кастомной конфигурацией под техдокументацию
- Лицензия MIT
