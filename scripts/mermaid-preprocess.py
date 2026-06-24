#!/usr/bin/env python3
"""
Препроцессор Mermaid-диаграмм для mdbook.

Заменяет ```mermaid блоки в .md файлах на SVG-изображения,
рендеря их через mmdc (mermaid-cli).

Использование:
    python3 scripts/mermaid-preprocess.py              # однократная замена
    python3 scripts/mermaid-preprocess.py --restore    # восстановить из git

Процесс:
  1. Сканирует book/src/*.md на ```mermaid блоки
  2. Рендерит SVG через mmdc, кеширует в book/src/img/mermaid/<hash>.svg
  3. Заменяет блоки на markdown-ссылки
  4. Все изменения в .md файлах можно откатить через --restore
"""
import logging
import os
import sys
from pathlib import Path

from mermaid_core import MERMAID_RE, find_mmdc, hash_mermaid, render_svg

logger = logging.getLogger(__name__)

BOOK_DIR = Path("book")
SRC_DIR = BOOK_DIR / "src"
CACHE_DIR = SRC_DIR / "img" / "mermaid"
BACKUP_PREFIX = ".mermaid-backup."


def process_file(md_path: Path, cache_dir: Path) -> int:
    """Обработать один .md файл: заменить mermaid блоки на SVG ссылки."""
    text = md_path.read_text(encoding="utf-8")
    original = text
    changes = 0
    failed = 0

    def replacer(m):
        nonlocal changes, failed
        source = m.group(1).strip()
        if not source:
            return m.group(0)
        h = hash_mermaid(source)
        svg_file = cache_dir / f"{h}.svg"

        if not svg_file.exists():
            if not render_svg(source, svg_file):
                logger.warning("  ✗ %s: hash=%s — ошибка рендера", md_path.name, h)
                failed += 1
                return m.group(0)
            size = svg_file.stat().st_size
            logger.info("  ✓ %s: hash=%s (%.1f KB)", md_path.name, h, size / 1024)

        rel = os.path.relpath(svg_file, md_path.parent)
        changes += 1
        return f"![Диаграмма]({rel})"

    text = MERMAID_RE.sub(replacer, text)

    if text != original:
        # Бэкап оригинального файла
        backup = md_path.with_suffix(md_path.suffix + BACKUP_PREFIX)
        backup.write_text(original, encoding="utf-8")
        # Запись изменённого
        md_path.write_text(text, encoding="utf-8")
        logger.info("  → %s: %d замен, %d ошибок", md_path.name, changes, failed)
    elif changes > 0:
        logger.info("  → %s: все блоки уже были заменены", md_path.name)

    return changes


def restore_file(md_path: Path) -> bool:
    """Восстановить .md файл из бэкапа."""
    backup = md_path.with_suffix(md_path.suffix + BACKUP_PREFIX)
    if backup.exists():
        backup.replace(md_path)
        logger.info("  ✓ %s: восстановлен", md_path.name)
        return True
    return False


def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Mermaid-препроцессор для mdbook")
    parser.add_argument("--restore", action="store_true",
                        help="Восстановить .md файлы из бэкапов")
    parser.add_argument("--render-only", action="store_true",
                        help="Только рендерить SVG, не заменять блоки")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        stream=sys.stderr,
    )

    cache_dir = Path.cwd() / CACHE_DIR
    src_dir = Path.cwd() / SRC_DIR

    if args.restore:
        logger.info("Mermaid: восстановление .md файлов...")
        restored = 0
        for md_path in sorted(src_dir.rglob("*.md")):
            if restore_file(md_path):
                restored += 1
        logger.info("  Восстановлено: %d файлов", restored)
        # Удаление оставшихся бэкапов
        for bak in src_dir.rglob(f"*{BACKUP_PREFIX}"):
            bak.unlink()
        return

    # Проверка mmdc
    mmdc = find_mmdc()
    if not mmdc:
        logger.error("mmdc не найден. Установите: npm install @mermaid-js/mermaid-cli")
        logger.error("  Или: PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium npm install @mermaid-js/mermaid-cli")
        sys.exit(1)

    cache_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Mermaid: обход %s...", src_dir)
    total_changes = 0
    total_files = 0
    for md_path in sorted(src_dir.rglob("*.md")):
        if md_path.name == "SUMMARY.md":
            continue
        text = md_path.read_text(encoding="utf-8")
        if "```mermaid" in text:
            total_files += 1
            if not args.render_only:
                c = process_file(md_path, cache_dir)
                total_changes += c
            else:
                # Только рендеринг
                for m in MERMAID_RE.finditer(text):
                    source = m.group(1).strip()
                    if not source:
                        continue
                    h = hash_mermaid(source)
                    svg_file = cache_dir / f"{h}.svg"
                    if not svg_file.exists():
                        if render_svg(source, svg_file):
                            logger.info("  ✓ %s: %s.svg", md_path.name, h)
                        else:
                            logger.warning("  ✗ %s: %s — ошибка", md_path.name, h)
                    else:
                        logger.info("  · %s: %s — кеш", md_path.name, h)

    total_svg = len(list(cache_dir.glob("*.svg")))
    logger.info(
        "\nГотово: %d файлов, %d замен, %d SVG в кеше (%s)",
        total_files, total_changes, total_svg, cache_dir,
    )


if __name__ == "__main__":
    main()
