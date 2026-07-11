#!/usr/bin/env python3
"""
Тесты для TestMermaidCore, TestMermaidPreprocess, TestMermaidMdbookPreprocessor.
"""

import os
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

        text = "```mermaid\ngraph TD; A;\n```\ntext\n```mermaid\ngraph TD; B;\n```\n"
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
        fake_result = subprocess.CompletedProcess(
            args=["mmdc"], returncode=1, stdout="", stderr="error"
        )
        with (
            patch("scripts.mermaid_core.find_mmdc", return_value="/usr/bin/fake-mmdc"),
            patch("subprocess.run", return_value=fake_result),
        ):
            result = render_svg("graph TD;\nX;", Path(tmp_dir) / "out.svg")
        self.assertFalse(result)

    def test_render_svg_returns_false_on_timeout(self) -> None:
        """render_svg возвращает False при таймауте mmdc"""
        import subprocess
        from scripts.mermaid_core import render_svg, MMDC_TIMEOUT
        from unittest.mock import patch

        tmp_dir = tempfile.gettempdir()
        with (
            patch("scripts.mermaid_core.find_mmdc", return_value="/usr/bin/fake-mmdc"),
            patch(
                "subprocess.run",
                side_effect=subprocess.TimeoutExpired(cmd="mmdc", timeout=MMDC_TIMEOUT),
            ),
        ):
            result = render_svg("graph TD;\nZ;", Path(tmp_dir) / "out.svg")
        self.assertFalse(result)


# ══════════════════════════════════════════════════════════════════
# SERVE
# ══════════════════════════════════════════════════════════════════


# ══════════════════════════════════════════════════════════════════
# MERMAID PREPROCESS
# ══════════════════════════════════════════════════════════════════
class TestMermaidPreprocess(unittest.TestCase):
    """Тесты препроцессора Mermaid"""

    @staticmethod
    def _import_preprocess() -> Any:
        """Импортирует mermaid-preprocess.py (имя с дефисами)"""
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "mermaid_preprocess",
            PROJECT_ROOT / "mermaid-preprocess.py",
            submodule_search_locations=[],
        )
        assert spec is not None, "Не найден mermaid-preprocess.py"
        assert spec.loader is not None
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

        mod = self._import_preprocess()

        # Создаём .md и его бэкап
        md = self.src_dir / "restore_main.md"
        original = "content\n```mermaid\ngraph TD;\nA;\n```\nend"
        md.write_text(original, encoding="utf-8")
        backup = md.with_suffix(md.suffix + mod.BACKUP_PREFIX)
        backup.write_text("restored content", encoding="utf-8")

        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "mermaid-preprocess.py"), "--restore"],
            cwd=self.tmpdir,
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(md.read_text(encoding="utf-8"), "restored content")

    def test_main_restore_no_backup(self) -> None:
        """main() с --restore не падает если бэкапов нет"""
        import subprocess

        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "mermaid-preprocess.py"), "--restore"],
            cwd=self.tmpdir,
            capture_output=True,
            text=True,
            timeout=10,
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
            [sys.executable, str(PROJECT_ROOT / "mermaid-preprocess.py"), "--render-only"],
            cwd=self.tmpdir,
            capture_output=True,
            text=True,
            timeout=10,
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
            [sys.executable, str(PROJECT_ROOT / "mermaid-preprocess.py")],
            cwd=self.tmpdir,
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("mmdc", result.stderr)

    def test_main_help_succeeds(self) -> None:
        """main() с --help возвращает 0"""
        import subprocess

        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "mermaid-preprocess.py"), "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("Mermaid", result.stdout)


# ══════════════════════════════════════════════════════════════════
# MERMAID MDBOOK PREPROCESSOR
# ══════════════════════════════════════════════════════════════════
class TestMermaidMdbookPreprocessor(unittest.TestCase):
    """Тесты mdBook preprocessor для Mermaid"""

    @staticmethod
    def _import_preprocessor() -> Any:
        """Импортирует mermaid-mdbook-preprocessor.py (имя с дефисами)"""
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "mermaid_mdbook_preprocessor",
            PROJECT_ROOT / "mermaid-mdbook-preprocessor.py",
            submodule_search_locations=[],
        )
        assert spec is not None, "Не найден mermaid-mdbook-preprocessor.py"
        assert spec.loader is not None
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

            book_sections = [{"Chapter": {"content": f"```mermaid\n{source}\n```"}}]

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

            book_sections = [{"Chapter": {"content": f"before\n```mermaid\n{source}\n```\nafter"}}]

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
            [
                sys.executable,
                str(PROJECT_ROOT / "mermaid-mdbook-preprocessor.py"),
                "supports",
                "html",
            ],
            capture_output=True,
            text=True,
            timeout=5,
        )
        self.assertEqual(result.stdout.strip(), "true")


# ══════════════════════════════════════════════════════════════════
# CATCAR CRAWLER
# ══════════════════════════════════════════════════════════════════


if __name__ == "__main__":
    unittest.main()
