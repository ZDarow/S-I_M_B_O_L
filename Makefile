# Makefile для проекта Руководство по ремонту Renault Symbol

MDBOOK := mdbook
BOOK_DIR := book
BUILD_DIR := $(BOOK_DIR)/book
HTML_DIR := $(BUILD_DIR)/html
PDF_DIR := $(BUILD_DIR)/pdf
SRC_DIR := $(BOOK_DIR)/src
BOT_DIR := bot
MERMAID_PRE := scripts/mermaid-preprocess.py

.PHONY: all build serve clean validate docker-build docker-run pdf install-deps lint check-links stats help mermaid mermaid-restore

all: build

## Рендеринг Mermaid → SVG (кеширование)
mermaid:
	PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium python3 $(MERMAID_PRE) --render-only

## Сборка книги (Mermaid SVG + HTML + PDF + пост-обработка)
build: mermaid-replace
	$(MDBOOK) build $(BOOK_DIR)
	python3 scripts/mermaid-preprocess.py --restore 2>/dev/null || true
	python3 scripts/pdf-a4.py book/book/pdf/output.pdf /tmp/out.pdf 2>/dev/null || echo "⚠️ PDF post-processing skipped"
	python3 scripts/sitemap.py --source $(HTML_DIR) 2>/dev/null || echo "⚠️ sitemap skipped"
	cp -n scripts/404.html $(HTML_DIR)/404.html 2>/dev/null || true
	cp $(PDF_DIR)/output.pdf $(HTML_DIR)/reno-symbol.pdf 2>/dev/null || true
	@echo "✅ Сборка завершена"

## Замена Mermaid-блоков на SVG в .md файлах (вызывается build)
mermaid-replace:
	python3 $(MERMAID_PRE)

## Восстановление .md файлов после сборки
mermaid-restore:
	python3 $(MERMAID_PRE) --restore

## Локальный сервер с автообновлением (http://localhost:3000)
serve:
	$(MDBOOK) serve $(BOOK_DIR) --open

## Очистка собранного вывода
clean:
	rm -rf $(BUILD_DIR)

## Проверка орфографии (требует hunspell + ru-словарь)
spellcheck:
	@echo "Проверка орфографии Markdown-файлов..."
	@for f in $$(find $(SRC_DIR) -name "*.md" ! -name "SUMMARY.md"); do \
		echo "  $$f"; \
		hunspell -d ru_RU -l $$f 2>/dev/null || true; \
	done

## Проверка битых ссылок
check-links:
	$(MDBOOK) build $(BOOK_DIR)
	@echo "Проверка внутренних ссылок (grep)..."
	@for f in $$(find $(SRC_DIR) -name '*.md'); do \
		grep -oP '\]\(\K[^)]+\.md' "$$f" 2>/dev/null | while read link; do \
			dir=$$(dirname "$$f"); \
			target="$$dir/$$link"; \
			[ -f "$$target" ] || echo "⚠️  BAD LINK in $$f: $$link -> $$target"; \
		done; \
	done

## Линтинг Markdown (требует markdownlint-cli)
lint:
	@echo "Проверка Markdown-стиля..."
	markdownlint '$(SRC_DIR)/**/*.md' -c .markdownlint.yaml || true

## Валидация: сборка + линтинг + ссылки + орфография
validate: build check-links lint spellcheck
	@echo "✅ Валидация пройдена"

## Установка зависимостей (Linux)
install-deps:
	@echo "Установка mdBook..."
	curl -fsSL https://github.com/rust-lang/mdBook/releases/latest/download/mdbook-x86_64-unknown-linux-gnu.tar.gz \
		| tar xzf - -C /usr/local/bin
	@echo "Установка mdbook-pdf..."
	curl -fsSL https://github.com/HollowMan6/mdbook-pdf/releases/download/v0.1.13/mdbook-pdf-v0.1.13-x86_64-unknown-linux-gnu \
		-o /usr/local/bin/mdbook-pdf && chmod +x /usr/local/bin/mdbook-pdf
	@echo "Установка mdbook-admonish..."
	curl -fsSL https://github.com/tommilligan/mdbook-admonish/releases/download/v1.20.0/mdbook-admonish-v1.20.0-x86_64-unknown-linux-gnu.tar.gz \
		| tar xzf - -C /usr/local/bin
	@echo "Установка Python-зависимостей..."
	pip3 install pikepdf 2>/dev/null || pip install pikepdf
	@echo "✅ Зависимости установлены"
	@echo "Для орфографии: sudo apt-get install hunspell hunspell-ru"

