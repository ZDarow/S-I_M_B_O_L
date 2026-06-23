# Docker-образ для сборки Руководства по ремонту Renault Symbol
# Использование:
#   docker build -t reno-symbol-book .
#   docker run --rm -v "$(pwd)/book/book":/output reno-symbol-book

FROM rust:slim-bookworm AS builder

# Установка зависимостей для mdBook и mdbook-pdf
RUN apt-get update && apt-get install -y --no-install-recommends \
    musl-dev \
    chromium \
    chromium-sandbox \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Установка mdBook и mdbook-pdf
RUN cargo install mdbook mdbook-pdf --locked

WORKDIR /book

# Копирование исходников
COPY book/ .

# Сборка книги (HTML + PDF)
RUN mdbook build

# Финальный образ — HTML + PDF
FROM alpine:latest
RUN apk add --no-cache ca-certificates
COPY --from=builder /book/book /output

CMD ["cp", "-r", "/output/.", "/book-output"]
VOLUME ["/book-output"]
