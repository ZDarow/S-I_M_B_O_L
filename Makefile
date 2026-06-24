# Makefile для проекта Руководство по ремонту Renault Symbol
# ==============================================================

MDBOOK      := mdbook
BOOK_DIR    := book
BUILD_DIR   := $(BOOK_DIR)/book
HTML_DIR    := $(BUILD_DIR)/html
PDF_DIR     := $(BUILD_DIR)/pdf
SRC_DIR     := $(BOOK_DIR)/src
SCRIPT_DIR  := scripts
MERMAID_PRE := $(SCRIPT_DIR)/mermaid-preprocess.py
BOT_DIR     := bot

# ── Переменные окружения ─────────────────────────────────────────
PUPPETEER ?= /usr/bin/chromium

# ── Фантомные цели ───────────────────────────────────────────────
.PHONY: all build build-html build-pdf sitemap post-process \
        serve clean validate \
        lint check-links spellcheck fmt \
        pdf dist portable portable-bundle portable-serve \
        docker-build docker-run \
        mermaid mermaid-replace mermaid-restore \
        gh-pages stats \
        install-deps \
        bot-index bot-run bot-install \
        install-hooks \
        help

# ── Сборка по умолчанию ─────────────────────────────────────────
all: build

# ══════════════════════════════════════════════════════════════════
# СБОРКА
# ══════════════════════════════════════════════════════════════════

## Рендеринг Mermaid → SVG (кеширование, без замены в .md)
mermaid:
	PUPPETEER_EXECUTABLE_PATH=$(PUPPETEER) python3 $(MERMAID_PRE) --render-only

## Замена Mermaid-блоков на SVG-ссылки в .md файлах
mermaid-replace:
	python3 $(MERMAID_PRE)

## Восстановление .md файлов после сборки
mermaid-restore:
	python3 $(MERMAID_PRE) --restore

## Сборка HTML через mdBook (с Mermaid)
build-html: export PUPPETEER_EXECUTABLE_PATH = $(PUPPETEER)
build-html: mermaid-replace
	$(MDBOOK) build $(BOOK_DIR)
	python3 $(MERMAID_PRE) --restore 2>/dev/null || true

## Сборка PDF через mdbook-pdf
build-pdf: build-html
	python3 $(SCRIPT_DIR)/pdf-a4.py $(PDF_DIR)/output.pdf $(PDF_DIR)/output-a4.pdf 2>/dev/null \
		|| echo "⚠️  PDF post-processing skipped"
	@if [ -f "$(PDF_DIR)/output-a4.pdf" ]; then \
		mv $(PDF_DIR)/output-a4.pdf $(PDF_DIR)/output.pdf; \
	fi

## Генерация sitemap.xml
sitemap:
	python3 $(SCRIPT_DIR)/sitemap.py --source $(HTML_DIR) 2>/dev/null \
		|| echo "⚠️  sitemap skipped"

## Пост-обработка: 404, PDF копия
post-process:
	cp -n $(SCRIPT_DIR)/404.html $(HTML_DIR)/404.html 2>/dev/null || true
	cp $(PDF_DIR)/output.pdf $(HTML_DIR)/reno-symbol.pdf 2>/dev/null || true

## Полная сборка книги (Mermaid → HTML → PDF → пост-обработка)
build: build-pdf sitemap post-process
	@echo "✅ Сборка завершена"

## Сборка только PDF
pdf: export PUPPETEER_EXECUTABLE_PATH = $(PUPPETEER)
pdf: mermaid-replace
	$(MDBOOK) build $(BOOK_DIR)
	python3 $(MERMAID_PRE) --restore 2>/dev/null || true
	python3 $(SCRIPT_DIR)/pdf-a4.py
	@echo "✅ PDF готов: $(PDF_DIR)/output.pdf"

## Локальный сервер с автообновлением (http://localhost:3000)
serve:
	$(MDBOOK) serve $(BOOK_DIR) --open

## Очистка собранного вывода
clean:
	rm -rf $(BUILD_DIR)
	rm -f reno-symbol-book-*.tar.gz

# ══════════════════════════════════════════════════════════════════
# КАЧЕСТВО
# ══════════════════════════════════════════════════════════════════

