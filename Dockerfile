# Docker-образ для сборки Руководства по ремонту Renault Symbol
# Использование:
#   docker build -t reno-symbol-book .
#   docker run --rm -v "$(pwd)/book/book":/output reno-symbol-book

FROM ubuntu:24.04 AS builder

# Установка системных зависимостей
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl \
    # Chromium for PDF + mmdc
    chromium \
    # Node.js for mermaid-cli
    nodejs npm \
    # Python for post-processing
    python3 python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Установка mdBook (pre-built)
RUN curl -fsSL https://github.com/rust-lang/mdBook/releases/latest/download/mdbook-x86_64-unknown-linux-gnu.tar.gz \
    | tar xzf - -C /usr/local/bin

# Установка mdbook-pdf (pre-built binary, v0.1.13)
RUN curl -fsSL https://github.com/HollowMan6/mdbook-pdf/releases/download/v0.1.13/mdbook-pdf-v0.1.13-x86_64-unknown-linux-gnu \
    -o /usr/local/bin/mdbook-pdf && chmod +x /usr/local/bin/mdbook-pdf

# Установка mermaid-cli для рендеринга SVG
RUN npm install -g @mermaid-js/mermaid-cli --ignore-engines
# Puppeteer config: используем системный Chromium
RUN mkdir -p /root/.puppeteerrc && \
    echo '{"executablePath":"/usr/bin/chromium","args":["--no-sandbox"]}' \
    > /root/.puppeteerrc/puppeteer.json

# Установка pikepdf для пост-обработки
RUN pip3 install --no-cache-dir pikepdf

WORKDIR /book

# Копирование исходников и скриптов
COPY book/ .
COPY scripts/ /scripts/
COPY package.json /package.json
COPY .puppeteerrc.cjs /.puppeteerrc.cjs

# Mermaid-рендеринг + сборка книги (HTML + PDF)
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium
RUN python3 /scripts/mermaid-preprocess.py --render-only && \
    python3 /scripts/mermaid-preprocess.py && \
    mdbook build && \
    python3 /scripts/mermaid-preprocess.py --restore

# Пост-обработка PDF (Letter → A4)
RUN python3 /scripts/pdf-a4.py

# Финальный образ — только результат
FROM alpine:latest
RUN apk add --no-cache ca-certificates && \
    adduser -D -H -h /output nobody
COPY --from=builder /book/book /output
RUN chown -R nobody:nobody /output

USER nobody
VOLUME ["/output"]
CMD ["cp", "-r", "/output/.", "/book-output"]
