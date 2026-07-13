"""
Единый модуль копирования артефактов сборки.

Вызывается из:
  - scripts/serve.py          (serve-режим)
  - scripts/bundle_portable.py (упаковка портативной версии)
  - Makefile post-process      (make build)

Добавляя новый артефакт, править нужно только этот файл.
"""

import shutil
from pathlib import Path


def copy_build_artifacts(html_dir: Path, project_root: Path | None = None) -> None:
    """Скопировать дополнительные файлы в директорию сборки.

    mdBook не копирует произвольные файлы из theme/ и data/ —
    выполняем это централизованно.

    Args:
        html_dir: Директория с собранным HTML-выводом mdBook.
        project_root: Корень проекта (автоопределяется, если не указан).
    """
    if project_root is None:
        project_root = Path(__file__).resolve().parent.parent

    theme_dir = project_root / "book" / "theme"
    data_dir = project_root / "book" / "data"
    out_theme_dir = html_dir / "theme"

    # --- Service Worker ---
    sw_src = theme_dir / "sw.js"
    if sw_src.exists():
        out_theme_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(sw_src, out_theme_dir / "sw.js")

    # --- PWA Manifest ---
    manifest_src = theme_dir / "manifest.json"
    if manifest_src.exists():
        out_theme_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(manifest_src, out_theme_dir / "manifest.json")

    # --- 404 страница ---
    not_found_page = html_dir / "404.html"
    if not not_found_page.exists():
        not_found_src = project_root / "scripts" / "404.html"
        if not_found_src.exists():
            shutil.copy2(not_found_src, not_found_page)

    # --- DTC-коды (JSON-данные для виджета поиска) ---
    if data_dir.exists():
        out_data_dir = html_dir / "data"
        out_data_dir.mkdir(parents=True, exist_ok=True)
        for f in data_dir.iterdir():
            if f.is_file():
                shutil.copy2(f, out_data_dir / f.name)
