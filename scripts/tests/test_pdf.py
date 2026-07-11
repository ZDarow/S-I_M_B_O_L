#!/usr/bin/env python3
"""
Тесты для TestPdfA4.
"""

import shutil
import sys
import tempfile
import unittest
from typing import Any
from pathlib import Path


TESTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TESTS_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ══════════════════════════════════════════════════════════════════
# PDF-A4
# ══════════════════════════════════════════════════════════════════
class TestPdfA4(unittest.TestCase):
    """Тесты конвертера Letter → A4"""

    @staticmethod
    def _import_pdf_a4() -> Any:
        """Импортирует pdf-a4.py (имя с дефисами), возвращает None если pikepdf нет"""
        import importlib.util

        try:
            spec = importlib.util.spec_from_file_location(
                "pdf_a4",
                PROJECT_ROOT / "pdf-a4.py",
                submodule_search_locations=[],
            )
            assert spec is not None, "Не найден pdf-a4.py"
            assert spec.loader is not None
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
            [sys.executable, str(PROJECT_ROOT / "pdf-a4.py"), "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(result.returncode, 0)

    def test_main_missing_pdf_exits_with_error(self) -> None:
        """pdf-a4.py с несуществующим файлом завершается с ненулевым кодом"""
        import subprocess

        result = subprocess.run(
            [
                sys.executable,
                str(PROJECT_ROOT / "pdf-a4.py"),
                "/nonexistent/input.pdf",
                str(self.tmpdir / "out.pdf"),
            ],
            capture_output=True,
            text=True,
            timeout=10,
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


if __name__ == "__main__":
    unittest.main()
