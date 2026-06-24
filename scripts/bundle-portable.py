#!/usr/bin/env python3
"""
Упаковщик портативной версии Руководства по ремонту Renault Symbol.

Создаёт самодостаточную директорию portable/ с:
  - Всем собранным HTML-выводом (mdBook)
  - Zero-Dependency HTTP-сервером (serve.py)
  - README.txt с инструкцией

Использование:
  python3 scripts/bundle-portable.py              # сборка + упаковка
  python3 scripts/bundle-portable.py --no-build   # только упаковка (без mdbook)
  python3 scripts/bundle-portable.py --output ./dist  # кастомный путь
"""
import argparse
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DEFAULT_HTML_DIR = PROJECT_ROOT / "book" / "book" / "html"
DEFAULT_OUTPUT = PROJECT_ROOT / "portable"
BUNDLE_NAME = "reno-symbol-portable"
SERVE_SCRIPT = SCRIPT_DIR / "serve.py"


def build_book() -> bool:
    """Собрать книгу через mdbook."""
    mdbook = shutil.which("mdbook")
    if not mdbook:
        print("❌ mdbook не найден. Установите: cargo install mdbook", file=sys.stderr)
        return False

    print("📖 Сборка книги...")
    result = subprocess.run(
        [mdbook, "build", str(PROJECT_ROOT / "book")],
        cwd=PROJECT_ROOT, capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"❌ Ошибка сборки: {result.stderr}", file=sys.stderr)
        return False

    html_dir = DEFAULT_HTML_DIR
    if html_dir.exists() and (html_dir / "index.html").exists():
        print(f"✅ Собрано: {html_dir}")
        return True

    print(f"❌ HTML не найден после сборки: {html_dir}", file=sys.stderr)
    return False


def bundle_portable(html_dir: Path, output_dir: Path, no_build: bool = False, no_archive: bool = False) -> Path:
    """Упаковать портативную версию в output_dir."""
    if not no_build and not build_book():
        print("⚠️  Сборка не удалась, упаковываю существующий вывод...")

    if not html_dir.exists():
        print(f"❌ Директория HTML не найдена: {html_dir}", file=sys.stderr)
        print("Сначала соберите книгу: make build", file=sys.stderr)
        sys.exit(1)

    # Создаём чистую директорию портативной версии
    if output_dir.exists():
        print(f"🧹 Очистка {output_dir}...")
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    # Копируем HTML-вывод
    print("📁 Копирование файлов...")
    for item in html_dir.iterdir():
        dest = output_dir / item.name
        if item.is_dir():
            shutil.copytree(item, dest, symlinks=False)
        else:
            shutil.copy2(item, dest)

    # Копируем serve.py
    shutil.copy2(SERVE_SCRIPT, output_dir / "serve.py")
    (output_dir / "serve.py").chmod(0o755)

    # Копируем README
    readme_src = SCRIPT_DIR / "portable-readme.txt"
    if readme_src.exists():
        shutil.copy2(readme_src, output_dir / "README.txt")

    # Создаём скрипт запуска (без .py расширения для удобства)
    create_launcher(output_dir)

    # Подсчёт файлов
    file_count = sum(1 for _ in output_dir.rglob("*") if _.is_file())
    size_mb = sum(
        f.stat().st_size for f in output_dir.rglob("*") if f.is_file()
    ) / 1024 / 1024

    print(f"\n✅ Портативная версия создана: {output_dir}")
    print(f"   📦 {file_count} файлов, {size_mb:.1f} MB")
    print(f"   ▶  Запуск: python3 {output_dir.name}/serve.py")
    print(f"   ▶  Или:    cd {output_dir.name} && python3 serve.py")
    print()

    if not no_archive:
        _ = create_archive(output_dir)
    return output_dir


def create_launcher(out_dir: Path):
    """Создать shell-скрипт запуска для Linux/macOS."""
    launcher = out_dir / "start.sh"
    launcher.write_text(
        "#!/usr/bin/env bash\n"
        '# Портативная версия Руководства по ремонту Renault Symbol\n'
        '# Запуск: ./start.sh\n'
        'cd "$(dirname "$0")" && python3 serve.py "$@"\n'
    )
    launcher.chmod(0o755)

    # Windows batch
    bat = out_dir / "start.bat"
    bat.write_text(
        '@echo off\r\n'
        'REM Портативная версия Руководства по ремонту Renault Symbol\r\n'
        'python3 serve.py %*\r\n'
        'pause\r\n'
    )


def create_archive(out_dir: Path) -> Path:
    """Создать tar.gz архив портативной версии."""
    archive_name = f"{BUNDLE_NAME}.tar.gz"
    archive_path = out_dir.parent / archive_name

    with tarfile.open(archive_path, "w:gz") as tar:
        tar.add(out_dir, arcname=out_dir.name)

    size_mb = archive_path.stat().st_size / 1024 / 1024
    print(f"📦 Архив: {archive_path} ({size_mb:.1f} MB)")
    print(f"   Распаковка: tar xzf {archive_name}")
    return archive_path


def main():
    parser = argparse.ArgumentParser(
        description="Упаковщик портативной версии Руководства Renault Symbol",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Примеры:\n"
            "  %(prog)s                            # сборка + упаковка\n"
            "  %(prog)s --no-build                 # только упаковка\n"
            "  %(prog)s --output ./dist            # кастомный путь\n"
            "  %(prog)s --no-archive               # без tar.gz"
        ),
    )
    parser.add_argument("--no-build", action="store_true",
                        help="Не запускать mdbook сборку")
    parser.add_argument("--no-archive", action="store_true",
                        help="Не создавать tar.gz архив")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT,
                        help="Директория для портативной версии")
    parser.add_argument("--html-dir", type=Path, default=DEFAULT_HTML_DIR,
                        help="Директория с собранным HTML")
    args = parser.parse_args()

    bundle_portable(args.html_dir, args.output, args.no_build, args.no_archive)


if __name__ == "__main__":
    main()
