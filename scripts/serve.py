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
import functools
import json
import logging
import os
import shutil
import socket
import subprocess
import sys
import threading
import time
import urllib.parse
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


# ─── Загрузка OEM-каталога ──────────────────────────────────────
OEM_CATALOG_PATH = SCRIPT_DIR / "oem_catalog.json"


def _reset_oem_catalog():
    """Сбросить кеш OEM-каталога (для тестов)."""
    _load_oem_catalog.cache_clear()


@functools.lru_cache(maxsize=1)
def _load_oem_catalog():
    """Загрузить и нормализовать OEM-каталог из JSON (ленивая загрузка, thread-safe).

    Поддерживает два формата:
    - Плоский список: [{name, oem, analogs, engines}, ...]
    - С категориями: [{category, parts: [{name, oem, ...}, ...]}, ...]
    """
    try:
        if OEM_CATALOG_PATH.exists():
            with open(OEM_CATALOG_PATH, encoding="utf-8") as f:
                raw = json.load(f)
            # Нормализация: если есть category/parts — разворачиваем
            if isinstance(raw, list) and raw and isinstance(raw[0], dict):
                if "parts" in raw[0]:
                    flat = []
                    for group in raw:
                        category = group.get("category", "")
                        for part in group.get("parts", []):
                            part["category"] = category
                            flat.append(part)
                    return flat
                return raw
            return raw if isinstance(raw, list) else []
        logger.warning("OEM-каталог не найден: %s", OEM_CATALOG_PATH)
        return []
    except Exception as exc:
        logger.error("Ошибка загрузки OEM-каталога: %s", exc)
        return []


def _search_oem(query: str, max_results: int = 50) -> list:
    """Поиск по OEM-каталогу (название, номер, аналог, двигатель)."""
    catalog = _load_oem_catalog()
    if not catalog:
        return []
    if not query or len(query) < 2:
        return catalog[:max_results] if isinstance(catalog, list) else []
    q = query.lower().replace(" ", "")
    results = []
    for item in catalog:
        if isinstance(item, dict):
            name = item.get("name", "")
            oem_num = item.get("oem", "").replace(" ", "").lower()
            analogs = item.get("analogs", "")
            engines = item.get("engines", "").lower()
            category = item.get("category", "").lower()
            if (
                q in name.lower()
                or q in oem_num
                or q in engines
                or q in category
                or any(
                    q in a.lower().replace(" ", "")
                    for a in (analogs if isinstance(analogs, list) else [analogs])
                )
            ):
                results.append(item)
    return results[:max_results]


CSP_HEADER = (
    "default-src 'self'; "
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
    "font-src 'self' https://fonts.gstatic.com; "
    "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
    "img-src 'self' data:; "
    "object-src 'none'; "
    "frame-ancestors 'none'; "
    "base-uri 'self'; "
    "form-action 'none'; "
)


class PortableHandler(SimpleHTTPRequestHandler):
    """Кастомный обработчик с русскоязычными index, MIME-типами и OEM API."""

    def guess_type(self, path):
        ext = os.path.splitext(path)[1].lower()
        return MIME_TYPES.get(ext, "application/octet-stream")

    def log_message(self, format, *args):
        """Тихий режим: не выводить каждый запрос."""
        if os.environ.get("SERVE_VERBOSE"):
            super().log_message(format, *args)

    def do_GET(self):
        """Обработка GET-запросов с поддержкой API."""
        parsed = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed.query)

        if parsed.path == "/api/oem-search":
            self._handle_oem_search(query_params.get("q", [""])[0])
            return
        if parsed.path == "/api/oem-catalog.json":
            self._serve_oem_catalog()
            return

        # Защита от path traversal (включая URL-encoded %2e%2e):
        #   1. URL-декодируем путь
        #   2. Джойним с базовой директорией
        #   3. Нормализуем через Path.resolve()
        #   4. Проверяем, что результат — внутри разрешённой директории
        decoded_path = urllib.parse.unquote(parsed.path)
        base_dir = Path(self.directory).resolve()
        requested = (base_dir / decoded_path.lstrip("/")).resolve()
        if base_dir not in requested.parents and requested != base_dir:
            self.send_error(404, "Not Found")
            return

        super().do_GET()

    def _send_json(self, data: dict | list, cache_seconds: int = 0):
        """Отправить JSON-ответ с едиными заголовками."""
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Security-Policy", CSP_HEADER)
        if cache_seconds:
            self.send_header("Cache-Control", f"max-age={cache_seconds}")
        else:
            self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"))

    def _handle_oem_search(self, query: str):
        """Эндпоинт /api/oem-search?q=... — поиск по OEM-каталогу."""
        results = _search_oem(query)
        self._send_json(
            {
                "query": query,
                "count": len(results),
                "results": results,
            }
        )

    def _serve_oem_catalog(self):
        """Эндпоинт /api/oem-catalog.json — полный каталог."""
        catalog = _load_oem_catalog()
        self._send_json(catalog, cache_seconds=3600)


