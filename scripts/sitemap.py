#!/usr/bin/env python3
"""
Генератор sitemap.xml для руководства Renault Symbol.
Сканирует собранный HTML-вывод mdBook и создаёт sitemap.

Использование:
    python3 scripts/sitemap.py                  # default: book/book/html → book/book/html/sitemap.xml
    python3 scripts/sitemap.py --source ./out   # произвольная директория
    python3 scripts/sitemap.py --url https://mi.github.io/reno-symbol.ru  # кастомный base URL
"""
import argparse
import os
import re
from pathlib import Path
from datetime import date


def generate_sitemap(source_dir: Path, base_url: str = None, output: Path = None):
    """Сканировать source_dir, собрать .html, записать sitemap.xml."""
    html_files = sorted(source_dir.rglob("*.html"))
    
    if not base_url:
        base_url = "https://mi.github.io/reno-symbol.ru"
    
    if base_url.endswith('/'):
        base_url = base_url.rstrip('/')
    
    if output is None:
        output = source_dir / "sitemap.xml"
    
    today = date.today().isoformat()
    
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    
    for html_file in html_files:
        rel_path = html_file.relative_to(source_dir)
        # Пропустить print.html — это PDF-версия
        if rel_path.name == "print.html":
            continue
        # Пропустить index.html — он дублирует корень
        url_path = str(rel_path).replace('\\', '/')
        if url_path.endswith('/index.html'):
            url_path = url_path[:-10] + '/'
        # Собрать приоритет по глубине вложенности
        depth = len(Path(url_path).parts)
        priority = max(0.3, 1.0 - depth * 0.15)
        
        lines.append(f'  <url>')
        lines.append(f'    <loc>{base_url}/{url_path}</loc>')
        lines.append(f'    <lastmod>{today}</lastmod>')
        lines.append(f'    <changefreq>monthly</changefreq>')
        lines.append(f'    <priority>{priority:.1f}</priority>')
        lines.append(f'  </url>')
    
    lines.append('</urlset>')
    
    sitemap_content = '\n'.join(lines)
    output.write_text(sitemap_content, encoding='utf-8')
    
    print(f"Sitemap: {len(html_files)} страниц → {output}")
    return output


def main():
    parser = argparse.ArgumentParser(description="Генератор sitemap.xml для mdBook")
    parser.add_argument('--source', type=Path, default='book/book/html',
                        help='Директория с собранным HTML (по умолч. book/book/html)')
    parser.add_argument('--url', type=str, default=None,
                        help='Base URL (по умолч. https://mi.github.io/reno-symbol.ru)')
    parser.add_argument('--output', type=Path, default=None,
                        help='Путь для sitemap.xml (по умолч. --source/sitemap.xml)')
    
    args = parser.parse_args()
    args.source = Path(args.source).resolve()
    
    if not args.source.exists():
        print(f"Ошибка: {args.source} не существует. Сначала соберите книгу: mdbook build")
        return 1
    
    generate_sitemap(args.source, args.url, args.output)
    return 0


if __name__ == '__main__':
    exit(main())