## Упаковка архива для распространения
dist: build
	tar czf reno-symbol-book-$$(date +%Y%m%d).tar.gz -C $(HTML_DIR) .
	@echo "Архив готов: reno-symbol-book-$$(date +%Y%m%d).tar.gz"

# Docker-команды

## Сборка Docker-образа
docker-build:
	docker build -t reno-symbol-book .

## Сборка книги в Docker-контейнере
docker-run:
	docker run --rm -v "$$(pwd)/book/book":/output reno-symbol-book

## Сборка PDF (пост-обработка включена в build)
pdf:
	$(MDBOOK) build $(BOOK_DIR)
	python3 scripts/pdf-a4.py
	@echo "PDF готов: $(PDF_DIR)/output.pdf"

# GitHub Pages

## Деплой в локальную папку для GitHub Pages
gh-pages: build
	mkdir -p gh-pages
	cp -r $(HTML_DIR)/* gh-pages/
	touch gh-pages/.nojekyll
	@echo "Страницы скопированы в gh-pages/"

## Показать статистику
stats:
	@echo "=== Статистика ==="
	@echo "Source .md: $$(find $(SRC_DIR) -name '*.md' ! -name 'SUMMARY.md' | wc -l)"
	@echo "Mermaid: $$(grep -r 'mermaid' $(SRC_DIR)/*.md $(SRC_DIR)/**/*.md 2>/dev/null | wc -l)"
	@echo "Изображения: $$(ls $(SRC_DIR)/img/*.{jpg,png} 2>/dev/null | wc -l)"
	@echo "Используемые img: $$(for f in $(SRC_DIR)/img/*.{jpg,png}; do n=$$(basename "$$f"); grep -rl "$$n" $(SRC_DIR)/*.md $(SRC_DIR)/**/*.md 2>/dev/null | wc -l | tr -d ' '; done | grep -v '^0$' | wc -l)"
	@echo "HTML страниц: $$(find $(HTML_DIR) -name '*.html' | wc -l)"
	@if [ -f "$(PDF_DIR)/output.pdf" ]; then \
		echo "PDF: $$(du -h $(PDF_DIR)/output.pdf | cut -f1)"; \
		python3 -c "import pikepdf; p=pikepdf.open('$(PDF_DIR)/output.pdf'); print('PDF страниц:', len(p.pages)); p.close()" 2>/dev/null || true; \
	fi

# Telegram-бот

## Перестроить поисковый индекс для Telegram-бота
bot-index:
	python3 $(BOT_DIR)/indexer.py

## Запустить Telegram-бота (требует BOT_TOKEN в окружении)
bot-run:
	python3 $(BOT_DIR)/main.py

## Установить зависимости Telegram-бота
bot-install:
	pip3 install -r $(BOT_DIR)/requirements.txt

help:
	@echo "Доступные цели:"
	@echo "  build         — собрать книгу (HTML + PDF + пост-обработка)"
	@echo "  serve         — локальный сервер с livereload"
	@echo "  clean         — очистить сборку"
	@echo "  validate      — сборка + линтинг + ссылки + орфография"
	@echo "  lint          — линтинг Markdown (markdownlint)"
	@echo "  spellcheck    — проверка орфографии (hunspell)"
	@echo "  check-links   — проверка битых ссылок"
	@echo "  dist          — упаковать архив"
	@echo "  docker-build  — собрать Docker-образ"
	@echo "  docker-run    — сборка в Docker"
	@echo "  pdf           — сборка PDF"
	@echo "  gh-pages      — подготовить для GitHub Pages"
	@echo "  stats         — статистика проекта"
	@echo "  install-deps  — установка pre-built бинарников"
	@echo "  bot-index     — перестроить поисковый индекс"
	@echo "  bot-run       — запустить Telegram-бота"
	@echo "  bot-install   — установить зависимости бота"
