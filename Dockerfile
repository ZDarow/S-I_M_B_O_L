# Docker-образ для сборки Руководства по ремонту Renault Symbol
# Использование:
#   docker build -t reno-symbol-book .
#   docker run --rm -v "$(pwd)/book/book:/output" reno-symbol-book
#
# Многостадийная сборка:
#   builder — установка зависимостей + сборка книги
#   alpine — минимальный образ с результатом
#
# Ключевое исправление: WORKDIR=/app, .puppeteerrc.cjs копируется
# в рабочую директорию для корректного обнаружения Puppeteer.

# ================================================================
# STAGE 1: Builder
# ================================================================
FROM ubuntu:24.04 AS builder

ENV DEBIAN_FRONTEND=noninteractive \
    PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium \
    npm_config_cache=/tmp/npm-cache

# Установка системных зависимостей (один слой)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl \
    chromium \
    nodejs npm \
    python3 python3-pip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Установка mdBook (pre-built)
RUN curl -fsSL https://github.com/rust-lang/mdBook/releases/latest/download/mdbook-x86_64-unknown-linux-gnu.tar.gz \
    | tar xzf - -C /usr/local/bin

# Установка mdbook-pdf (pre-built binary, v0.1.13)
RUN curl -fsSL https://github.com/HollowMan6/mdbook-pdf/releases/download/v0.1.13/mdbook-pdf-v0.1.13-x86_64-unknown-linux-gnu \
    -o /usr/local/bin/mdbook-pdf && chmod +x /usr/local/bin/mdbook-pdf

# Установка mermaid-cli и pikepdf
RUN npm install -g @mermaid-js/mermaid-cli --ignore-engines && \
    npm cache clean --force && \
    pip3 install --no-cache-dir pikepdf

WORKDIR /app

# Копирование исходников с корректными путями (см. mermaid-preprocess.py: Path("book"))
COPY book/ ./book/
COPY scripts/ ./scripts/
COPY .puppeteerrc.cjs ./    # Puppeteer ищет конфиг в CWD

# Mermaid-рендеринг + сборка книги (HTML + PDF) + пост-обработка
RUN python3 scripts/mermaid-preprocess.py --render-only && \
    python3 scripts/mermaid-preprocess.py && \
    mdbook build book && \
    python3 scripts/mermaid-preprocess.py --restore && \
    python3 scripts/pdf-a4.py

# ================================================================
# STAGE 2: Minimal runtime image
# ================================================================
FROM alpine:latest

RUN apk add --no-cache ca-certificates && \
    adduser -D -H -h /output nobody

COPY --from=builder --chown=nobody:nobody /app/book/book /output

USER nobody
VOLUME ["/output"]
CMD ["cp", "-r", "/output/.", "/book-output"]
