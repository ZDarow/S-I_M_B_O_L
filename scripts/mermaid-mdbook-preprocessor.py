#!/usr/bin/env python3
"""
mdBook preprocessor: конвертирует ```mermaid блоки в SVG-изображения.

Протокол mdbook 0.5 (раздельные процессы):
1. mdbook запускает: скрипт supports <renderer>
   → скрипт выводит "true\n" или "false\n" и завершается
2. mdbook запускает: скрипт < /dev/stdin
   → скрипт читает JSON книги из stdin
   → выводит изменённый JSON в stdout
   → завершается

Зависимости: Python 3.10+, Node.js + @mermaid-js/mermaid-cli
"""
import json
import logging
import os
import sys
from pathlib import Path

from mermaid_core import MERMAID_RE, hash_mermaid, render_svg

logger = logging.getLogger(__name__)

CACHE_DIR_REL = Path("src/img/mermaid")
MAX_BLOCK_LEN = 20_000


def collect_pending(book_sections, cache_dir) -> dict:
    """Собрать хеши mermaid-блоков без кеша."""
    pending = {}

    def walk(data):
        if isinstance(data, dict):
            if "Chapter" in data:
                ch = data["Chapter"]
                if "content" in ch and isinstance(ch["content"], str):
                    for m in MERMAID_RE.finditer(ch["content"]):
                        source = m.group(1).strip()
                        if not source or len(source) > MAX_BLOCK_LEN:
                            continue
                        h = hash_mermaid(source)
                        if not (cache_dir / f"{h}.svg").exists():
                            pending[h] = source
                if "sub_items" in ch:
                    for sub in ch["sub_items"]:
                        walk(sub)
        elif isinstance(data, list):
            for item in data:
                walk(item)
    walk(book_sections)
    return pending


def replace_in_book(book_sections, cache_dir, src_dir):
    """Заменить mermaid-блоки на ссылки на SVG."""
    def replacer(m):
        source = m.group(1).strip()
        if not source or len(source) > MAX_BLOCK_LEN:
            return m.group(0)
        h = hash_mermaid(source)
        svg_file = cache_dir / f"{h}.svg"
        if svg_file.exists():
            rel = os.path.relpath(svg_file, src_dir)
            return f"![Диаграмма](../{rel})"
        return m.group(0)

    def walk(data):
        if isinstance(data, dict):
            if "Chapter" in data:
                ch = data["Chapter"]
                if "content" in ch and isinstance(ch["content"], str):
                    ch["content"] = MERMAID_RE.sub(replacer, ch["content"])
                if "sub_items" in ch:
                    for sub in ch["sub_items"]:
                        walk(sub)
        elif isinstance(data, list):
            for item in data:
                walk(item)
    walk(book_sections)


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s: %(message)s",
        stream=sys.stderr,
    )

    # --- Фаза 0: протокол mdbook ---
    if len(sys.argv) >= 3 and sys.argv[1] == "supports":
        sys.stdout.write("true\n")
        sys.stdout.flush()
        return

    # Читаем JSON
    raw = sys.stdin.read()
    if not raw.strip():
        return
    data = json.loads(raw)

    # Извлекаем sections
    if isinstance(data, list):
        if len(data) == 2 and isinstance(data[1], dict) and "items" in data[1]:
            book_sections = data[1]["items"]
        elif len(data) == 1 and isinstance(data[0], dict) and "sections" in data[0]:
            book_sections = data[0]["sections"]
        else:
            book_sections = data  # fallback: sections напрямую
    elif isinstance(data, dict) and "sections" in data:
        book_sections = data["sections"]
    else:
        book_sections = None
        logger.warning("Неподдерживаемый формат JSON")

    if book_sections is None or not isinstance(book_sections, list):
        # Не можем обработать — выводим как есть
        sys.stdout.write(raw)
        sys.stdout.flush()
        return

    # --- Подготовка ---
    book_root = Path.cwd().resolve()
    cache_dir = (book_root / CACHE_DIR_REL).resolve()
    src_dir = (book_root / "src").resolve()
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Фаза 1: рендеринг недостающих SVG
    pending = collect_pending(book_sections, cache_dir)
    if pending:
        n = len(pending)
        logger.info("Mermaid: рендер %d SVG...", n)
        ok = 0
        for h, src in sorted(pending.items()):
            svg_file = cache_dir / f"{h}.svg"
            if render_svg(src, svg_file):
                ok += 1
                logger.info("  ✓ %s.svg", h)
            else:
                logger.warning("  ✗ %s", h)
        logger.info("  Итого: %d/%d", ok, n)
    else:
        c = len(list(cache_dir.glob("*.svg")))
        if c:
            logger.info("Mermaid: %d SVG в кеше", c)

    # Фаза 2: замена блоков
    replace_in_book(book_sections, cache_dir, src_dir)

    # Фаза 3: вывод
    sys.stdout.write(json.dumps(data, ensure_ascii=False))
    sys.stdout.write("\n")
    sys.stdout.flush()


if __name__ == "__main__":
    main()
