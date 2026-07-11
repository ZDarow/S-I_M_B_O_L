#!/usr/bin/env python3
"""
Тесты для TestGenerateIllustrations, TestCatcarCrawler, TestElcatsCrawler, TestMergeOemCatalogs.
"""

import shutil
import sys
import tempfile
import unittest
import json
from pathlib import Path

# One-time modules перемещены в scripts/archive/
_SCRIPTS = Path(__file__).resolve().parent.parent
_ARCHIVE = _SCRIPTS / "archive"
if _ARCHIVE.exists():
    sys.path.insert(0, str(_ARCHIVE))
    sys.path.insert(0, str(_SCRIPTS))  # для _crawler_common и других shared модулей


TESTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = TESTS_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))


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
        from generate_illustrations import svg_header

        result = svg_header("Test", 800, 600)
        self.assertIn('viewBox="0 0 800 600"', result)
        self.assertIn('width="800"', result)
        self.assertIn('height="600"', result)
        self.assertIn("Test", result)

    def test_svg_footer_closes_svg(self) -> None:
        """svg_footer возвращает закрывающий тег"""
        from generate_illustrations import svg_footer

        self.assertEqual(svg_footer(), "</svg>\n")

    def test_rounded_rect_produces_rect(self) -> None:
        """rounded_rect возвращает SVG rect с параметрами"""
        from generate_illustrations import rounded_rect

        result = rounded_rect(10, 20, 100, 50, r=8, fill="#fff", stroke="#000")
        self.assertIn('x="10"', result)
        self.assertIn('y="20"', result)
        self.assertIn('width="100"', result)
        self.assertIn('height="50"', result)
        self.assertIn('rx="8"', result)
        self.assertIn("#fff", result)
        self.assertIn("#000", result)

    def test_label_contains_text(self) -> None:
        """label возвращает SVG text с указанным текстом"""
        from generate_illustrations import label

        result = label("Hello", 50, 60, size=14, color="#333", anchor="middle", bold=True)
        self.assertIn("Hello", result)
        self.assertIn('x="50"', result)
        self.assertIn('y="60"', result)
        self.assertIn('font-size="14"', result)
        self.assertIn("#333", result)
        self.assertIn('font-weight="bold"', result)

    def test_arrow_produces_line(self) -> None:
        """arrow возвращает SVG line с маркером"""
        from generate_illustrations import arrow

        result = arrow(0, 0, 100, 100, color="#666", width=3)
        self.assertIn('x1="0"', result)
        self.assertIn('y1="0"', result)
        self.assertIn('x2="100"', result)
        self.assertIn('y2="100"', result)
        self.assertIn('marker-end="url(#arrow)"', result)

    def test_arrow_def_contains_marker(self) -> None:
        """arrow_def содержит defs с маркером"""
        from generate_illustrations import arrow_def

        result = arrow_def()
        self.assertIn("<defs>", result)
        self.assertIn("<marker", result)
        self.assertIn("arrow", result)

    def test_line_produces_svg_line(self) -> None:
        """line возвращает SVG line без маркера"""
        from generate_illustrations import line

        result = line(10, 20, 30, 40, color="#999", width=1)
        self.assertIn('x1="10"', result)
        self.assertIn('y1="20"', result)
        self.assertIn('x2="30"', result)
        self.assertIn('y2="40"', result)
        self.assertNotIn("marker-end", result)

    def test_main_creates_svg_files(self) -> None:
        """main() создаёт 9 SVG файлов"""
        import generate_illustrations as gi

        orig_dir = gi.OUTPUT_DIR
        try:
            gi.OUTPUT_DIR = str(self.output_dir)
            gi.main()
            svg_files = list(self.output_dir.glob("*.svg"))
            self.assertEqual(len(svg_files), 9)
            expected = [
                "oil-circuit.svg",
                "coolant-circuit.svg",
                "disc-brake.svg",
                "suspension-mcpherson.svg",
                "battery.svg",
                "timing-belt.svg",
                "noise-isolation-zones.svg",
                "tools.svg",
                "alternator.svg",
            ]
            for name in expected:
                self.assertTrue((self.output_dir / name).exists(), f"Missing: {name}")
        finally:
            gi.OUTPUT_DIR = orig_dir

    def test_svg_files_are_valid_xml(self) -> None:
        """main() создаёт валидные SVG-файлы"""
        import xml.etree.ElementTree as ET
        import generate_illustrations as gi

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
            cat_id="M",
            grp_id="10",
            subGrp_id="10A",
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
        encoded = urllib.parse.quote(base64.b64encode(raw.encode()).decode(), safe="")
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


# ══════════════════════════════════════════════════════════════════
# ELCATS CRAWLER
# ══════════════════════════════════════════════════════════════════
class TestElcatsCrawler(unittest.TestCase):
    """Smoke-тесты для elcats_crawler.py (парсинг, main)"""

    maxDiff = None

    def setUp(self):
        from elcats_crawler import (
            parse_units,
            parse_callback_response,
            _save_results,
            main as elcats_main,
        )

        self.parse_units = parse_units
        self.parse_callback_response = parse_callback_response
        self._save_results = _save_results
        self.elcats_main = elcats_main

    def test_main_help_succeeds(self):
        """elcats_crawler.main() с --help через subprocess возвращает 0"""
        import subprocess
        import sys

        result = subprocess.run(
            [sys.executable, "scripts/archive/elcats_crawler.py", "--help"],
            capture_output=True,
            text=True,
            timeout=5,
            env={**__import__('os').environ, 'PYTHONPATH': 'scripts/archive:scripts'},
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
            self._save_results(
                path,
                [
                    {"oem": "7701472317", "code_key": "abc", "description": "ДВИГАТЕЛЬ"},
                ],
                {"grp1"},
                total_oems=1,
            )
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(data["statistics"]["total_oems"], 1)
            self.assertEqual(len(data["parts"]), 1)
            self.assertEqual(data["parts"][0]["oem"], "7701472317")
        finally:
            path.unlink(missing_ok=True)


# ══════════════════════════════════════════════════════════════════
# MERGE OEM CATALOGS
# ══════════════════════════════════════════════════════════════════


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
        import merge_oem_catalogs

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
            result["parts"][0]["source_parts"],
            ["s1", "s2"],
        )

    def test_merge_catalogs_multiple_oems(self) -> None:
        """Разные OEM — все сохраняются."""
        src = self._make_catalog(
            "src.json",
            [
                {"oem": "A", "name": "Part A"},
                {"oem": "B", "name": "Part B"},
            ],
        )
        self.mod.SOURCES = {"s": src}
        result = self.mod.merge_catalogs(self.tmpdir / "out.json")
        self.assertEqual(result["statistics"]["total_unique_oems"], 2)

    def test_merge_catalogs_no_oem_skipped(self) -> None:
        """Детали без OEM — пропускаются."""
        src = self._make_catalog(
            "src.json",
            [
                {"oem": "A", "name": "Part A"},
                {"name": "No OEM"},
            ],
        )
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
        src = self._make_catalog(
            "src.json",
            [
                {"oem": "A", "name": "X", "subgroup": "Engine"},
            ],
        )
        self.mod.SOURCES = {"s": src}
        result = self.mod.merge_catalogs(self.tmpdir / "out.json")
        self.assertEqual(result["parts"][0].get("subgroup"), "Engine")


# ══════════════════════════════════════════════════════════════════
# ЗАПУСК
# ══════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    unittest.main()


if __name__ == "__main__":
    unittest.main()
