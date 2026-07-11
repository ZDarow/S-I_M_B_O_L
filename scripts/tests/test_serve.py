#!/usr/bin/env python3
"""
Тесты для TestServe, TestServeMain, TestServeHandler.
"""

import os
import shutil
import sys
import tempfile
import unittest
import json
from pathlib import Path


TESTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TESTS_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ══════════════════════════════════════════════════════════════════
# SERVE
# ══════════════════════════════════════════════════════════════════
class TestServe(unittest.TestCase):
    """Тесты Zero-Dependency HTTP-сервера"""

    def test_guess_type_html(self) -> None:
        """guess_type возвращает text/html для .html"""
        self._test_mime("index.html", "text/html; charset=utf-8")

    def test_guess_type_css(self) -> None:
        """guess_type возвращает text/css для .css"""
        self._test_mime("style.css", "text/css; charset=utf-8")

    def test_guess_type_svg(self) -> None:
        """guess_type возвращает image/svg+xml для .svg"""
        self._test_mime("diagram.svg", "image/svg+xml")

    def test_guess_type_woff2(self) -> None:
        """guess_type возвращает font/woff2 для .woff2"""
        self._test_mime("font.woff2", "font/woff2")

    def test_guess_type_pdf(self) -> None:
        """guess_type возвращает application/pdf для .pdf"""
        self._test_mime("manual.pdf", "application/pdf")

    def test_guess_type_unknown(self) -> None:
        """guess_type возвращает octet-stream для неизвестных расширений"""
        self._test_mime("data.bin", "application/octet-stream")

    def test_guess_type_no_ext(self) -> None:
        """guess_type возвращает octet-stream для файлов без расширения"""
        self._test_mime("README", "application/octet-stream")

    def _test_mime(self, path, expected) -> None:
        from scripts.serve import PortableHandler

        handler = PortableHandler.__new__(PortableHandler)
        result = handler.guess_type(path)
        self.assertEqual(result, expected)

    def test_find_available_port_returns_integer(self) -> None:
        """find_available_port возвращает int"""
        from scripts.serve import find_available_port

        port = find_available_port(18900)
        self.assertIsInstance(port, int)
        self.assertGreaterEqual(port, 18900)
        self.assertLess(port, 19000)

    def test_find_available_port_actually_free(self) -> None:
        """Возвращённый порт действительно свободен"""
        from scripts.serve import find_available_port
        import socket

        port = find_available_port(18910)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            result = s.connect_ex(("127.0.0.1", port))
            self.assertNotEqual(result, 0, f"Порт {port} должен быть свободен")

    def test_try_build_returns_true_if_exists(self) -> None:
        """try_build возвращает True, если index.html уже есть"""
        from scripts.serve import try_build

        with tempfile.TemporaryDirectory() as tmp:
            html_dir = Path(tmp) / "html"
            html_dir.mkdir(parents=True)
            (html_dir / "index.html").write_text("ok", encoding="utf-8")
            self.assertTrue(try_build(html_dir))

    def test_try_build_returns_false_if_not_exists(self) -> None:
        """try_build возвращает False, если html_dir не существует"""
        from scripts.serve import try_build

        import tempfile
        import uuid

        nonexistent = Path(tempfile.gettempdir()) / f"nonexistent_{uuid.uuid4().hex[:8]}"
        ok = try_build(nonexistent)
        self.assertFalse(ok)

    def test_load_oem_catalog_flat_list(self) -> None:
        """_load_oem_catalog загружает плоский список"""
        from unittest.mock import patch
        from scripts.serve import _load_oem_catalog, _reset_oem_catalog

        _reset_oem_catalog()
        data = [
            {"name": "Фильтр масляный", "oem": "7700274177", "category": "Двигатель"},
            {"name": "Фильтр воздушный", "oem": "172024135R", "category": "Двигатель"},
        ]
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(data, f, ensure_ascii=False)
            tmp = f.name

        try:
            with patch("scripts.serve.OEM_CATALOG_PATH", Path(tmp)):
                result = _load_oem_catalog()
            self.assertEqual(len(result), 2)
            self.assertEqual(result[0]["name"], "Фильтр масляный")
        finally:
            os.unlink(tmp)
            _reset_oem_catalog()

    def test_load_oem_catalog_categorized(self) -> None:
        """_load_oem_catalog разворачивает категоризированный формат"""
        from unittest.mock import patch
        from scripts.serve import _load_oem_catalog, _reset_oem_catalog

        _reset_oem_catalog()
        data = [
            {
                "category": "Двигатель",
                "parts": [
                    {"name": "Фильтр масляный", "oem": "7700274177"},
                    {"name": "Фильтр воздушный", "oem": "172024135R"},
                ],
            },
            {
                "category": "Тормоза",
                "parts": [
                    {"name": "Колодки передние", "oem": "440607877R"},
                ],
            },
        ]
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            json.dump(data, f, ensure_ascii=False)
            tmp = f.name

        try:
            with patch("scripts.serve.OEM_CATALOG_PATH", Path(tmp)):
                result = _load_oem_catalog()
            self.assertEqual(len(result), 3)
            self.assertEqual(result[0]["name"], "Фильтр масляный")
            self.assertEqual(result[0]["category"], "Двигатель")
            self.assertEqual(result[2]["category"], "Тормоза")
        finally:
            os.unlink(tmp)
            _reset_oem_catalog()

    def test_load_oem_catalog_missing_file(self) -> None:
        """_load_oem_catalog возвращает [] при отсутствии файла"""
        from unittest.mock import patch
        from scripts.serve import _load_oem_catalog, _reset_oem_catalog

        _reset_oem_catalog()
        missing = Path(tempfile.gettempdir()) / "nonexistent_oem_catalog.json"
        with patch("scripts.serve.OEM_CATALOG_PATH", missing):
            result = _load_oem_catalog()
        self.assertEqual(result, [])
        _reset_oem_catalog()

    def test_load_oem_catalog_invalid_json(self) -> None:
        """_load_oem_catalog возвращает [] при невалидном JSON"""
        from unittest.mock import patch
        from scripts.serve import _load_oem_catalog, _reset_oem_catalog

        _reset_oem_catalog()
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="utf-8"
        ) as f:
            f.write("это не json")
            tmp = f.name

        try:
            with patch("scripts.serve.OEM_CATALOG_PATH", Path(tmp)):
                result = _load_oem_catalog()
            self.assertEqual(result, [])
        finally:
            os.unlink(tmp)
            _reset_oem_catalog()

    def test_search_oem_empty_query(self) -> None:
        """_search_oem('') возвращает весь каталог (до лимита)"""
        from unittest.mock import patch
        from scripts.serve import _search_oem

        mock_catalog = [{"name": f"Part {i}", "oem": f"OEM{i}"} for i in range(60)]
        with patch("scripts.serve._load_oem_catalog", return_value=mock_catalog):
            result = _search_oem("")
        self.assertEqual(len(result), 50)  # max_results

    def test_search_oem_short_query(self) -> None:
        """_search_oem('a') с коротким запросом возвращает весь каталог"""
        from unittest.mock import patch
        from scripts.serve import _search_oem

        mock_catalog = [{"name": "Part", "oem": "OEM1"}]
        with patch("scripts.serve._load_oem_catalog", return_value=mock_catalog):
            result = _search_oem("a")
        self.assertEqual(len(result), 1)

    def test_search_oem_by_name(self) -> None:
        """_search_oem ищет по названию"""
        from unittest.mock import patch
        from scripts.serve import _search_oem

        mock_catalog = [
            {"name": "Фильтр масляный", "oem": "7700274177"},
            {"name": "Фильтр воздушный", "oem": "172024135R"},
            {"name": "Свеча зажигания", "oem": "7700101234"},
        ]
        with patch("scripts.serve._load_oem_catalog", return_value=mock_catalog):
            result = _search_oem("фильтр")
        self.assertEqual(len(result), 2)

    def test_search_oem_by_oem_number(self) -> None:
        """_search_oem ищет по OEM-номеру"""
        from unittest.mock import patch
        from scripts.serve import _search_oem

        mock_catalog = [
            {"name": "Фильтр", "oem": "7700274177"},
            {"name": "Свеча", "oem": "7700101234"},
        ]
        with patch("scripts.serve._load_oem_catalog", return_value=mock_catalog):
            result = _search_oem("7700")
        self.assertEqual(len(result), 2)

    def test_search_oem_by_analog(self) -> None:
        """_search_oem ищет по аналогу"""
        from unittest.mock import patch
        from scripts.serve import _search_oem

        mock_catalog = [
            {"name": "Фильтр", "oem": "OE1", "analogs": "MANN W610"},
            {"name": "Свеча", "oem": "OE2", "analogs": "NGK BKR6E"},
        ]
        with patch("scripts.serve._load_oem_catalog", return_value=mock_catalog):
            result = _search_oem("mann")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "Фильтр")

    def test_search_oem_no_results(self) -> None:
        """_search_oem возвращает [] при отсутствии совпадений"""
        from unittest.mock import patch
        from scripts.serve import _search_oem

        mock_catalog = [{"name": "Фильтр", "oem": "7700"}]
        with patch("scripts.serve._load_oem_catalog", return_value=mock_catalog):
            result = _search_oem("ZZZZZZ")
        self.assertEqual(result, [])

    def test_open_browser_starts_thread(self) -> None:
        """open_browser запускает daemon-поток (не падает)"""
        from scripts.serve import open_browser

        result = open_browser("http://localhost:8080/")
        self.assertIsNone(result)

    def test_open_browser_with_delay(self) -> None:
        """open_browser с кастомной задержкой (не падает)"""
        from scripts.serve import open_browser

        result = open_browser("http://localhost:8080/", delay=0.1)
        self.assertIsNone(result)

    def test_in_vscode_default_false(self) -> None:
        """_in_vscode возвращает False без переменных VS Code"""
        from unittest.mock import patch
        from scripts.serve import _in_vscode

        with patch.dict(os.environ, {}, clear=True):
            self.assertFalse(_in_vscode())

    def test_in_vscode_with_term_program(self) -> None:
        """_in_vscode возвращает True при TERM_PROGRAM=vscode"""
        from unittest.mock import patch
        from scripts.serve import _in_vscode

        with patch.dict(os.environ, {"TERM_PROGRAM": "vscode"}, clear=True):
            self.assertTrue(_in_vscode())

    def test_in_vscode_with_injection_var(self) -> None:
        """_in_vscode возвращает True при VSCODE_INJECTION=1"""
        from unittest.mock import patch
        from scripts.serve import _in_vscode

        with patch.dict(os.environ, {"VSCODE_INJECTION": "1"}, clear=True):
            self.assertTrue(_in_vscode())

    def test_open_browser_vscode_uri(self) -> None:
        """open_browser с vscode=True использует vscode:// URI"""
        from unittest.mock import patch
        from scripts.serve import open_browser

        with patch("scripts.serve.webbrowser.open") as mock_open:
            open_browser("http://localhost:8080/", delay=0.01, vscode=True)
            import time

            time.sleep(0.05)  # ждём daemon-поток
            self.assertTrue(mock_open.called)
            uri = mock_open.call_args[0][0]
            self.assertIn("vscode://vscode.open", uri)
            self.assertIn("http%3A//localhost%3A8080/", uri)


