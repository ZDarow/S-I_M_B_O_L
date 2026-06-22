# Makefile для проекта Руководство по ремонту Renault Symbol

MDBOOK := mdbook
BOOK_DIR := book
BUILD_DIR := $(BOOK_DIR)/book
SRC_DIR := $(BOOK_DIR)/src

.PHONY: all build serve clean validate docker-build docker-run pdf install-deps lint

all: build

## Сборка книги
build:
	$(MDBOOK) build $(BOOK_DIR)

## Локальный сервер с автообновлением (http://localhost:3000)
serve:
	$(MDBOOK) serve $(BOOK_DIR) --open

## Очистка собранного вывода
clean:
	rm -rf $(BUILD_DIR)

## Проверка орфографии (требует hunspell + ru-словарь)
spellcheck:
	@echo "Проверка орфографии Markdown-файлов..."
	@for f in $$(find $(SRC_DIR) -name "*.md"); do \
		echo "  $$f"; \
		hunspell -d ru_RU -l $$f 2>/dev/null || true; \
	done

## Проверка битых ссылок (требует cargo-insta)
check-links:
	$(MDBOOK) build $(BOOK_DIR)
	@echo "Проверка ссылок..."
	cargo install linkcheck 2>/dev/null; linkcheck $(BUILD_DIR) 2>/dev/null || true

## Валидация: сборка + проверки
validate: build spellcheck
	@echo "✅ Валидация пройдена"

## Установка зависимостей (Linux)
install-deps:
	@echo "Установка mdBook..."
	@command -v cargo >/dev/null 2>&1 || { echo "Требуется Rust: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"; exit 1; }
	cargo install mdbook
	@echo "✅ Зависимости установлены"
	@echo "Для проверки орфографии: sudo apt-get install hunspell hunspell-ru"

## Упаковка архива для распространения
dist: build
	tar czf reno-symbol-book-$$(date +%Y%m%d).tar.gz -C $(BUILD_DIR) .
	@echo "📦 Архив готов: reno-symbol-book-$$(date +%Y%m%d).tar.gz"

# Docker-команды

## Сборка Docker-образа
docker-build:
	docker build -t reno-symbol-book .

## Сборка книги в Docker-контейнере
docker-run:
	docker run --rm -v "$$(pwd)/book":/book reno-symbol-book

# GitHub Pages

## Деплой в локальную папку для GitHub Pages
gh-pages: build
	mkdir -p gh-pages
	cp -r $(BUILD_DIR)/* gh-pages/
	cp -r $(BUILD_DIR)/.nojekyll gh-pages/ 2>/dev/null || true
	@echo "✅ Страницы скопированы в gh-pages/"

## Показать статистику
stats:
	@echo "=== Статистика ==="
	@echo "Markdown-файлов: $$(find $(SRC_DIR) -name '*.md' | wc -l)"
	@echo "Строк кода: $$(wc -l $(SRC_DIR)/**/*.md $(SRC_DIR)/*.md 2>/dev/null | tail -1 | awk '{print $$1}')"
	@echo "Размер HTML: $$(du -sh $(BUILD_DIR) 2>/dev/null | awk '{print $$1}')"
	@echo "Страниц HTML: $$(find $(BUILD_DIR) -name '*.html' | wc -l)"

help:
	@echo "Доступные цели:"
	@echo "  build       — собрать книгу (по умолчанию)"
	@echo "  serve       — локальный сервер с livereload"
	@echo "  clean       — очистить сборку"
	@echo "  validate    — сборка + проверка орфографии"
	@echo "  spellcheck  — проверка орфографии (hunspell)"
	@echo "  check-links — проверка битых ссылок"
	@echo "  dist        — упаковать архив"
	@echo "  docker-build — собрать Docker-образ"
	@echo "  docker-run  — сборка в Docker"
	@echo "  gh-pages    — подготовить для GitHub Pages"
	@echo "  stats       — статистика проекта"
	@echo "  install-deps — установка mdBook"
