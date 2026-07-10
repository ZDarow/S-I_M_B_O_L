#!/usr/bin/env python3
"""
Тесты для Python-скриптов Руководства по ремонту Renault Symbol.

Запуск:
    python3 -m pytest scripts/test_portable.py -v
    python3 -m unittest scripts/test_portable.py -v
"""
import os
import shutil
import sys
import tarfile
import tempfile
import unittest
import json
from pathlib import Path


# ── Настройка путей ─────────────────────────────────────────────
TESTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TESTS_DIR.parent
sys.path.insert(0, str(TESTS_DIR))


# ══════════════════════════════════════════════════════════════════
# SITEMAP
# ══════════════════════════════════════════════════════════════════
class TestSitemap(unittest.TestCase):
    """Тесты генератора sitemap.xml"""

    maxDiff = None

    def setUp(self) -> None:
        self.tmpdir = Path(tempfile.mkdtemp(prefix="sitemap_test_"))
        self.html_dir = self.tmpdir / "html"
        self.html_dir.mkdir(parents=True)

        # Создаём тестовые HTML-файлы
        (self.html_dir / "index.html").write_text("<h1>Home</h1>", encoding="utf-8")
        (self.html_dir / "dvigatel").mkdir()
        (self.html_dir / "dvigatel" / "3-1.html").write_text(
            "<h1>Engine</h1>", encoding="utf-8"
        )
        (self.html_dir / "dvigatel" / "3-2.html").write_text(
            "<h1>Fuel</h1>", encoding="utf-8"
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_generate_sitemap_creates_file(self) -> None:
        """sitemap.xml создаётся в source_dir"""
        from scripts.sitemap import generate_sitemap

        result = generate_sitemap(self.html_dir)
        self.assertTrue(result.exists())
        self.assertEqual(result, self.html_dir / "sitemap.xml")

    def test_generate_sitemap_contains_proper_xml(self) -> None:
        """sitemap содержит корректный XML"""
        from scripts.sitemap import generate_sitemap

        output = generate_sitemap(self.html_dir)
        content = output.read_text(encoding="utf-8")

        self.assertIn('<?xml version="1.0"', content)
        self.assertIn('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">', content)
        self.assertIn('</urlset>', content)

    def test_generate_sitemap_expected_urls(self) -> None:
        """Проверка количества и содержания URL"""
        from scripts.sitemap import generate_sitemap

        output = generate_sitemap(self.html_dir)
        content = output.read_text(encoding="utf-8")

        self.assertIn("dvigatel/3-1.html", content)
        self.assertIn("dvigatel/3-2.html", content)
        self.assertIn("index.html", content)

    def test_generate_sitemap_priority_by_depth(self) -> None:
        """Приоритет уменьшается с глубиной вложенности"""
        from scripts.sitemap import generate_sitemap

        output = generate_sitemap(self.html_dir)
        content = output.read_text(encoding="utf-8")

        # index.html → depth 1 → priority 0.85 → fmt '0.8'
        # dvigatel/3-1.html → depth 2 → priority 0.7 → fmt '0.7'
        self.assertIn("<priority>0.8</priority>", content)
        self.assertIn("<priority>0.7</priority>", content)

    def test_generate_sitemap_custom_base_url(self) -> None:
        """Кастомный base_url подставляется в <loc>"""
        from scripts.sitemap import generate_sitemap

        output = generate_sitemap(self.html_dir, base_url="https://example.com/book")
        content = output.read_text(encoding="utf-8")
        self.assertIn("https://example.com/book", content)
        self.assertNotIn("mi.github.io", content)

    def test_generate_sitemap_empty_dir(self) -> None:
        """Пустая директория → sitemap с пустым urlset"""
        from scripts.sitemap import generate_sitemap

        empty_dir = self.tmpdir / "empty"
        empty_dir.mkdir()
        output = generate_sitemap(empty_dir)
        content = output.read_text(encoding="utf-8")
        # Только открывающий и закрывающий теги urlset
        self.assertIn("</urlset>", content)


# ══════════════════════════════════════════════════════════════════
# MERMAID CORE
# ══════════════════════════════════════════════════════════════════
class TestMermaidCore(unittest.TestCase):
    """Тесты общего модуля mermaid"""

    def test_hash_mermaid_consistent(self) -> None:
        """Хеш одинаков для одинакового кода диаграммы"""
        from scripts.mermaid_core import hash_mermaid

        source = "graph TD; A-->B;"
        self.assertEqual(hash_mermaid(source), hash_mermaid(source))

    def test_hash_mermaid_different(self) -> None:
        """Хеш разный для разного кода диаграммы"""
        from scripts.mermaid_core import hash_mermaid

        a = hash_mermaid("graph TD; A-->B;")
        b = hash_mermaid("graph TD; A-->C;")
        self.assertNotEqual(a, b)

    def test_hash_mermaid_length(self) -> None:
        """Хеш — 16 символов"""
        from scripts.mermaid_core import hash_mermaid

        h = hash_mermaid("graph TD; A-->B;")
        self.assertEqual(len(h), 16)

    def test_hash_mermaid_empty(self) -> None:
        """Пустая строка тоже хешируется"""
        from scripts.mermaid_core import hash_mermaid

        h = hash_mermaid("")
        self.assertEqual(len(h), 16)

    def test_mergemare_re_matches(self) -> None:
        """MERMAID_RE находит ```mermaid блоки"""
        from scripts.mermaid_core import MERMAID_RE

        text = "text\n```mermaid\ngraph TD;\nA-->B;\n```\nmore"
        matches = MERMAID_RE.findall(text)
        self.assertEqual(len(matches), 1)
        self.assertIn("graph TD;", matches[0])
        self.assertIn("A-->B;", matches[0])

    def test_mergemare_re_no_false_positives(self) -> None:
        """MERMAID_RE не матчит обычные блоки кода"""
        from scripts.mermaid_core import MERMAID_RE

        text = "```python\nprint('hello')\n```"
        self.assertEqual(MERMAID_RE.findall(text), [])

    def test_mergemare_re_multi_matches(self) -> None:
        """MERMAID_RE находит несколько блоков"""
        from scripts.mermaid_core import MERMAID_RE

        text = (
            "```mermaid\ngraph TD; A;\n```\n"
            "text\n"
            "```mermaid\ngraph TD; B;\n```\n"
        )
        self.assertEqual(len(MERMAID_RE.findall(text)), 2)

    def test_find_mmdc_returns_none_on_empty_path(self) -> None:
        """find_mmdc() → None, когда mmdc нет"""
        from scripts.mermaid_core import find_mmdc

        # Сохраняем и подменяем PATH
        orig_path = os.environ.get("PATH", "")
        try:
            os.environ["PATH"] = "/dev/null"
            result = find_mmdc()
            self.assertIsNone(result)
        finally:
            os.environ["PATH"] = orig_path

    def test_render_svg_returns_false_no_mmdc(self) -> None:
        """render_svg возвращает False, если mmdc не найден"""
        from scripts.mermaid_core import render_svg
        from unittest.mock import patch

        tmp_dir = tempfile.gettempdir()
        with patch("scripts.mermaid_core.find_mmdc", return_value=None):
            result = render_svg("graph TD;\nA-->B;", Path(tmp_dir) / "test.svg")
        self.assertFalse(result)

    def test_render_svg_cleans_up_temp_on_failure(self) -> None:
        """render_svg удаляет temp-файл при ошибке mmdc (через mock find_mmdc)"""
        import subprocess
        from scripts.mermaid_core import render_svg
        from unittest.mock import patch

        # Мокаем subprocess.run, чтобы он вернул возврат 1
        tmp_dir = tempfile.gettempdir()
        fake_result = subprocess.CompletedProcess(args=["mmdc"], returncode=1, stdout="", stderr="error")
        with patch("scripts.mermaid_core.find_mmdc", return_value="/usr/bin/fake-mmdc"), \
             patch("subprocess.run", return_value=fake_result):
            result = render_svg("graph TD;\nX;", Path(tmp_dir) / "out.svg")
        self.assertFalse(result)

    def test_render_svg_returns_false_on_timeout(self) -> None:
        """render_svg возвращает False при таймауте mmdc"""
        import subprocess
        from scripts.mermaid_core import render_svg, MMDC_TIMEOUT
        from unittest.mock import patch

        tmp_dir = tempfile.gettempdir()
        with patch("scripts.mermaid_core.find_mmdc", return_value="/usr/bin/fake-mmdc"), \
             patch("subprocess.run", side_effect=subprocess.TimeoutExpired(
                 cmd="mmdc", timeout=MMDC_TIMEOUT)):
            result = render_svg("graph TD;\nZ;", Path(tmp_dir) / "out.svg")
        self.assertFalse(result)


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
        import json
        from unittest.mock import patch
        from scripts.serve import _load_oem_catalog, _reset_oem_catalog

        _reset_oem_catalog()
        data = [
            {"name": "Фильтр масляный", "oem": "7700274177", "category": "Двигатель"},
            {"name": "Фильтр воздушный", "oem": "172024135R", "category": "Двигатель"},
        ]
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False,
                                         encoding="utf-8") as f:
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
        import json
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
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False,
                                         encoding="utf-8") as f:
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
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False,
                                         encoding="utf-8") as f:
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
class TestBundlePortable(unittest.TestCase):
    """Тесты упаковщика портативной версии"""

    def setUp(self) -> None:
        self.tmpdir = Path(tempfile.mkdtemp(prefix="bundle_test_"))
        self.html_dir = self.tmpdir / "html"
        self.html_dir.mkdir(parents=True)
        (self.html_dir / "index.html").write_text("<h1>Book</h1>", encoding="utf-8")
        (self.html_dir / "style.css").write_text("body {}", encoding="utf-8")
        (self.html_dir / "img").mkdir()
        (self.html_dir / "img" / "photo.jpg").write_bytes(b"fake jpg data")

        self.output_dir = self.tmpdir / "portable"
        # Создаём фейковый serve.py для тестов
        self.fake_serve = self.tmpdir / "serve.py"
        self.fake_serve.write_text("#!/usr/bin/env python3\nprint('ok')\n", encoding="utf-8")

    def tearDown(self) -> None:
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_create_launcher_creates_scripts(self) -> None:
        """create_launcher создаёт start.sh и start.bat"""
        from scripts.bundle_portable import create_launcher

        out = self.tmpdir / "launcher_test"
        out.mkdir()
        create_launcher(out)

        self.assertTrue((out / "start.sh").exists())
        self.assertTrue((out / "start.bat").exists())

    def test_create_launcher_start_sh_executable(self) -> None:
        """start.sh должен быть исполняемым"""
        from scripts.bundle_portable import create_launcher

        out = self.tmpdir / "launcher_perm"
        out.mkdir()
        create_launcher(out)

        self.assertTrue(os.access(out / "start.sh", os.X_OK))

    def test_create_launcher_start_sh_content(self) -> None:
        """start.sh содержит корректный shebang и команду"""
        from scripts.bundle_portable import create_launcher

        out = self.tmpdir / "launcher_content"
        out.mkdir()
        create_launcher(out)

        content = (out / "start.sh").read_text(encoding="utf-8")
        self.assertIn("#!/usr/bin/env bash", content)
        self.assertIn("python3 serve.py", content)

    def test_create_launcher_bat_content(self) -> None:
        """start.bat содержит корректные команды Windows"""
        from scripts.bundle_portable import create_launcher

        out = self.tmpdir / "launcher_bat"
        out.mkdir()
        create_launcher(out)

        content = (out / "start.bat").read_text(encoding="utf-8")
        self.assertIn("@echo off", content)
        self.assertIn("python3 serve.py", content)
        self.assertIn("pause", content)

    def test_create_archive_creates_tar_gz(self) -> None:
        """create_archive создаёт tar.gz с содержимым директории"""
        from scripts.bundle_portable import create_archive, BUNDLE_NAME

        out = self.tmpdir / "archive_src"
        out.mkdir()
        (out / "test.txt").write_text("hello", encoding="utf-8")

        archive = create_archive(out)
        expected_name = self.tmpdir / f"{BUNDLE_NAME}.tar.gz"
        self.assertEqual(archive, expected_name)
        self.assertTrue(archive.exists())

        # Проверяем содержимое
        with tarfile.open(archive, "r:gz") as tar:
            names = tar.getnames()
            self.assertTrue(any("test.txt" in n for n in names))

    def test_bundle_portable_creates_output_dir(self) -> None:
        """bundle_portable создаёт директорию с содержимым html + serve.py + README"""
        from scripts.bundle_portable import bundle_portable

        # Подменяем SERVE_SCRIPT и portable-readme.txt
        import scripts.bundle_portable as bp
        orig_serve = bp.SERVE_SCRIPT

        try:
            bp.SERVE_SCRIPT = self.fake_serve
            result = bundle_portable(
                self.html_dir, self.output_dir,
                no_build=True, no_archive=True,
            )
            self.assertTrue(result.exists())
            self.assertTrue((result / "index.html").exists())
            self.assertTrue((result / "style.css").exists())
            self.assertTrue((result / "img" / "photo.jpg").exists())
            self.assertTrue((result / "serve.py").exists())
        finally:
            bp.SERVE_SCRIPT = orig_serve

    def test_bundle_portable_skips_archive(self) -> None:
        """bundle_portable с no_archive=True не создаёт архив"""
        from scripts.bundle_portable import bundle_portable, BUNDLE_NAME

        import scripts.bundle_portable as bp
        orig_serve = bp.SERVE_SCRIPT

        try:
            bp.SERVE_SCRIPT = self.fake_serve
            bundle_portable(
                self.html_dir, self.output_dir,
                no_build=True, no_archive=True,
            )
            archive = self.tmpdir / f"{BUNDLE_NAME}.tar.gz"
            self.assertFalse(archive.exists())
        finally:
            bp.SERVE_SCRIPT = orig_serve


