"""
Dev-сервер с корректными MIME-типами для Service Worker и JSON.
Запуск: python3 scripts/serve.py [порт]
"""

import http.server
import socketserver
import sys
from pathlib import Path


class CorrectMIMEHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler с правильными MIME-типами."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(HTML_DIR), **kwargs)

    extensions_map = {
        **http.server.SimpleHTTPRequestHandler.extensions_map,
        ".js": "application/javascript",
        ".json": "application/json",
        ".svg": "image/svg+xml",
        ".wasm": "application/wasm",
        ".webmanifest": "application/manifest+json",
    }


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    HTML_DIR = Path(__file__).resolve().parent.parent / "book" / "book" / "html"

    if not HTML_DIR.exists():
        print(f"❌ Директория сборки не найдена: {HTML_DIR}")
        print("   Выполни сначала: mdbook build book")
        sys.exit(1)

    with socketserver.TCPServer(("", port), CorrectMIMEHandler) as httpd:
        print(f"🚀 Dev-сервер: http://localhost:{port}")
        print(f"📁 Директория: {HTML_DIR}")
        print("   Выход: Ctrl+C")
        httpd.serve_forever()