# ══════════════════════════════════════════════════════════════════
# BUNDLE PORTABLE
# ══════════════════════════════════════════════════════════════════


class TestServeMain(unittest.TestCase):
    """Тесты main() функции serve.py"""

    def test_main_help_succeeds(self) -> None:
        """serve.py --help возвращает 0 и содержит описание"""
        import subprocess

        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "serve.py"), "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("Renault Symbol", result.stdout)

    def test_main_nonexistent_dir_exits_nonzero(self) -> None:
        """serve.py с несуществующей директорией завершается с ошибкой"""
        import subprocess
        import uuid

        bad_dir = tempfile.gettempdir() / Path(f"nonexistent_{uuid.uuid4().hex[:8]}")
        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "serve.py"), "--dir", str(bad_dir)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("не найдена", result.stderr)  # "не найдена" or "не существует"

    def test_main_verbose_sets_env_var(self) -> None:
        """serve.py --verbose запускается без ошибок"""
        import subprocess
        import time

        with tempfile.TemporaryDirectory() as tmp:
            html_dir = Path(tmp) / "html"
            html_dir.mkdir(parents=True)
            (html_dir / "index.html").write_text("ok", encoding="utf-8")

            proc = subprocess.Popen(
                [
                    sys.executable,
                    str(PROJECT_ROOT / "serve.py"),
                    "--dir",
                    str(html_dir),
                    "--verbose",
                    "--no-browser",
                    "--port",
                    "19100",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            time.sleep(1.5)
            try:
                poll = proc.poll()
                if poll is not None:
                    stderr_out = proc.stderr.read() if proc.stderr else ""
                    self.fail(f"Сервер упал сразу (код {poll}): {stderr_out[:200]}")
            finally:
                proc.terminate()
                proc.wait(timeout=3)


# ══════════════════════════════════════════════════════════════════
# SERVE — HTTP handler integration
# ══════════════════════════════════════════════════════════════════


# ══════════════════════════════════════════════════════════════════
# SERVE — HTTP handler integration
# ══════════════════════════════════════════════════════════════════
class TestServeHandler(unittest.TestCase):
    """Интеграционные тесты HTTP-обработчика PortableHandler"""

    tmpdir: Path
    html_dir: Path
    port: int
    server = None
    base = ""

    @classmethod
    def setUpClass(cls) -> None:
        import functools
        import threading
        from http.server import HTTPServer
        from scripts.serve import PortableHandler, find_available_port

        cls.tmpdir = Path(tempfile.mkdtemp(prefix="serve_handler_test_"))
        cls.html_dir = cls.tmpdir / "html"
        cls.html_dir.mkdir(parents=True)
        # Создаём тестовые файлы
        (cls.html_dir / "index.html").write_text(
            "<html><body>INDEX</body></html>", encoding="utf-8"
        )
        (cls.html_dir / "test.svg").write_text(
            '<svg xmlns="http://www.w3.org/2000/svg"></svg>', encoding="utf-8"
        )
        (cls.html_dir / "sub").mkdir()
        (cls.html_dir / "sub" / "page.html").write_text(
            "<html><body>SUB PAGE</body></html>", encoding="utf-8"
        )

        cls.port = find_available_port(18850)
        handler = functools.partial(PortableHandler, directory=str(cls.html_dir))
        cls.server = HTTPServer(("127.0.0.1", cls.port), handler)
        cls.server.allow_reuse_address = True
        t = threading.Thread(target=cls.server.serve_forever, daemon=True)
        t.start()
        cls.base = f"http://127.0.0.1:{cls.port}"

    @classmethod
    def tearDownClass(cls) -> None:
        if cls.server:
            cls.server.shutdown()
            cls.server.server_close()
        shutil.rmtree(cls.tmpdir, ignore_errors=True)

    def _get(self, path: str) -> None:
        """Выполнить GET запрос и вернуть (code, body)."""
        import urllib.request
        import urllib.error

        try:
            with urllib.request.urlopen(f"{self.base}{path}", timeout=3) as resp:  # nosec B310: test URL
                return resp.status, resp.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode("utf-8")

    def test_get_root_returns_index(self) -> None:
        """GET / возвращает index.html"""
        code, body = self._get("/")
        self.assertEqual(code, 200)
        self.assertIn("INDEX", body)

    def test_get_subdir_html_file(self) -> None:
        """GET /sub/page.html возвращает HTML"""
        code, body = self._get("/sub/page.html")
        self.assertEqual(code, 200)
        self.assertIn("SUB PAGE", body)

    def test_get_svg_returns_svg_mime(self) -> None:
        """GET /test.svg возвращает SVG с image/svg+xml"""
        import urllib.request

        with urllib.request.urlopen(f"{self.base}/test.svg", timeout=3) as resp:  # nosec B310: test URL
            self.assertEqual(resp.status, 200)
            content_type = resp.headers.get("Content-Type", "")
            self.assertIn("image/svg+xml", content_type)

    def test_get_nonexistent_returns_404(self) -> None:
        """GET /nonexistent.html возвращает 404"""
        code, body = self._get("/nonexistent.html")
        self.assertEqual(code, 404)

    def test_get_oem_search_json(self) -> None:
        """GET /api/oem-search?q=7700274177 возвращает JSON"""
        from scripts.serve import _reset_oem_catalog

        _reset_oem_catalog()
        code, body = self._get("/api/oem-search?q=7700274177")
        self.assertEqual(code, 200)
        data = json.loads(body)
        self.assertIn("query", data)
        self.assertIn("results", data)

    def test_get_oem_catalog_json(self) -> None:
        """GET /api/oem-catalog.json возвращает полный каталог"""
        from scripts.serve import _reset_oem_catalog

        _reset_oem_catalog()
        code, body = self._get("/api/oem-catalog.json")
        self.assertEqual(code, 200)
        data = json.loads(body)
        self.assertIsInstance(data, list)


# ══════════════════════════════════════════════════════════════════
# PDF-A4
# ══════════════════════════════════════════════════════════════════


if __name__ == "__main__":
    unittest.main()