# ══════════════════════════════════════════════════════════════════
# GENERATE ILLUSTRATIONS
# ══════════════════════════════════════════════════════════════════
class TestGenerateIllustrations(unittest.TestCase):
    """Тесты генератора SVG-иллюстраций"""

    def setUp(self) -> None:
        self.tmpdir = Path(tempfile.mkdtemp(prefix="illustrations_test_"))
        self.output_dir = self.tmpdir / "img"
        self.output_dir.mkdir(parents=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_svg_header_contains_dimensions(self) -> None:
        """svg_header содержит указанные width и height"""
        from scripts.generate_illustrations import svg_header

        result = svg_header("Test", 800, 600)
        self.assertIn('viewBox="0 0 800 600"', result)
        self.assertIn('width="800"', result)
        self.assertIn('height="600"', result)
        self.assertIn("Test", result)

    def test_svg_footer_closes_svg(self) -> None:
        """svg_footer возвращает закрывающий тег"""
        from scripts.generate_illustrations import svg_footer

        self.assertEqual(svg_footer(), "</svg>\n")

    def test_rounded_rect_produces_rect(self) -> None:
        """rounded_rect возвращает SVG rect с параметрами"""
        from scripts.generate_illustrations import rounded_rect

        result = rounded_rect(10, 20, 100, 50, r=8, fill="#fff", stroke="#000")
        self.assertIn("x=\"10\"", result)
        self.assertIn("y=\"20\"", result)
        self.assertIn('width="100"', result)
        self.assertIn('height="50"', result)
        self.assertIn('rx="8"', result)
        self.assertIn('#fff', result)
        self.assertIn('#000', result)

    def test_label_contains_text(self) -> None:
        """label возвращает SVG text с указанным текстом"""
        from scripts.generate_illustrations import label

        result = label("Hello", 50, 60, size=14, color="#333", anchor="middle", bold=True)
        self.assertIn("Hello", result)
        self.assertIn('x="50"', result)
        self.assertIn('y="60"', result)
        self.assertIn('font-size="14"', result)
        self.assertIn('#333', result)
        self.assertIn('font-weight="bold"', result)

    def test_arrow_produces_line(self) -> None:
        """arrow возвращает SVG line с маркером"""
        from scripts.generate_illustrations import arrow

        result = arrow(0, 0, 100, 100, color="#666", width=3)
        self.assertIn('x1="0"', result)
        self.assertIn('y1="0"', result)
        self.assertIn('x2="100"', result)
        self.assertIn('y2="100"', result)
        self.assertIn('marker-end="url(#arrow)"', result)

    def test_arrow_def_contains_marker(self) -> None:
        """arrow_def содержит defs с маркером"""
        from scripts.generate_illustrations import arrow_def

        result = arrow_def()
        self.assertIn("<defs>", result)
        self.assertIn("<marker", result)
        self.assertIn("arrow", result)

    def test_line_produces_svg_line(self) -> None:
        """line возвращает SVG line без маркера"""
        from scripts.generate_illustrations import line

        result = line(10, 20, 30, 40, color="#999", width=1)
        self.assertIn('x1="10"', result)
        self.assertIn('y1="20"', result)
        self.assertIn('x2="30"', result)
        self.assertIn('y2="40"', result)
        self.assertNotIn("marker-end", result)

    def test_main_creates_svg_files(self) -> None:
        """main() создаёт 9 SVG файлов"""
        import scripts.generate_illustrations as gi

        orig_dir = gi.OUTPUT_DIR
        try:
            gi.OUTPUT_DIR = str(self.output_dir)
            gi.main()
            svg_files = list(self.output_dir.glob("*.svg"))
            self.assertEqual(len(svg_files), 9)
            expected = [
                "oil-circuit.svg", "coolant-circuit.svg", "disc-brake.svg",
                "suspension-mcpherson.svg", "battery.svg", "timing-belt.svg",
                "noise-isolation-zones.svg", "tools.svg", "alternator.svg",
            ]
            for name in expected:
                self.assertTrue(
                    (self.output_dir / name).exists(),
                    f"Missing: {name}"
                )
        finally:
            gi.OUTPUT_DIR = orig_dir

    def test_svg_files_are_valid_xml(self) -> None:
        """main() создаёт валидные SVG-файлы"""
        import xml.etree.ElementTree as ET
        import scripts.generate_illustrations as gi

        orig_dir = gi.OUTPUT_DIR
        try:
            gi.OUTPUT_DIR = str(self.output_dir)
            gi.main()
            for svg_file in self.output_dir.glob("*.svg"):
                content = svg_file.read_text(encoding="utf-8")
                try:
                    ET.fromstring(content)  # nosec B314: test data, not user input
                except ET.ParseError:
                    self.fail(f"Invalid XML in {svg_file.name}")
        finally:
            gi.OUTPUT_DIR = orig_dir


# ══════════════════════════════════════════════════════════════════
# MERMAID PREPROCESS
# ══════════════════════════════════════════════════════════════════
class TestMermaidPreprocess(unittest.TestCase):
    """Тесты препроцессора Mermaid"""

    @staticmethod
    def _import_preprocess() -> object:
        """Импортирует mermaid-preprocess.py (имя с дефисами)"""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "mermaid_preprocess",
            TESTS_DIR / "mermaid-preprocess.py",
            submodule_search_locations=[],
        )
        mod = importlib.util.module_from_spec(spec)
        sys.modules["mermaid_preprocess"] = mod
        spec.loader.exec_module(mod)
        return mod

    def setUp(self) -> None:
        self.tmpdir = Path(tempfile.mkdtemp(prefix="mermaid_preprocess_test_"))
        self.src_dir = self.tmpdir / "book" / "src"
        self.src_dir.mkdir(parents=True)
        self.cache_dir = self.src_dir / "img" / "mermaid"
        self.cache_dir.mkdir(parents=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_process_file_replaces_mermaid_block(self) -> None:
        """process_file заменяет ```mermaid блок на SVG-ссылку"""
        mod = self._import_preprocess()

        md = self.src_dir / "test.md"
        md.write_text("text\n```mermaid\ngraph TD;\nA-->B;\n```\nend", encoding="utf-8")

        from scripts.mermaid_core import hash_mermaid
        h = hash_mermaid("graph TD;\nA-->B;")
        (self.cache_dir / f"{h}.svg").write_text("<svg></svg>", encoding="utf-8")

        changes = mod.process_file(md, self.cache_dir)
        self.assertEqual(changes, 1)
        content = md.read_text(encoding="utf-8")
        self.assertIn("![Диаграмма]", content)
        self.assertNotIn("```mermaid", content)

    def test_process_file_creates_backup(self) -> None:
        """process_file создаёт бэкап .md файла"""
        mod = self._import_preprocess()

        md = self.src_dir / "backup_test.md"
        original = "text\n```mermaid\ngraph TD;\nA-->B;\n```\nend"
        md.write_text(original, encoding="utf-8")

        from scripts.mermaid_core import hash_mermaid
        h = hash_mermaid("graph TD;\nA-->B;")
        (self.cache_dir / f"{h}.svg").write_text("<svg></svg>", encoding="utf-8")

        mod.process_file(md, self.cache_dir)

        backup = md.with_suffix(md.suffix + mod.BACKUP_PREFIX)
        self.assertTrue(backup.exists())
        self.assertEqual(backup.read_text(encoding="utf-8"), original)

    def test_restore_file_restores_from_backup(self) -> None:
        """restore_file восстанавливает .md из бэкапа"""
        mod = self._import_preprocess()

        md = self.src_dir / "restore_test.md"
        original = "original content"
        backup = md.with_suffix(md.suffix + mod.BACKUP_PREFIX)
        backup.write_text(original, encoding="utf-8")
        md.write_text("modified content", encoding="utf-8")

        result = mod.restore_file(md)
        self.assertTrue(result)
        self.assertEqual(md.read_text(encoding="utf-8"), original)

    def test_restore_file_returns_false_when_no_backup(self) -> None:
        """restore_file возвращает False если бэкапа нет"""
        mod = self._import_preprocess()

        md = self.src_dir / "no_backup.md"
        md.write_text("content", encoding="utf-8")
        self.assertFalse(mod.restore_file(md))

    def test_process_file_empty_mermaid_block(self) -> None:
        """process_file не меняет файл если mermaid блок пустой"""
        mod = self._import_preprocess()

        md = self.src_dir / "empty.md"
        original = "text\n```mermaid\n\n```\nend"
        md.write_text(original, encoding="utf-8")

        changes = mod.process_file(md, self.cache_dir)
        self.assertEqual(changes, 0)
        content = md.read_text(encoding="utf-8")
        self.assertEqual(content, original)  # без изменений

    def test_process_file_no_changes_when_no_mermaid(self) -> None:
        """process_file возвращает 0 если mermaid блоков нет"""
        mod = self._import_preprocess()

        md = self.src_dir / "plain.md"
        original = "просто текст без диаграмм\n"
        md.write_text(original, encoding="utf-8")

        changes = mod.process_file(md, self.cache_dir)
        self.assertEqual(changes, 0)
        self.assertEqual(md.read_text(encoding="utf-8"), original)

    def test_process_file_backup_not_created_on_no_changes(self) -> None:
        """process_file не создаёт бэкап если изменений нет"""
        mod = self._import_preprocess()

        md = self.src_dir / "nochange.md"
        md.write_text("just text", encoding="utf-8")
        mod.process_file(md, self.cache_dir)

        backup = md.with_suffix(md.suffix + mod.BACKUP_PREFIX)
        self.assertFalse(backup.exists())

    def test_process_file_multiple_blocks(self) -> None:
        """process_file заменяет несколько mermaid блоков"""
        mod = self._import_preprocess()
        from scripts.mermaid_core import hash_mermaid

        md = self.src_dir / "multi.md"
        source1 = "graph TD;\nA-->B;"
        source2 = "graph LR;\nX-->Y;"
        md.write_text(
            f"text\n```mermaid\n{source1}\n```\nmore\n```mermaid\n{source2}\n```\nend",
            encoding="utf-8",
        )

        h1 = hash_mermaid(source1)
        h2 = hash_mermaid(source2)
        (self.cache_dir / f"{h1}.svg").write_text("<svg></svg>", encoding="utf-8")
        (self.cache_dir / f"{h2}.svg").write_text("<svg></svg>", encoding="utf-8")

        changes = mod.process_file(md, self.cache_dir)
        self.assertEqual(changes, 2)
        content = md.read_text(encoding="utf-8")
        self.assertIn("![Диаграмма]", content)
        self.assertEqual(content.count("![Диаграмма]"), 2)

    def test_main_restore_via_subprocess(self) -> None:
        """main() с --restore восстанавливает файлы и не падает"""
        import subprocess

        # Создаём .md и его .mermaid-backup
        md = self.src_dir / "restore_main.md"
        original = "content\n```mermaid\ngraph TD;\nA;\n```\nend"
        md.write_text(original, encoding="utf-8")
        backup = md.with_suffix(md.suffix + ".mermaid-backup.")
        backup.write_text("restored content", encoding="utf-8")

        result = subprocess.run(
            [sys.executable, str(TESTS_DIR / "mermaid-preprocess.py"), "--restore"],
            cwd=self.tmpdir, capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(md.read_text(encoding="utf-8"), "restored content")

    def test_main_restore_no_backup(self) -> None:
        """main() с --restore не падает если бэкапов нет"""
        import subprocess

        result = subprocess.run(
            [sys.executable, str(TESTS_DIR / "mermaid-preprocess.py"), "--restore"],
            cwd=self.tmpdir, capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(result.returncode, 0)

    def test_process_file_render_failure_logs_warning(self) -> None:
        """process_file логирует предупреждение при ошибке рендера (не падает)"""
        from unittest.mock import patch
        mod = self._import_preprocess()

        md = self.src_dir / "render_fail.md"
        md.write_text("```mermaid\ngraph TD;\nA-->B;\n```\n", encoding="utf-8")

        with patch.object(mod, "render_svg", return_value=False):
            changes = mod.process_file(md, self.cache_dir)
        self.assertEqual(changes, 0)  # блок не заменён
        # Файл не должен измениться
        self.assertIn("```mermaid", md.read_text(encoding="utf-8"))

    def test_process_file_already_replaced(self) -> None:
        """process_file не заменяет уже заменённые блоки (нет ```mermaid)"""
        mod = self._import_preprocess()

        md = self.src_dir / "already.md"
        md.write_text("text\n![Диаграмма](img/mermaid/abc.svg)\nend", encoding="utf-8")

        changes = mod.process_file(md, self.cache_dir)
        self.assertEqual(changes, 0)

    def test_main_render_only_creates_cache_dir(self) -> None:
        """main() с --render-only создаёт директорию кеша (если mmdc нет — ошибка)"""
        import subprocess

        result = subprocess.run(
            [sys.executable, str(TESTS_DIR / "mermaid-preprocess.py"), "--render-only"],
            cwd=self.tmpdir, capture_output=True, text=True, timeout=10,
        )
        # mmdc скорее всего нет — ждём ненулевой код
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("mmdc", result.stderr)

    def test_main_no_mmdc_exits_with_error(self) -> None:
        """main() выходит с ошибкой если mmdc не найден"""
        import subprocess
        import shutil

        # Убеждаемся, что mmdc нет в PATH
        if shutil.which("mmdc") is not None:
            self.skipTest("mmdc установлен, тест требует его отсутствия")

        result = subprocess.run(
            [sys.executable, str(TESTS_DIR / "mermaid-preprocess.py")],
            cwd=self.tmpdir, capture_output=True, text=True, timeout=10,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("mmdc", result.stderr)

    def test_main_help_succeeds(self) -> None:
        """main() с --help возвращает 0"""
        import subprocess

        result = subprocess.run(
            [sys.executable, str(TESTS_DIR / "mermaid-preprocess.py"), "--help"],
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("Mermaid", result.stdout)


class TestServeMain(unittest.TestCase):
    """Тесты main() функции serve.py"""

    def test_main_help_succeeds(self) -> None:
        """serve.py --help возвращает 0 и содержит описание"""
        import subprocess
        result = subprocess.run(
            [sys.executable, str(TESTS_DIR / "serve.py"), "--help"],
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("Renault Symbol", result.stdout)

    def test_main_nonexistent_dir_exits_nonzero(self) -> None:
        """serve.py с несуществующей директорией завершается с ошибкой"""
        import subprocess
        import uuid
        bad_dir = tempfile.gettempdir() / Path(f"nonexistent_{uuid.uuid4().hex[:8]}")
        result = subprocess.run(
            [sys.executable, str(TESTS_DIR / "serve.py"), "--dir", str(bad_dir)],
            capture_output=True, text=True, timeout=10,
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
                [sys.executable, str(TESTS_DIR / "serve.py"), "--dir", str(html_dir),
                 "--verbose", "--no-browser", "--port", "19100"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
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
            "<html><body>INDEX</body></html>", encoding="utf-8")
        (cls.html_dir / "test.svg").write_text(
            '<svg xmlns="http://www.w3.org/2000/svg"></svg>', encoding="utf-8")
        (cls.html_dir / "sub").mkdir()
        (cls.html_dir / "sub" / "page.html").write_text(
            "<html><body>SUB PAGE</body></html>", encoding="utf-8")

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
        import json
        from scripts.serve import _reset_oem_catalog
        _reset_oem_catalog()
        code, body = self._get("/api/oem-search?q=7700274177")
        self.assertEqual(code, 200)
        data = json.loads(body)
        self.assertIn("query", data)
        self.assertIn("results", data)

    def test_get_oem_catalog_json(self) -> None:
        """GET /api/oem-catalog.json возвращает полный каталог"""
        import json
        from scripts.serve import _reset_oem_catalog
        _reset_oem_catalog()
        code, body = self._get("/api/oem-catalog.json")
        self.assertEqual(code, 200)
        data = json.loads(body)
        self.assertIsInstance(data, list)


# ══════════════════════════════════════════════════════════════════
# PDF-A4
# ══════════════════════════════════════════════════════════════════
class TestPdfA4(unittest.TestCase):
    """Тесты конвертера Letter → A4"""

    @staticmethod
    def _import_pdf_a4() -> object | None:
        """Импортирует pdf-a4.py (имя с дефисами), возвращает None если pikepdf нет"""
        import importlib.util
        try:
            spec = importlib.util.spec_from_file_location(
                "pdf_a4",
                TESTS_DIR / "pdf-a4.py",
                submodule_search_locations=[],
            )
            mod = importlib.util.module_from_spec(spec)
            sys.modules["pdf_a4"] = mod
            spec.loader.exec_module(mod)
            return mod
        except (ModuleNotFoundError, ImportError):
            return None

    def setUp(self) -> None:
        self.tmpdir = Path(tempfile.mkdtemp(prefix="pdf_a4_test_"))

    def tearDown(self) -> None:
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_letter_to_a4_returns_false_on_missing(self) -> None:
        """letter_to_a4 возвращает False для несуществующего файла"""
        mod = self._import_pdf_a4()
        if mod is None:
            self.skipTest("pikepdf не установлен")

        result = mod.letter_to_a4("/nonexistent/input.pdf", str(self.tmpdir / "out.pdf"))
        self.assertFalse(result)

    @staticmethod
    def _make_letter_pdf(path: Path, mod, num_pages: int = 1) -> None:
        """Создать Letter-size PDF с указанным числом страниц."""
        from pikepdf import Pdf
        pdf = Pdf.new()
        for _ in range(num_pages):
            page = pdf.add_blank_page()
            page.MediaBox = [0, 0, mod.LETTER_W, mod.LETTER_H]
        pdf.save(str(path))
        pdf.close()

    def test_letter_to_a4_converts_letter_to_a4(self) -> None:
        """letter_to_a4 конвертирует Letter PDF в A4"""
        mod = self._import_pdf_a4()
        if mod is None:
            self.skipTest("pikepdf не установлен")

        in_pdf = self.tmpdir / "letter.pdf"
        self._make_letter_pdf(in_pdf, mod)

        out_pdf = self.tmpdir / "output.pdf"
        result = mod.letter_to_a4(str(in_pdf), str(out_pdf))
        self.assertTrue(result)
        self.assertTrue(out_pdf.exists())

        # Проверяем A4 размеры
        from pikepdf import Pdf
        pdf2 = Pdf.open(str(out_pdf))
        mb = pdf2.pages[0].MediaBox
        w = float(mb[2]) - float(mb[0])
        h = float(mb[3]) - float(mb[1])
        pdf2.close()

        self.assertAlmostEqual(w, mod.A4_W, delta=5)
        self.assertAlmostEqual(h, mod.A4_H, delta=5)

    def test_letter_to_a4_handles_already_a4(self) -> None:
        """letter_to_a4 не меняет A4 PDF (нет Letter-страниц)"""
        mod = self._import_pdf_a4()
        if mod is None:
            self.skipTest("pikepdf не установлен")

        from pikepdf import Pdf
        in_pdf = self.tmpdir / "a4.pdf"
        pdf = Pdf.new()
        page = pdf.add_blank_page()
        page.MediaBox = [0, 0, mod.A4_W, mod.A4_H]
        pdf.save(str(in_pdf))
        pdf.close()

        out_pdf = self.tmpdir / "output.pdf"
        result = mod.letter_to_a4(str(in_pdf), str(out_pdf))
        self.assertTrue(result)
        self.assertTrue(out_pdf.exists())

    def test_letter_to_a4_multiple_pages(self) -> None:
        """letter_to_a4 конвертирует многостраничный Letter PDF"""
        mod = self._import_pdf_a4()
        if mod is None:
            self.skipTest("pikepdf не установлен")

        in_pdf = self.tmpdir / "multi.pdf"
        self._make_letter_pdf(in_pdf, mod, num_pages=3)

        from pikepdf import Pdf
        out_pdf = self.tmpdir / "output.pdf"
        result = mod.letter_to_a4(str(in_pdf), str(out_pdf))
        self.assertTrue(result)

        # Проверяем, что все страницы сконвертированы
        pdf2 = Pdf.open(str(out_pdf))
        self.assertEqual(len(pdf2.pages), 3)
        for p in pdf2.pages:
            w = float(p.MediaBox[2]) - float(p.MediaBox[0])
            self.assertAlmostEqual(w, mod.A4_W, delta=5)
        pdf2.close()

    def test_letter_to_a4_cropbox_also_converted(self) -> None:
        """letter_to_a4 обновляет CropBox если он совпадает с Letter"""
        mod = self._import_pdf_a4()
        if mod is None:
            self.skipTest("pikepdf не установлен")

        from pikepdf import Pdf
        in_pdf = self.tmpdir / "crop.pdf"
        pdf = Pdf.new()
        page = pdf.add_blank_page()
        page.MediaBox = [0, 0, mod.LETTER_W, mod.LETTER_H]
        page.CropBox = [0, 0, mod.LETTER_W, mod.LETTER_H]
        pdf.save(str(in_pdf))
        pdf.close()

        out_pdf = self.tmpdir / "output.pdf"
        mod.letter_to_a4(str(in_pdf), str(out_pdf))

        pdf2 = Pdf.open(str(out_pdf))
        crop = pdf2.pages[0].CropBox
        cw = float(crop[2]) - float(crop[0])
        self.assertAlmostEqual(cw, mod.A4_W, delta=5)
        pdf2.close()

    def test_letter_to_a4_with_content_stream(self) -> None:
        """letter_to_a4 обрабатывает страницу с content stream"""
        mod = self._import_pdf_a4()
        if mod is None:
            self.skipTest("pikepdf не установлен")

        from pikepdf import Pdf, Stream
        in_pdf = self.tmpdir / "content.pdf"
        pdf = Pdf.new()
        page = pdf.add_blank_page()
        page.MediaBox = [0, 0, mod.LETTER_W, mod.LETTER_H]
        page.Contents = Stream(pdf, b"q\n1 0 0 1 0 0 cm\nQ\n")
        pdf.save(str(in_pdf))
        pdf.close()

        out_pdf = self.tmpdir / "output.pdf"
        result = mod.letter_to_a4(str(in_pdf), str(out_pdf))
        self.assertTrue(result)

    def test_main_help_succeeds(self) -> None:
        """pdf-a4.py --help возвращает 0"""
        import subprocess
        result = subprocess.run(
            [sys.executable, str(TESTS_DIR / "pdf-a4.py"), "--help"],
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(result.returncode, 0)

    def test_main_missing_pdf_exits_with_error(self) -> None:
        """pdf-a4.py с несуществующим файлом завершается с ненулевым кодом"""
        import subprocess
        result = subprocess.run(
            [sys.executable, str(TESTS_DIR / "pdf-a4.py"),
             "/nonexistent/input.pdf", str(self.tmpdir / "out.pdf")],
            capture_output=True, text=True, timeout=10,
        )
        self.assertNotEqual(result.returncode, 0)

    def test_letter_to_a4_no_pikepdf_returns_false(self) -> None:
        """letter_to_a4 возвращает False если pikepdf не установлен (через _get_pikepdf)"""
        from unittest.mock import patch
        mod = self._import_pdf_a4()
        if mod is None:
            self.skipTest("pikepdf не установлен")

        with patch.object(mod, "_get_pikepdf", return_value=(None, None, None)):
            result = mod.letter_to_a4("/some/input.pdf", "/some/output.pdf")
        self.assertFalse(result)

    def test_letter_to_a4_invalid_pdf_returns_false(self) -> None:
        """letter_to_a4 возвращает False для невалидного PDF"""
        mod = self._import_pdf_a4()
        if mod is None:
            self.skipTest("pikepdf не установлен")

        bad_pdf = self.tmpdir / "bad.pdf"
        bad_pdf.write_bytes(b"not a valid pdf file at all")
        out_pdf = self.tmpdir / "result.pdf"

        result = mod.letter_to_a4(str(bad_pdf), str(out_pdf))
        self.assertFalse(result)


# ══════════════════════════════════════════════════════════════════
# MERMAID MDBOOK PREPROCESSOR
# ══════════════════════════════════════════════════════════════════
class TestMermaidMdbookPreprocessor(unittest.TestCase):
    """Тесты mdBook preprocessor для Mermaid"""

    @staticmethod
    def _import_preprocessor() -> object:
        """Импортирует mermaid-mdbook-preprocessor.py (имя с дефисами)"""
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "mermaid_mdbook_preprocessor",
            TESTS_DIR / "mermaid-mdbook-preprocessor.py",
            submodule_search_locations=[],
        )
        mod = importlib.util.module_from_spec(spec)
        sys.modules["mermaid_mdbook_preprocessor"] = mod
        spec.loader.exec_module(mod)
        return mod

    def test_collect_pending_finds_uncached_blocks(self) -> None:
        """collect_pending находит блоки без SVG в кеше"""
        mod = self._import_preprocessor()

        tmpdir = Path(tempfile.mkdtemp(prefix="preproc_test_"))
        try:
            cache_dir = tmpdir / "img" / "mermaid"
            cache_dir.mkdir(parents=True)

            book_sections = [
                {"Chapter": {"content": "text\n```mermaid\ngraph TD;\nA-->B;\n```\nend"}}
            ]

            pending = mod.collect_pending(book_sections, cache_dir)
            self.assertEqual(len(pending), 1)
            self.assertIn("graph TD;", list(pending.values())[0])
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_collect_pending_skips_cached(self) -> None:
        """collect_pending пропускает блоки с SVG в кеше"""
        mod = self._import_preprocessor()
        from scripts.mermaid_core import hash_mermaid

        tmpdir = Path(tempfile.mkdtemp(prefix="preproc_cached_"))
        try:
            cache_dir = tmpdir / "img" / "mermaid"
            cache_dir.mkdir(parents=True)

            source = "graph TD;\nA-->B;"
            h = hash_mermaid(source)
            (cache_dir / f"{h}.svg").write_text("<svg></svg>", encoding="utf-8")

            book_sections = [
                {"Chapter": {"content": f"```mermaid\n{source}\n```"}}
            ]

            pending = mod.collect_pending(book_sections, cache_dir)
            self.assertEqual(len(pending), 0)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_collect_pending_skips_empty_and_long(self) -> None:
        """collect_pending пропускает пустые и слишком длинные блоки"""
        mod = self._import_preprocessor()

        tmpdir = Path(tempfile.mkdtemp(prefix="preproc_skips_"))
        try:
            cache_dir = tmpdir / "cache"
            cache_dir.mkdir()

            book_sections = [
                {"Chapter": {"content": "```mermaid\n\n```"}},
                {"Chapter": {"content": f"```mermaid\n{'x' * (mod.MAX_BLOCK_LEN + 1)}\n```"}},
            ]

            pending = mod.collect_pending(book_sections, cache_dir)
            self.assertEqual(len(pending), 0)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_replace_in_book_substitutes_cached_blocks(self) -> None:
        """replace_in_book заменяет блоки на SVG-ссылки если SVG в кеше"""
        mod = self._import_preprocessor()
        from scripts.mermaid_core import hash_mermaid

        tmpdir = Path(tempfile.mkdtemp(prefix="preproc_replace_"))
        try:
            cache_dir = tmpdir / "cache"
            cache_dir.mkdir()
            src_dir = tmpdir / "src"
            src_dir.mkdir()

            source = "graph TD;\nA-->B;"
            h = hash_mermaid(source)
            (cache_dir / f"{h}.svg").write_text("<svg></svg>", encoding="utf-8")

            book_sections = [
                {"Chapter": {"content": f"before\n```mermaid\n{source}\n```\nafter"}}
            ]

            mod.replace_in_book(book_sections, cache_dir, src_dir)
            content = book_sections[0]["Chapter"]["content"]
            self.assertNotIn("```mermaid", content)
            self.assertIn("![Диаграмма]", content)
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_supports_returns_true(self) -> None:
        """supports <renderer> возвращает 'true'"""
        import subprocess
        result = subprocess.run(
            [sys.executable, str(TESTS_DIR / "mermaid-mdbook-preprocessor.py"),
             "supports", "html"],
            capture_output=True, text=True, timeout=5,
        )
        self.assertEqual(result.stdout.strip(), "true")


# ══════════════════════════════════════════════════════════════════
# CATCAR CRAWLER
# ══════════════════════════════════════════════════════════════════
class TestCatcarCrawler(unittest.TestCase):
    """Smoke-тесты для catcar_crawler.py (кодирование, декодирование, парсинг)"""

    maxDiff = None

    def setUp(self):
        from catcar_crawler import decode_l, encode_l, parse_groups, parse_parts
        self.decode_l = decode_l
        self.encode_l = encode_l
        self.parse_groups = parse_groups
        self.parse_parts = parse_parts

    def test_encode_decode_roundtrip(self):
        """Проверка encode→decode даёт те же параметры"""
        params = {
            "st": "40",
            "sts": {"10": "Модель", "20": "Symbol-Thalia", "30": "LU3R", "40": "Механические узлы"},
            "cat_id": "M",
        }
        l_val = self.encode_l(**params)
        decoded = self.decode_l(l_val)
        self.assertEqual(decoded.get("st"), "40")
        self.assertEqual(decoded.get("cat_id"), "M")

    def test_encode_with_group_and_subgroup(self):
        """encode_l с grp_id и subGrp_id"""
        l_val = self.encode_l(
            st="50",
            sts={"10": "Модель", "50": "10 Двигатель"},
            cat_id="M", grp_id="10", subGrp_id="10A",
        )
        decoded = self.decode_l(l_val)
        self.assertEqual(decoded.get("grp_id"), "10")
        self.assertEqual(decoded.get("subGrp_id"), "10A")

    def test_decode_with_url_encoded_input(self):
        """decode_l обрабатывает URL-encoded %3D"""
        # Эмуляция URL-encoded l-параметра с %3D вместо =
        import base64
        import urllib.parse
        raw = 'st==40||sts=={"10":"Модель"}||cat_id==M'
        encoded = urllib.parse.quote(base64.b64encode(raw.encode()).decode(), safe='')
        decoded = self.decode_l(encoded)
        self.assertEqual(decoded.get("st"), "40")
        self.assertEqual(decoded.get("cat_id"), "M")

    def test_parse_groups_empty_html(self):
        """parse_groups на пустом HTML возвращает []"""
        groups = self.parse_groups("<html></html>")
        self.assertEqual(groups, [])

    def test_parse_parts_empty_html(self):
        """parse_parts на пустом HTML возвращает []"""
        parts = self.parse_parts("<html></html>")
        self.assertEqual(parts, [])

    def test_parse_groups_with_real_html(self):
        """parse_groups корректно находит группы в реальном HTML"""
        html = """
        <div class="rowblocks hr-bottom" name="10">
            <div class="blocks vertical-align">
                <div class="left_image">
                    <span class="blocks__title">10 Двигатель</span>
                </div>
            </div>
            <div class="blocks"><div>
                <a class="blocks__item" href="http://catcar.info/renault/?l=c3Q9PTUwfHxzdHM9PXsiMTAiOiLQnNC+0LTQtdC70YwiLCIyMCI6IlN5bWJvbC1UaGFsaWEiLCIzMCI6IkxVM1IiLCI0MCI6ItCc0LXRhdCw0L3QuNGH0LXRgdC60LjQtSDRg9C30LvRiyIsIjUwIjoiMTAg0JTQstC40LPQsNGC0LXQu9GMIC8g0JTQstC40LPQsNGC0LXQu9GMINCyINGB0LHQvtGA0LUifXx8bm9wcnM9PTE0MzV8fGJyYW5kPT1SZW5hdWx0fHxub3ByPT0xNDM1fHx0eXBlPT1MVTNSfHxjYXRfaWQ9PU18fGltZz09fHxncnBfaWQ9PTEwfHxzdWJHcnBfaWQ9PTEwQQ==">
                    <span class="blocks__img">
                        <img src="http://ci.catcar.info/renault_2017_01/vignette/10A.png" alt="Двигатель в сборе" title="Двигатель в сборе"/>
                    </span>
                    <span class="blocks__title">Двигатель в сборе</span>
                </a>
            </div></div>
        </div>
        """
        groups = self.parse_groups(html)
        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0]["grp_id"], "10")
        self.assertEqual(len(groups[0]["subgroups"]), 1)
        self.assertEqual(groups[0]["subgroups"][0]["subGrp_id"], "10A")

    def test_parse_parts_with_real_html(self):
        """parse_parts извлекает OEM-номера из HTML-таблицы"""
        html = """
        <table>
            <tr><td>1</td><td>7701472317</td><td></td><td>ДВИГАТЕЛЬ K4J 712</td><td>Тип КПП = МКП</td></tr>
            <tr><td>2</td><td>7700107864</td><td></td><td>ПАТРУБОК ВОЗД. ФИЛ</td><td></td></tr>
        </table>
        """
        parts = self.parse_parts(html)
        self.assertEqual(len(parts), 2)
        self.assertEqual(parts[0]["oem"], "7701472317")
        self.assertEqual(parts[1]["oem"], "7700107864")
        self.assertEqual(parts[0]["name"], "ДВИГАТЕЛЬ K4J 712")
        self.assertEqual(parts[0]["position"], "1")

    def test_parse_parts_skips_header_row(self):
        """parse_parts пропускает строку-заголовок таблицы"""
        html = """
        <table>
            <tr><td>Код</td><td>Номер</td><td>Замены</td><td>Название</td><td>Дополнительная информация</td></tr>
            <tr><td>1</td><td>7701472317</td><td></td><td>ДВИГАТЕЛЬ</td><td></td></tr>
        </table>
        """
        parts = self.parse_parts(html)
        self.assertEqual(len(parts), 1)
        self.assertEqual(parts[0]["oem"], "7701472317")

    def test_parse_parts_invalid_oem_skipped(self):
        """parse_parts пропускает не-цифровые OEM"""
        html = """
        <table>
            <tr><td>1</td><td>7701472317</td><td></td><td>ДВИГАТЕЛЬ</td><td></td></tr>
            <tr><td>2</td><td>INVALID</td><td></td><td>НЕ OEM</td><td></td></tr>
        </table>
        """
        parts = self.parse_parts(html)
        self.assertEqual(len(parts), 1)
        self.assertEqual(parts[0]["oem"], "7701472317")


# ══════════════════════════════════════════════════════════════════
# ELCATS CRAWLER
# ══════════════════════════════════════════════════════════════════
class TestElcatsCrawler(unittest.TestCase):
    """Smoke-тесты для elcats_crawler.py (парсинг, main)"""

    maxDiff = None

    def setUp(self):
        from elcats_crawler import parse_units, parse_callback_response, _save_results, main as elcats_main
        self.parse_units = parse_units
        self.parse_callback_response = parse_callback_response
        self._save_results = _save_results
        self.elcats_main = elcats_main

    def test_main_help_succeeds(self):
        """elcats_crawler.main() с --help через subprocess возвращает 0"""
        import subprocess
        import sys
        result = subprocess.run(
            [sys.executable, "scripts/elcats_crawler.py", "--help"],
            capture_output=True, text=True, timeout=5,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("usage:", result.stdout.lower())

    def test_parse_units_empty_html(self):
        """parse_units на пустом HTML возвращает []"""
        units = self.parse_units("<html></html>")
        self.assertEqual(units, [])

    def test_parse_units_with_submit_pattern(self):
        """parse_units находит unit GUID в submit-паттерне"""
        html = """
        <a href="javascript:__doPostBack('ctl00$MainContent$UnitList$ctrl1$UnitLink','')"
           onclick="submit('1792b579-3be7-4ec0-ad76-f70e952158f1','550e8400-e29b-41d4-a716-446655440000')"
           title="Двигатель K4J 1.4 16V">K4J</a>
        """
        units = self.parse_units(html)
        self.assertEqual(len(units), 1)
        self.assertEqual(units[0]["guid"], "550e8400-e29b-41d4-a716-446655440000")

    def test_parse_units_deduplicates(self):
        """parse_units не добавляет дубликаты GUID"""
        html = """
        <a onclick="submit('1792b579-3be7-4ec0-ad76-f70e952158f1','550e8400-e29b-41d4-a716-446655440000')" title="First">A</a>
        <a onclick="submit('1792b579-3be7-4ec0-ad76-f70e952158f1','550e8400-e29b-41d4-a716-446655440000')" title="Second">B</a>
        """
        units = self.parse_units(html)
        self.assertEqual(len(units), 1)

    def test_parse_units_uses_imageunit_fallback(self):
        """parse_units без submit находит через ImageUnitHandler"""
        html = '<img src="ImageUnitHandler.ashx?Unit=550e8400-e29b-41d4-a716-446655440000">'
        units = self.parse_units(html)
        self.assertEqual(len(units), 1)
        self.assertEqual(units[0]["guid"], "550e8400-e29b-41d4-a716-446655440000")

    def test_parse_callback_response_empty(self):
        """parse_callback_response на пустом ответе возвращает []"""
        parts = self.parse_callback_response("")
        self.assertEqual(parts, [])

    def test_parse_callback_response_with_prefix(self):
        """parse_callback_response удаляет префикс 0|"""
        parts = self.parse_callback_response("0|")
        self.assertEqual(parts, [])

    def test_parse_callback_response_with_real_data(self):
        """parse_callback_response извлекает code_key и description"""
        response = """0|<table>
        <tr>
            <td>1</td>
            <td><img src="/Codes.ashx?Key=abc123" alt="code"></td>
            <td style="text-align:left">ДВИГАТЕЛЬ K4J 712</td>
            <td>Тип КПП = МКП</td>
        </tr>
        <tr>
            <td>2</td>
            <td><img src="/Codes.ashx?Key=def456" alt="code"></td>
            <td style="text-align:left">ПАТРУБОК ВОЗД. ФИЛ</td>
            <td></td>
        </tr>
        </table>"""
        parts = self.parse_callback_response(response)
        self.assertEqual(len(parts), 2)
        self.assertEqual(parts[0]["code_key"], "abc123")
        self.assertEqual(parts[0]["description"], "ДВИГАТЕЛЬ K4J 712")
        self.assertEqual(parts[1]["code_key"], "def456")
        self.assertEqual(parts[1]["description"], "ПАТРУБОК ВОЗД. ФИЛ")

    def test_parse_callback_response_skips_no_info(self):
        """parse_callback_response пропускает 'Нет информации'"""
        response = """0|<table>
        <tr>
            <td>1</td>
            <td><img src="Codes.ashx?Key=abc123"></td>
            <td>Нет информации</td>
        </tr>
        </table>"""
        parts = self.parse_callback_response(response)
        self.assertEqual(len(parts), 0)

    def test_parse_callback_response_marks_alternative(self):
        """parse_callback_response помечает is_alternative=True"""
        response = """0|<table>
        <tr>
            <td>1</td>
            <td><img src="Codes.ashx?Key=abc123"></td>
            <td>Альтернативное предложение</td>
            <td style="text-align:left">ДВИГАТЕЛЬ</td>
        </tr>
        </table>"""
        parts = self.parse_callback_response(response)
        self.assertEqual(len(parts), 1)
        self.assertTrue(parts[0]["is_alternative"])

    def test_save_results_creates_file(self):
        """_save_results пишет JSON-файл"""
        import json
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            path = Path(f.name)
        try:
            self._save_results(path, [
                {"oem": "7701472317", "code_key": "abc", "description": "ДВИГАТЕЛЬ"},
            ], {"grp1"}, total_oems=1)
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(data["statistics"]["total_oems"], 1)
            self.assertEqual(len(data["parts"]), 1)
            self.assertEqual(data["parts"][0]["oem"], "7701472317")
        finally:
            path.unlink(missing_ok=True)


# ══════════════════════════════════════════════════════════════════
# MERGE OEM CATALOGS
# ══════════════════════════════════════════════════════════════════
class TestMergeOemCatalogs(unittest.TestCase):
    """Тесты слияния OEM-каталогов"""

    maxDiff = None

    def setUp(self) -> None:
        self.tmpdir = Path(tempfile.mkdtemp(prefix="merge_oem_"))
        # Свежий импорт модуля (сброс кеша)
        if "scripts.merge_oem_catalogs" in sys.modules:
            del sys.modules["scripts.merge_oem_catalogs"]
        from scripts import merge_oem_catalogs
        self.mod = merge_oem_catalogs

    def tearDown(self) -> None:
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _make_catalog(self, filename: str, data: object) -> Path:
        """Создать JSON-каталог во временной папке."""
        path = self.tmpdir / filename
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return path

    # ── extract_oem ───────────────────────────────────────────────

    def test_extract_oem_from_oem_field(self) -> None:
        """oem из поля 'oem'."""
        self.assertEqual(self.mod.extract_oem({"oem": "7701472317"}), "7701472317")

    def test_extract_oem_from_number_field(self) -> None:
        """oem из поля 'number'."""
        self.assertEqual(self.mod.extract_oem({"number": "8200421359"}), "8200421359")

    def test_extract_oem_from_code_field(self) -> None:
        """oem из поля 'code'."""
        self.assertEqual(self.mod.extract_oem({"code": "6001549368"}), "6001549368")

    def test_extract_oem_cleans_spaces_and_dashes(self) -> None:
        """Очистка пробелов и дефисов."""
        self.assertEqual(
            self.mod.extract_oem({"oem": " 77-01-472-317 "}),
            "7701472317",
        )

    def test_extract_oem_missing_returns_empty(self) -> None:
        """Без oem/number/code — пустая строка."""
        self.assertEqual(self.mod.extract_oem({"name": "Bolt"}), "")

    # ── load_catalog ──────────────────────────────────────────────

    def test_load_catalog_flat_list(self) -> None:
        """Плоский список — возвращается как есть."""
        cat = self._make_catalog("src.json", [{"oem": "A"}, {"oem": "B"}])
        result = self.mod.load_catalog(cat, "test")
        self.assertEqual(result, [{"oem": "A"}, {"oem": "B"}])

    def test_load_catalog_dict_with_parts(self) -> None:
        """dict с ключом parts — извлекается список."""
        cat = self._make_catalog("src.json", {"parts": [{"oem": "A"}]})
        result = self.mod.load_catalog(cat, "test")
        self.assertEqual(result, [{"oem": "A"}])

    def test_load_catalog_dict_with_oems(self) -> None:
        """dict с ключом oems — извлекается список."""
        cat = self._make_catalog("src.json", {"oems": [{"oem": "B"}]})
        result = self.mod.load_catalog(cat, "test")
        self.assertEqual(result, [{"oem": "B"}])

    def test_load_catalog_list_of_categories(self) -> None:
        """Список категорий с вложенными parts — разворачивается с category."""
        data = [
            {"name": "Engine", "parts": [{"oem": "A"}, {"oem": "B"}]},
            {"name": "Gearbox", "parts": [{"oem": "C"}]},
        ]
        cat = self._make_catalog("src.json", data)
        result = self.mod.load_catalog(cat, "test")
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]["category"], "Engine")
        self.assertEqual(result[2]["category"], "Gearbox")

    def test_load_catalog_missing_file(self) -> None:
        """Отсутствующий файл — пустой список + warning."""
        result = self.mod.load_catalog(self.tmpdir / "nonexistent.json", "test")
        self.assertEqual(result, [])

    def test_load_catalog_bad_json(self) -> None:
        """Битый JSON — пустой список + error."""
        bad = self.tmpdir / "bad.json"
        bad.write_text("{bad json}", encoding="utf-8")
        result = self.mod.load_catalog(bad, "test")
        self.assertEqual(result, [])

    def test_load_catalog_parts_not_list(self) -> None:
        """parts не список — пустой результат."""
        cat = self._make_catalog("src.json", {"parts": "not_a_list"})
        result = self.mod.load_catalog(cat, "test")
        self.assertEqual(result, [])

    # ── merge_catalogs ────────────────────────────────────────────

    def test_merge_catalogs_deduplicates_by_oem(self) -> None:
        """Дубликаты OEM схлопываются, source_parts пополняется."""
        s1 = self._make_catalog("s1.json", [{"oem": "A", "name": "Part A"}])
        s2 = self._make_catalog("s2.json", [{"oem": "A", "name": "Part A"}])
        self.mod.SOURCES = {"s1": s1, "s2": s2}
        out = self.tmpdir / "out.json"
        result = self.mod.merge_catalogs(out)
        self.assertEqual(result["statistics"]["total_unique_oems"], 1)
        self.assertEqual(
            result["parts"][0]["source_parts"], ["s1", "s2"],
        )

    def test_merge_catalogs_multiple_oems(self) -> None:
        """Разные OEM — все сохраняются."""
        src = self._make_catalog("src.json", [
            {"oem": "A", "name": "Part A"},
            {"oem": "B", "name": "Part B"},
        ])
        self.mod.SOURCES = {"s": src}
        result = self.mod.merge_catalogs(self.tmpdir / "out.json")
        self.assertEqual(result["statistics"]["total_unique_oems"], 2)

    def test_merge_catalogs_no_oem_skipped(self) -> None:
        """Детали без OEM — пропускаются."""
        src = self._make_catalog("src.json", [
            {"oem": "A", "name": "Part A"},
            {"name": "No OEM"},
        ])
        self.mod.SOURCES = {"s": src}
        result = self.mod.merge_catalogs(self.tmpdir / "out.json")
        self.assertEqual(result["statistics"]["total_unique_oems"], 1)

    def test_merge_catalogs_empty_sources(self) -> None:
        """Все источники пусты — пустой каталог."""
        src = self._make_catalog("s1.json", [])
        self.mod.SOURCES = {"s1": src}
        result = self.mod.merge_catalogs(self.tmpdir / "out.json")
        self.assertEqual(result["statistics"]["total_unique_oems"], 0)
        self.assertEqual(result["parts"], [])

    def test_merge_catalogs_writes_file(self) -> None:
        """merge_catalogs записывает JSON на диск."""
        src = self._make_catalog("src.json", [{"oem": "A", "name": "Part A"}])
        self.mod.SOURCES = {"s": src}
        out = self.tmpdir / "out.json"
        self.mod.merge_catalogs(out)
        self.assertTrue(out.exists())
        data = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(data["statistics"]["total_unique_oems"], 1)

    def test_merge_catalogs_statistics(self) -> None:
        """Проверка статистики: 1, 2, 3 источника."""
        s1 = self._make_catalog("s1.json", [{"oem": "A"}, {"oem": "B"}])
        s2 = self._make_catalog("s2.json", [{"oem": "A"}, {"oem": "C"}])
        s3 = self._make_catalog("s3.json", [{"oem": "A"}])
        self.mod.SOURCES = {"s1": s1, "s2": s2, "s3": s3}
        result = self.mod.merge_catalogs(self.tmpdir / "out.json")
        stats = result["statistics"]
        self.assertEqual(stats["total_unique_oems"], 3)
        self.assertEqual(stats["oems_found_in_1_source"], 2)  # B, C
        self.assertEqual(stats["oems_found_in_2_sources"], 0)
        self.assertEqual(stats["oems_found_in_all_3_sources"], 1)  # A

    def test_merge_catalogs_uses_category_fallback(self) -> None:
        """Пробует category → group → subgroup → grp_name → parts_group."""
        src = self._make_catalog("src.json", [
            {"oem": "A", "name": "X", "subgroup": "Engine"},
        ])
        self.mod.SOURCES = {"s": src}
        result = self.mod.merge_catalogs(self.tmpdir / "out.json")
        self.assertEqual(result["parts"][0].get("subgroup"), "Engine")


# ══════════════════════════════════════════════════════════════════
# ЗАПУСК
# ══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    unittest.main()
