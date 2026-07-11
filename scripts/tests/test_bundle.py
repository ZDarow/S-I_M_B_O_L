#!/usr/bin/env python3
"""
Тесты для TestBundlePortable.
"""

import os
import shutil
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path


TESTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TESTS_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))


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
                self.html_dir,
                self.output_dir,
                no_build=True,
                no_archive=True,
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
                self.html_dir,
                self.output_dir,
                no_build=True,
                no_archive=True,
            )
            archive = self.tmpdir / f"{BUNDLE_NAME}.tar.gz"
            self.assertFalse(archive.exists())
        finally:
            bp.SERVE_SCRIPT = orig_serve


# ══════════════════════════════════════════════════════════════════
# GENERATE ILLUSTRATIONS
# ══════════════════════════════════════════════════════════════════


if __name__ == "__main__":
    unittest.main()
