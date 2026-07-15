"""
Пост-обработка сборки: создаёт data/search-text.json — текстовый индекс
для кастомного поиска по кириллице.

mdBook использует elasticlunr с English pipeline, который вырезает
все не-ASCII символы. Русский текст в индекс не попадает.
Этот скрипт извлекает текст из built HTML-файлов и формирует
JSON с {url, title, breadcrumbs, body} для substring-поиска.

Вызывается из _copy_artifacts.py после mdbook build.
"""

import json
import re
from pathlib import Path


def extract_text(html_dir: Path) -> list[dict]:
    """Извлечь текст из всех HTML-файлов сборки (кроме print.html)."""
    documents = []

    for html_file in sorted(html_dir.glob("*.html")):
        name = html_file.name
        # Пропускаем print-версию (все главы в одном файле) и 404
        if name in ("print.html", "404.html"):
            continue

        content = html_file.read_text(encoding="utf-8")

        # Извлекаем title
        title_match = re.search(r"<title>(.*?)</title>", content, re.DOTALL)
        title = title_match.group(1).strip() if title_match else name

        # Извлекаем body text
        body_match = re.search(
            r'<main[^>]*>\s*<div[^>]*id="content"[^>]*class="content"[^>]*>(.*?)'
            r'</div>\s*</main>',
            content,
            re.DOTALL,
        )
        if not body_match:
            # Fallback: весь текст между <body> и </body>
            body_match = re.search(r"<body[^>]*>(.*?)</body>", content, re.DOTALL)

        body_html = body_match.group(1) if body_match else ""

        # Удаляем HTML-теги, оставляем текст
        body_text = re.sub(r"<[^>]+>", " ", body_html)
        body_text = re.sub(r"\s+", " ", body_text).strip()

        # Извлекаем breadcrumbs (навигационная цепочка)
        breadcrumbs = ""
        bc_match = re.search(
            r'<nav[^>]*aria-label="Chapter navigation"[^>]*>(.*?)</nav>',
            content,
            re.DOTALL,
        )
        if bc_match:
            bc_text = re.sub(r"<[^>]+>", " ", bc_match.group(1))
            breadcrumbs = re.sub(r"\s+", " ", bc_text).strip()

        if body_text:
            documents.append(
                {
                    "url": name,
                    "title": title,
                    "breadcrumbs": breadcrumbs,
                    "body": body_text[:5000],  # Ограничение 5000 символов
                }
            )

    return documents


def build_search_data(html_dir: Path) -> None:
    """Создать data/search-text.json в директории сборки."""
    documents = extract_text(html_dir)

    out_dir = html_dir / "data"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "search-text.json"

    out_path.write_text(
        json.dumps(documents, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"  📄 search-text.json: {len(documents)} документов, "
          f"{out_path.stat().st_size // 1024} KB")


if __name__ == "__main__":
    html_dir = Path(__file__).resolve().parent.parent / "book" / "book" / "html"
    build_search_data(html_dir)
