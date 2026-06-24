# Changelog

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