## Линтинг Markdown (требует markdownlint-cli)
lint:
	@echo "🔍 Проверка Markdown-стиля..."
	markdownlint '$(SRC_DIR)/**/*.md' -c .markdownlint.yaml || true

## Проверка орфографии (требует hunspell + ru-словарь)
spellcheck:
	@echo "🔍 Проверка орфографии Markdown-файлов..."
	@for f in $$(find $(SRC_DIR) -name "*.md" ! -name "SUMMARY.md"); do \
		echo "  $$f"; \
		hunspell -d ru_RU -l "$$f" 2>/dev/null || true; \
	done

## Проверка битых ссылок
check-links:
	@echo "🔍 Проверка внутренних ссылок..."
	@for f in $$(find $(SRC_DIR) -name '*.md'); do \
		grep -oP '\]\(\K[^)]+\.md' "$$f" 2>/dev/null | while read link; do \
			dir=$$(dirname "$$f"); \
			target="$$dir/$$link"; \
			[ -f "$$target" ] || echo "⚠️  BAD LINK in $$f: $$link -> $$target"; \
		done; \
	done

## Авто-форматирование: удаление trailing whitespace
fmt:
	@echo "🧹 Удаление trailing whitespace..."
	@find $(SRC_DIR) -name '*.md' -exec sed -i 's/[[:space:]]*$$//' {} +
	@echo "✅ Форматирование завершено"

## Валидация: сборка + линтинг + ссылки + орфография
validate: build check-links lint spellcheck
	@echo "✅ Валидация пройдена"

# ══════════════════════════════════════════════════════════════════
# ДИСТРИБУЦИЯ
# ══════════════════════════════════════════════════════════════════

## Упаковка архива для распространения
dist: build
	tar czf reno-symbol-book-$$(date +%Y%m%d).tar.gz -C $(HTML_DIR) .
	@echo "📦 Архив готов: reno-symbol-book-$$(date +%Y%m%d).tar.gz"

