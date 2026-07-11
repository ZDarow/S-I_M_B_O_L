#!/usr/bin/env python3
"""
Тесты для TestSitemap.
"""

import shutil
import sys
import tempfile
import unittest
from pathlib import Path


TESTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TESTS_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))


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
        (self.html_dir / "dvigatel" / "3-1.html").write_text("<h1>Engine</h1>", encoding="utf-8")
        (self.html_dir / "dvigatel" / "3-2.html").write_text("<h1>Fuel</h1>", encoding="utf-8")

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
        self.assertIn("</urlset>", content)

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


if __name__ == "__main__":
    unittest.main()
