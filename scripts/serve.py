#!/usr/bin/env python3
"""
Zero-Dependency HTTP-сервер для портативной версии
Руководства по ремонту Renault Symbol.

Не требует установки зависимостей — только Python 3 в системе.
Работает на любом HTTP-клиенте (браузер, curl).

Использование:
  python3 scripts/serve.py                    # книга собрана в book/book/html
  python3 scripts/serve.py --dir ./out        # кастомная директория
  python3 scripts/serve.py --port 8080        # кастомный порт
  python3 scripts/serve.py --no-browser       # без открытия браузера
"""
import argparse
import logging
import os
import shutil
import subprocess
import sys
import threading
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

logger = logging.getLogger(__name__)


# ─── Пути ─────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DEFAULT_HTML_DIR = PROJECT_ROOT / "book" / "book" / "html"
DEFAULT_PORT = 8080

# MIME-типы для корректной отдачи файлов
MIME_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".json": "application/json",
    ".xml": "application/xml",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".ico": "image/x-icon",
    ".webp": "image/webp",
    ".woff": "font/woff",
    ".woff2": "font/woff2",
    ".ttf": "font/ttf",
    ".otf": "font/otf",
    ".eot": "application/vnd.ms-fontobject",
    ".pdf": "application/pdf",
    ".txt": "text/plain; charset=utf-8",
    ".md": "text/markdown; charset=utf-8",
    ".yaml": "text/yaml; charset=utf-8",
    ".yml": "text/yaml; charset=utf-8",
}


class PortableHandler(SimpleHTTPRequestHandler):
    """Кастомный обработчик с русскоязычными index и MIME-типами."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def guess_type(self, path):
        ext = os.path.splitext(path)[1].lower()
        return MIME_TYPES.get(ext, "application/octet-stream")

    def log_message(self, format, *args):
        """Тихий режим: не выводить каждый запрос."""
        if os.environ.get("SERVE_VERBOSE"):
            super().log_message(format, *args)


def find_available_port(start: int = DEFAULT_PORT) -> int:
    """Найти свободный порт, начиная с start."""
    import socket
    for port in range(start, start + 100):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    return start  # fallback


def open_browser(url: str, delay: float = 0.5):
    """Открыть браузер после задержки (чтобы сервер успел стартовать)."""
    def _open():
        import time
        time.sleep(delay)
        webbrowser.open(url)
    threading.Thread(target=_open, daemon=True).start()


def try_build(html_dir: Path) -> bool:
    """Попытаться собрать книгу, если она ещё не собрана."""
    if html_dir.exists() and (html_dir / "index.html").exists():
        return True  # уже собрана

    # Проверяем наличие mdbook
    mdbook = shutil.which("mdbook")
    if not mdbook:
        return False

    print("📖 Книга не собрана. Запускаю сборку...")
    result = subprocess.run(
        [mdbook, "build", str(PROJECT_ROOT / "book")],
        cwd=PROJECT_ROOT, capture_output=True, text=True,
    )
    if result.returncode != 0:
        print(f"❌ Ошибка сборки:\n{result.stderr}", file=sys.stderr)
        return False
    print("✅ Сборка завершена")
    return html_dir.exists() and (html_dir / "index.html").exists()


def main():
    parser = argparse.ArgumentParser(
        description="Zero-Dependency HTTP-сервер для Руководства Renault Symbol",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Примеры:\n"
            "  python3 %(prog)s                        # порт 8080\n"
            "  python3 %(prog)s --port 3000            # кастомный порт\n"
            "  python3 %(prog)s --dir ./out            # из директории\n"
            "  python3 %(prog)s --no-browser           # без открытия браузера\n"
            "  python3 %(prog)s --verbose              # подробные логи"
        ),
    )
    parser.add_argument("--port", type=int, default=DEFAULT_PORT,
                        help=f"Порт сервера (по умолч. {DEFAULT_PORT})")
    parser.add_argument("--log-level", default="WARNING",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                        help="Уровень логирования")
    parser.add_argument("--dir", type=Path, default=DEFAULT_HTML_DIR,
                        help="Директория с HTML (по умолч. book/book/html)")
    parser.add_argument("--no-browser", action="store_true",
                        help="Не открывать браузер автоматически")
    parser.add_argument("--verbose", action="store_true",
                        help="Подробные логи запросов")
    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.log_level),
                        format="%(levelname)s: %(message)s")
    if args.verbose:
        os.environ["SERVE_VERBOSE"] = "1"

    logger.info("Сервер запускается...")
    html_dir = args.dir.resolve()

    # Попытка сборки, если директория пуста
    if not try_build(html_dir):
        print(f"❌ Директория не найдена: {html_dir}", file=sys.stderr)
        print("Сначала соберите книгу: make build", file=sys.stderr)
        sys.exit(1)

    port = find_available_port(args.port)
    host = "127.0.0.1"

    server = HTTPServer((host, port), PortableHandler)

    # Меняем рабочую директорию на HTML-вывод
    os.chdir(html_dir)

    url = f"http://{host}:{port}/"

    print()
    print("╔══════════════════════════════════════════════╗")
    print("║  Руководство по ремонту Renault Symbol      ║")
    print("║  📖 Портативная версия                      ║")
    print("╠══════════════════════════════════════════════╣")
    print(f"║  ▶  {url:<36}║")
    print(f"║  📁  {str(html_dir):<36}║")
    print("║                                              ║")
    print("║  Для остановки: Ctrl+C                      ║")
    print("╚══════════════════════════════════════════════╝")
    print()

    if not args.no_browser:
        open_browser(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Сервер остановлен")
        server.server_close()


if __name__ == "__main__":
    main()