## Подготовка для GitHub Pages
gh-pages: build
	mkdir -p gh-pages
	cp -r $(HTML_DIR)/* gh-pages/
	touch gh-pages/.nojekyll
	@echo "📄 Страницы скопированы в gh-pages/"

# ══════════════════════════════════════════════════════════════════
# ПОРТАТИВНАЯ ВЕРСИЯ
# ══════════════════════════════════════════════════════════════════

## Собрать портативную версию (bundle)
portable: build
	python3 $(SCRIPT_DIR)/bundle-portable.py --no-build

## Упаковать портативную версию без пересборки
portable-bundle:
	python3 $(SCRIPT_DIR)/bundle-portable.py --no-build

## Запустить Zero-Dependency HTTP-сервер портативной версии
portable-serve:
	python3 $(SCRIPT_DIR)/serve.py

# ══════════════════════════════════════════════════════════════════
# DOCKER
# ══════════════════════════════════════════════════════════════════

## Сборка Docker-образа
docker-build:
	docker build -t reno-symbol-book .

## Сборка книги в Docker-контейнере
docker-run:
	docker run --rm -v "$$(pwd)/book/book:/output" reno-symbol-book

## Сборка Docker Compose (альтернатива)
docker-compose-build:
	mkdir -p book/book
	docker compose -f docker-compose.yml up --build

# ══════════════════════════════════════════════════════════════════
# ИНСТРУМЕНТЫ
# ══════════════════════════════════════════════════════════════════

## Установка pre-commit hook (локальный, из scripts/pre-commit)
install-hooks:
	cp $(SCRIPT_DIR)/pre-commit .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit
	@echo "✅ Pre-commit hook установлен"

## Установка зависимостей (Linux — pre-built бинарники)
install-deps:
	@echo "📦 Установка mdBook..."
	curl -fsSL https://github.com/rust-lang/mdBook/releases/latest/download/mdbook-x86_64-unknown-linux-gnu.tar.gz \
		| tar xzf - -C /usr/local/bin
	@echo "📦 Установка mdbook-pdf..."
	curl -fsSL https://github.com/HollowMan6/mdbook-pdf/releases/download/v0.1.13/mdbook-pdf-v0.1.13-x86_64-unknown-linux-gnu \
		-o /usr/local/bin/mdbook-pdf && chmod +x /usr/local/bin/mdbook-pdf
	@echo "📦 Установка Python-зависимостей..."
	pip3 install pikepdf 2>/dev/null || pip install pikepdf
	@echo "✅ Зависимости установлены"
	@echo "ℹ️  Для орфографии: sudo apt-get install hunspell hunspell-ru"
	@echo "ℹ️  Для mermaid: npm install @mermaid-js/mermaid-cli"

# ══════════════════════════════════════════════════════════════════
# TELEGRAM-БОТ
# ══════════════════════════════════════════════════════════════════

## Перестроить поисковый индекс для Telegram-бота
bot-index:
	python3 $(BOT_DIR)/indexer.py

## Запустить Telegram-бота (требует BOT_TOKEN в окружении)
bot-run:
	python3 $(BOT_DIR)/main.py

## Установить зависимости Telegram-бота
bot-install:
	pip3 install -r $(BOT_DIR)/requirements.txt

# ══════════════════════════════════════════════════════════════════
# СТАТИСТИКА
# ══════════════════════════════════════════════════════════════════

## Показать статистику проекта
stats:
	@echo "=== Статистика проекта ==="
	@echo "Source .md:      $$(find $(SRC_DIR) -name '*.md' ! -name 'SUMMARY.md' | wc -l)"
	@echo "Mermaid:         $$(grep -rl 'mermaid' $(SRC_DIR) 2>/dev/null | wc -l)"
	@echo "Изображения:     $$(ls $(SRC_DIR)/img/*.{jpg,png,jpeg} 2>/dev/null | wc -l)"
	@if [ -d "$(HTML_DIR)" ]; then \
		echo "HTML страниц:    $$(find $(HTML_DIR) -name '*.html' | wc -l)"; \
	fi
	@if [ -f "$(PDF_DIR)/output.pdf" ]; then \
		echo "PDF:             $$(du -h $(PDF_DIR)/output.pdf | cut -f1)"; \
		python3 -c "import pikepdf; p=pikepdf.open('$(PDF_DIR)/output.pdf'); print('PDF страниц:', len(p.pages)); p.close()" 2>/dev/null || true; \
	fi

# ══════════════════════════════════════════════════════════════════
# СПРАВКА
# ══════════════════════════════════════════════════════════════════

help:
	@echo "Руководство по ремонту Renault Symbol — Makefile"
	@echo ""
	@echo "Сборка:"
	@echo "  build          — полная сборка (HTML + PDF + пост-обработка)"
	@echo "  build-html     — только HTML (с Mermaid)"
	@echo "  build-pdf      — HTML + PDF"
	@echo "  sitemap        — генерация sitemap.xml"
	@echo "  post-process   — копирование 404, PDF в HTML"
	@echo "  serve          — локальный сервер с livereload (http://localhost:3000)"
	@echo "  clean          — очистить сборку"
	@echo "  pdf            — собрать только PDF"
	@echo ""
	@echo "Качество:"
	@echo "  validate       — сборка + линтинг + ссылки + орфография"
	@echo "  lint           — линтинг Markdown (markdownlint)"
	@echo "  fmt            — удалить trailing whitespace в .md"
	@echo "  spellcheck     — проверка орфографии (hunspell)"
	@echo "  check-links    — проверка битых ссылок"
	@echo ""
	@echo "Mermaid:"
	@echo "  mermaid        — рендеринг Mermaid → SVG (кеширование)"
	@echo "  mermaid-restore— восстановить .md из бэкапов"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build   — собрать Docker-образ"
	@echo "  docker-run     — сборка книги в Docker"
	@echo ""
	@echo "Дистрибуция:"
	@echo "  dist           — упаковать архив"
	@echo "  gh-pages       — подготовить для GitHub Pages"
	@echo ""
	@echo "Портативная версия:"
	@echo "  portable       — сборка + упаковка portable/"
	@echo "  portable-bundle— упаковка portable/ (без пересборки)"
	@echo "  portable-serve — Zero-Dependency HTTP-сервер"
	@echo ""
	@echo "Утилиты:"
	@echo "  install-deps   — установка pre-built бинарников (Linux)"
	@echo "  install-hooks  — установка pre-commit hook"
	@echo "  stats          — статистика проекта"
	@echo "  bot-index      — перестроить поисковый индекс бота"
	@echo "  bot-run        — запустить Telegram-бота"
	@echo "  bot-install    — установить зависимости бота"
