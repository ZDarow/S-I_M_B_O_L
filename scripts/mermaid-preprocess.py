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
import hashlib
import subprocess
import sys
import tempfile
import os
import re
from pathlib import Path

BOOK_DIR = Path("book")
SRC_DIR = BOOK_DIR / "src"
CACHE_DIR = SRC_DIR / "img" / "mermaid"
MERMAID_RE = re.compile(r'```mermaid\s*\n(.*?)```', re.DOTALL)
BACKUP_PREFIX = ".mermaid-backup."


def find_mmdc() -> str | None:
    for c in [
        Path("node_modules/.bin/mmdc"),
        BOOK_DIR / "node_modules" / ".bin" / "mmdc",
        Path("../node_modules/.bin/mmdc"),
    ]:
        if c.is_file():
            return str(c.resolve())
    for p in os.environ.get("PATH", "").split(os.pathsep):
        mmdc = Path(p) / "mmdc"
        if mmdc.is_file():
            return str(mmdc)
    return None


def render_svg(mermaid_source: str, output: Path) -> bool:
    mmdc = find_mmdc()
    if not mmdc:
        return False
    with tempfile.NamedTemporaryFile(mode="w", suffix=".mmd",
                                     delete=False, encoding="utf-8") as tmp:
        tmp.write(mermaid_source)
        tmp_path = tmp.name
    try:
        r = subprocess.run(
            [mmdc, "-i", tmp_path, "-o", str(output),
             "-b", "transparent", "-w", "1200"],
            capture_output=True, text=True, timeout=30,
        )
        return r.returncode == 0 and output.exists() and output.stat().st_size >= 50
    except (subprocess.TimeoutExpired, OSError):
        return False
    finally:
        try: os.unlink(tmp_path)
        except OSError: pass


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
        h = hashlib.sha256(source.encode()).hexdigest()[:16]
        svg_file = cache_dir / f"{h}.svg"

        if not svg_file.exists():
            if not render_svg(source, svg_file):
                print(f"  ✗ {md_path.name}: hash={h} — ошибка рендера", file=sys.stderr)
                failed += 1
                return m.group(0)
            size = svg_file.stat().st_size
            print(f"  ✓ {md_path.name}: hash={h} ({size/1024:.1f} KB)", file=sys.stderr)

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
        print(f"  → {md_path.name}: {changes} замен, {failed} ошибок", file=sys.stderr)
    elif changes > 0:
        print(f"  → {md_path.name}: все блоки уже были заменены", file=sys.stderr)

    return changes


def restore_file(md_path: Path) -> bool:
    """Восстановить .md файл из бэкапа."""
    backup = md_path.with_suffix(md_path.suffix + BACKUP_PREFIX)
    if backup.exists():
        backup.replace(md_path)
        print(f"  ✓ {md_path.name}: восстановлен", file=sys.stderr)
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

    cache_dir = Path.cwd() / CACHE_DIR
    src_dir = Path.cwd() / SRC_DIR

    if args.restore:
        print("Mermaid: восстановление .md файлов...", file=sys.stderr)
        restored = 0
        for md_path in sorted(src_dir.rglob("*.md")):
            if restore_file(md_path):
                restored += 1
        print(f"  Восстановлено: {restored} файлов", file=sys.stderr)
        # Удаление оставшихся бэкапов
        for bak in src_dir.rglob(f"*{BACKUP_PREFIX}"):
            bak.unlink()
        return

    # Проверка mmdc
    mmdc = find_mmdc()
    if not mmdc:
        print("⚠ mmdc не найден. Установите: npm install @mermaid-js/mermaid-cli",
              file=sys.stderr)
        print("  Или: PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium npm install @mermaid-js/mermaid-cli",
              file=sys.stderr)
        sys.exit(1)

    cache_dir.mkdir(parents=True, exist_ok=True)

    print(f"Mermaid: обход {src_dir}...", file=sys.stderr)
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
                    h = hashlib.sha256(source.encode()).hexdigest()[:16]
                    svg_file = cache_dir / f"{h}.svg"
                    if not svg_file.exists():
                        if render_svg(source, svg_file):
                            print(f"  ✓ {md_path.name}: {h}.svg", file=sys.stderr)
                        else:
                            print(f"  ✗ {md_path.name}: {h} — ошибка", file=sys.stderr)
                    else:
                        print(f"  · {md_path.name}: {h} — кеш", file=sys.stderr)

    total_svg = len(list(cache_dir.glob("*.svg")))
    print(f"\nГотово: {total_files} файлов, {total_changes} замен, "
          f"{total_svg} SVG в кеше ({cache_dir})", file=sys.stderr)


if __name__ == "__main__":
    main()
