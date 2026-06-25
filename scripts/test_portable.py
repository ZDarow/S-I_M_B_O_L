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
# ЗАПУСК
# ══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    unittest.main()
