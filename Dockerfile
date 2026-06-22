# Docker-образ для сборки Руководства по ремонту Renault Symbol
# Использование:
#   docker build -t reno-symbol-book .
#   docker run --rm -v "$(pwd)/book/book":/output reno-symbol-book

FROM rust:alpine AS builder

# Установка зависимостей для mdBook
RUN apk add --no-cache musl-dev

# Установка mdBook
RUN cargo install mdbook --locked

WORKDIR /book

# Копирование исходников
COPY book/ .

# Сборка книги
RUN mdbook build

# Финальный образ — только HTML
FROM alpine:latest
RUN apk add --no-cache ca-certificates
COPY --from=builder /book/book /output

CMD ["cp", "-r", "/output/.", "/book-output"]
VOLUME ["/book-output"]
