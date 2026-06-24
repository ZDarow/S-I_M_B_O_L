# Docker-образ для сборки Руководства по ремонту Renault Symbol
# Использование:
#   docker build -t reno-symbol-book .
#   docker run --rm -v "$(pwd)/book/book:/output" reno-symbol-book
#
# Многостадийная сборка:
#   builder — установка зависимостей + сборка книги
#   alpine — минимальный образ с результатом

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

# Установка mermaid-cli для рендеринга SVG
RUN npm install -g @mermaid-js/mermaid-cli --ignore-engines && \
    mkdir -p /root/.puppeteerrc && \
    echo '{"executablePath":"/usr/bin/chromium","args":["--no-sandbox"]}' \
    > /root/.puppeteerrc/puppeteer.json && \
    npm cache clean --force

# Установка pikepdf для пост-обработки
RUN pip3 install --no-cache-dir pikepdf

WORKDIR /book

# Копирование исходников и скриптов
COPY book/ .
COPY scripts/ /scripts/
COPY .puppeteerrc.cjs /.puppeteerrc.cjs

# Mermaid-рендеринг + сборка книги (HTML + PDF)
RUN python3 /scripts/mermaid-preprocess.py --render-only && \
    python3 /scripts/mermaid-preprocess.py && \
    mdbook build && \
    python3 /scripts/mermaid-preprocess.py --restore

# Пост-обработка PDF (Letter → A4)
RUN python3 /scripts/pdf-a4.py

# ================================================================
# STAGE 2: Minimal runtime image
# ================================================================
FROM alpine:latest

RUN apk add --no-cache ca-certificates && \
    adduser -D -H -h /output nobody

COPY --from=builder /book/book /output
RUN chown -R nobody:nobody /output

USER nobody
VOLUME ["/output"]
CMD ["cp", "-r", "/output/.", "/book-output"]