def find_available_port(start: int = DEFAULT_PORT) -> int:
    """Найти свободный порт, начиная с start."""
    for port in range(start, start + 100):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    return start  # fallback


def _in_vscode() -> bool:
    """Проверить, запущен ли сервер внутри VS Code.

    Переменные TERM_PROGRAM=vscode или VSCODE_INJECTION=1
    устанавливаются VS Code при запуске встроенного терминала.
    """
    return os.environ.get("TERM_PROGRAM") == "vscode" or "VSCODE_INJECTION" in os.environ


def open_browser(url: str, delay: float = 0.5, vscode: bool = False):
    """Открыть браузер после задержки (чтобы сервер успел стартовать).

    Если vscode=True или сервер запущен внутри VS Code, открывает
    в интегрированном браузере через vscode:// URI.

    В обычном режиме открывает системный браузер через webbrowser.open().
    """

    def _open():
        time.sleep(delay)
        if vscode or _in_vscode():
            # VS Code Integrated Browser через vscode:// URI
            vscode_uri = f"vscode://vscode.open?url={urllib.parse.quote(url)}"
            webbrowser.open(vscode_uri)
        else:
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
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"❌ Ошибка сборки:\n{result.stderr}", file=sys.stderr)
        return False
    print("✅ Сборка завершена")

    # Пост-обработка: копируем дополнительные файлы
    _copy_build_artifacts(html_dir)

    return html_dir.exists() and (html_dir / "index.html").exists()


def _copy_build_artifacts(html_dir: Path) -> None:
    """Скопировать дополнительные файлы в директорию сборки (делегирует _copy_artifacts)."""
    import importlib.util
    _spec = importlib.util.spec_from_file_location("_copy_artifacts", SCRIPT_DIR / "_copy_artifacts.py")
    _mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    _mod.copy_build_artifacts(html_dir, PROJECT_ROOT)


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
    parser.add_argument(
        "--port", type=int, default=DEFAULT_PORT, help=f"Порт сервера (по умолч. {DEFAULT_PORT})"
    )
    parser.add_argument(
        "--log-level",
        default="WARNING",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Уровень логирования",
    )
    parser.add_argument(
        "--dir",
        type=Path,
        default=DEFAULT_HTML_DIR,
        help="Директория с HTML (по умолч. book/book/html)",
    )
    parser.add_argument(
        "--no-browser", action="store_true", help="Не открывать браузер автоматически"
    )
    parser.add_argument(
        "--vscode",
        action="store_true",
        help="Открыть во встроенном браузере VS Code (автоопределяется, если не указан)",
    )
    parser.add_argument("--verbose", action="store_true", help="Подробные логи запросов")
    args = parser.parse_args()

    logging.basicConfig(level=getattr(logging, args.log_level), format="%(levelname)s: %(message)s")
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

    # Передаём директорию через functools.partial вместо os.chdir
    handler = functools.partial(PortableHandler, directory=str(html_dir))
    server = HTTPServer((host, port), handler)

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
        open_browser(url, vscode=args.vscode)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Сервер остановлен")
        server.server_close()


if __name__ == "__main__":
    main()
