# Руководство по ремонту Renault Symbol

Технический справочник-руководство по ремонту и эксплуатации Renault Symbol (Thalia).

[![Build & Deploy](https://github.com/mi/reno-symbol.ru/actions/workflows/deploy.yml/badge.svg)](https://github.com/mi/reno-symbol.ru/actions/workflows/deploy.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## О проекте

Электронное руководство, созданное с использованием [mdBook](https://github.com/rust-lang/mdBook).
Содержит проверенные технические данные: характеристики двигателей, трансмиссий, ходовой части,
электрооборудования и кузова Renault Symbol (Thalia) всех поколений.

### Технический стек

| Компонент | Технология |
|-----------|-----------|
| Сборщик | [mdBook](https://github.com/rust-lang/mdBook) (Rust) |
| Исходники | Markdown + Mermaid (диаграммы) |
| PDF | mdbook-pdf + Chromium (рендеринг) |
| Диаграммы | Mermaid.js → SVG (mmdc) |
| CI/CD | GitHub Actions → GitHub Pages |
| Контейнер | Docker (многостадийная сборка) |
| Качество | markdownlint, pre-commit hooks, hunspell |

## Быстрый старт

```bash
# Установка зависимостей (Linux)
make install-deps

# Сборка книги (HTML + PDF)
make build

# Локальный сервер с автообновлением
make serve
# Открыть: http://localhost:3000
```

### Docker

```bash
# Сборка образа
make docker-build

# Сборка книги в контейнере
make docker-run
```

## Цели Makefile

### Сборка
| Цель | Описание |
|------|----------|
| `make build` | Полная сборка (Mermaid → HTML → PDF → пост-обработка) |
| `make pdf` | Сборка только PDF |
| `make serve` | Локальный сервер с livereload |
| `make clean` | Очистка результатов сборки |

### Качество
| Цель | Описание |
|------|----------|
| `make validate` | Сборка + линтинг + ссылки + орфография |
| `make lint` | Линтинг Markdown (markdownlint) |
| `make fmt` | Удаление trailing whitespace |
| `make spellcheck` | Проверка орфографии (hunspell) |
| `make check-links` | Проверка битых ссылок |

### Mermaid
| Цель | Описание |
|------|----------|
| `make mermaid` | Рендеринг Mermaid → SVG (кеширование) |
| `make mermaid-restore` | Восстановить .md из бэкапов |

### Docker
| Цель | Описание |
|------|----------|
| `make docker-build` | Сборка Docker-образа |
| `make docker-run` | Сборка книги в контейнере |

## Структура проекта

```
book/
├── book.toml          # конфигурация mdBook
├── theme/             # кастомные CSS/JS/SW темы
├── src/               # исходники Markdown
│   ├── README.md      # введение
│   ├── SUMMARY.md     # оглавление
│   ├── dvigatel/      # двигатель (3.*)
│   ├── transmissiya/  # трансмиссия (4.*)
│   ├── hodovaya/      # ходовая часть (5.*)
│   ├── rulevoe/       # рулевое управление (6.*)
│   ├── tormoza/       # тормозная система (7.*)
│   ├── elektrika/     # электрооборудование (8.*)
│   ├── kuzov/         # кузов (9.*)
│   ├── shemy/         # электрические схемы
│   ├── areodinamika/  # аэродинамика
│   └── statyi/        # статьи
├── book/              # скомпилированный вывод (gitignored)
scripts/               # утилиты (mermaid, PDF, sitemap, 404)
├── mermaid-preprocess.py
├── pdf-a4.py
├── sitemap.py
├── 404.html
└── pre-commit         # pre-commit hook (установка: `make install-hooks`)
```

## Разработка и контрибьюция

1. Форкните репозиторий
2. Создайте ветку: `git checkout -b feature/my-section`
3. Внесите изменения
4. Проверьте качество: `make validate`
5. Откройте pull request

### Pre-commit hook

```bash
make install-hooks   # установить pre-commit hook
```

Хук проверяет:
- Сборку mdBook
- Внутренние ссылки в изменённых файлах
- Наличие TODO/FIXME маркеров

## Требования к окружению

- **mdBook** — сборщик книги
- **make** — автоматизация команд
- **Python 3** — скрипты пост-обработки
- **Node.js + npm** — mermaid-cli (опционально, для диаграмм)
- **Chromium** — PDF-генерация (опционально)
- **Docker** — контейнерная сборка (опционально)

## Лицензия

MIT. Подробнее в файле [LICENSE](LICENSE).
