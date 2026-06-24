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

Зависимости: Node.js + @mermaid-js/mermaid-cli
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

CACHE_DIR_REL = Path("src/img/mermaid")
MAX_BLOCK_LEN = 20_000
MMDC_TIMEOUT = 30

MERMAID_RE = re.compile(r'```mermaid\s*\n(.*?)```', re.DOTALL)


# ─── mmdc ────────────────────────────────────────────────────────────────

def find_mmdc() -> str | None:
    for c in [Path("node_modules/.bin/mmdc"),
              Path("../node_modules/.bin/mmdc")]:
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
            capture_output=True, text=True, timeout=MMDC_TIMEOUT,
        )
        if r.returncode != 0:
            return False
        return output.exists() and output.stat().st_size >= 50
    except (subprocess.TimeoutExpired, OSError):
        return False
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


# ─── Обработка книги ────────────────────────────────────────────────────

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
                        h = hashlib.sha256(source.encode()).hexdigest()[:16]
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
        h = hashlib.sha256(source.encode()).hexdigest()[:16]
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


# ─── Главная ────────────────────────────────────────────────────────────

def main():
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
        print(f"Mermaid: ⚠ неподдерживаемый формат JSON", file=sys.stderr)

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
        print(f"Mermaid: рендер {n} SVG...", file=sys.stderr)
        ok = 0
        for h, src in sorted(pending.items()):
            svg_file = cache_dir / f"{h}.svg"
            if render_svg(src, svg_file):
                ok += 1
                print(f"  ✓ {h}.svg", file=sys.stderr)
            else:
                print(f"  ✗ {h}", file=sys.stderr)
        print(f"  Итого: {ok}/{n}", file=sys.stderr)
    else:
        c = len(list(cache_dir.glob("*.svg")))
        if c:
            print(f"Mermaid: {c} SVG в кеше", file=sys.stderr)

    # Фаза 2: замена блоков
    replace_in_book(book_sections, cache_dir, src_dir)

    # Фаза 3: вывод
    sys.stdout.write(json.dumps(data, ensure_ascii=False))
    sys.stdout.write("\n")
    sys.stdout.flush()


if __name__ == "__main__":
    main()
