#!/usr/bin/env python3
"""
Полный краулер каталога запчастей Renault с elcats.ru.

Pipeline:
  1. Group.aspx?Model=GUID — 3-колоночное дерево (67 групп, 186 подгрупп)
  2. Unit.aspx?Model=GUID&Subgroup=GUID — список Unit'ов (диаграмм)
  3. Parts.aspx?Model=GUID&Unit=GUID — страница с позициями
  4. ASP.NET callback (WebForm_DoCallback) с номером позиции → HTML с ключами кода
  5. Codes.ashx?Key=... — PNG-изображение номера → OCR → OEM-номер

Использование:
  python3 scripts/elcats_crawler.py                    # полный запуск
  python3 scripts/elcats_crawler.py --resume           # продолжить
  python3 scripts/elcats_crawler.py --output cat.json  # кастомный путь
  python3 scripts/elcats_crawler.py --test             # только 1 подгруппа
"""

import argparse
import json
import logging
import re
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

import requests

from _crawler_common import get_session

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ─── Конфигурация ────────────────────────────────────────────────
BASE_URL = "http://www.elcats.ru/renault"
MODEL_GUID = "1792b579-3be7-4ec0-ad76-f70e952158f1"
DELAY = 0.25  # секунд между запросами (анти-бан)
MAX_POSITIONS = 20  # макс номер позиции на Parts.aspx
RESUME_FILE = Path(tempfile.gettempdir()) / "elcats_progress.json"

# ─── Структура каталога (загружается из JSON) ─────────────────
CATALOG_TREE_PATH = Path(__file__).resolve().parent / "data" / "elcats_catalog_tree.json"
try:
    with open(CATALOG_TREE_PATH, encoding="utf-8") as _f:
        CATALOG_TREE: dict[str, Any] = json.load(_f)
except (FileNotFoundError, json.JSONDecodeError) as _e:
    logger.warning("Не удалось загрузить %s: %s", CATALOG_TREE_PATH, _e)
    CATALOG_TREE = {"modelGuid": MODEL_GUID, "columns": []}

# ─── Вспомогательные функции ─────────────────────────────────────

def fetch_unit_page(subgroup_guid: str) -> str | None:
    """Загрузить Unit.aspx для подгруппы — получить список Unit'ов (диаграмм)."""
    url = f"{BASE_URL}/Unit.aspx?Model={MODEL_GUID}&Subgroup={subgroup_guid}"
    try:
        resp = get_session().get(url, timeout=15)
        resp.raise_for_status()
        resp.encoding = "utf-8"
        return resp.text
    except requests.RequestException as exc:
        logger.warning("  Ошибка Unit.aspx: %s", exc)
        return None


def parse_units(html: str) -> list[dict[str, str]]:
    """Извлечь Unit GUID'ы и их заголовки из Unit.aspx."""
    units: list[dict[str, str]] = []
    seen: set[str] = set()
    # Ищем submit('model', 'unit_guid') - для Parts.aspx
    for m in re.finditer(
        r"submit\('([a-f0-9\-]+)','([a-f0-9\-]+)'\)",
        html,
    ):
        unit_guid = m.group(2)
        if unit_guid not in seen:
            seen.add(unit_guid)
            # Ищем title рядом
            title_m = re.search(rf'{re.escape(unit_guid)}[^"]*title="([^"]+)"', html)
            title = title_m.group(1) if title_m else ""
            units.append({"guid": unit_guid, "title": title})

    # Резерв: ищем ImageUnitHandler ссылки
    if not units:
        for m in re.finditer(
            r'ImageUnitHandler\.ashx\?Unit=([a-f0-9\-]+)',
            html,
        ):
            unit_guid = m.group(1)
            if unit_guid not in seen:
                seen.add(unit_guid)
                units.append({"guid": unit_guid, "title": ""})

    return units


def fetch_parts_page(unit_guid: str) -> tuple[str, str, str]:
    """Загрузить Parts.aspx и извлечь ViewState, ViewStateGenerator, EventValidation."""
    url = f"{BASE_URL}/Parts.aspx?Model={MODEL_GUID}&Unit={unit_guid}"
    resp = get_session().get(url, timeout=15)
    resp.encoding = "utf-8"
    html = resp.text

    vs = re.search(r'id="__VIEWSTATE" value="([^"]+)"', html)
    vsg = re.search(r'id="__VIEWSTATEGENERATOR" value="([^"]+)"', html)
    ve = re.search(r'id="__EVENTVALIDATION" value="([^"]+)"', html)

    return (
        vs.group(1) if vs else "",
        vsg.group(1) if vsg else "",
        ve.group(1) if ve else "",
    )


def callback_parts(viewstate: str, vsg: str, ve: str, unit_guid: str, pos: str) -> str | None:
    """ASP.NET WebForm_DoCallback для получения данных по позиции."""
    url = f"{BASE_URL}/Parts.aspx?Model={MODEL_GUID}&Unit={unit_guid}"
    data = {
        "__CALLBACKID": "__Page",
        "__CALLBACKPARAM": pos,
        "__VIEWSTATE": viewstate,
        "__VIEWSTATEGENERATOR": vsg,
        "__EVENTVALIDATION": ve,
    }
    try:
        resp = get_session().post(url, data=data, timeout=15)
        resp.encoding = "utf-8"
        return resp.text
    except requests.RequestException as exc:
        logger.warning("    Callback pos %s error: %s", pos, exc)
        return None


def parse_callback_response(response: str) -> list[dict[str, Any]]:
    """Извлечь коды деталей из ответа callback'а.

    Ответ: 0|<table>...</table>
    Код детали — изображение Codes.ashx?Key=...
    Описание — текст в <td style="text-align:left">
    """
    parts = []

    # Удаляем префикс "0|"
    if response.startswith("0|"):
        response = response[2:]

    # Извлекаем строки таблицы
    rows = re.findall(r"<tr>(.*?)</tr>", response, re.DOTALL | re.IGNORECASE)
    for row_html in rows:
        cells = re.findall(r"<td[^>]*>(.*?)</td>", row_html, re.DOTALL | re.IGNORECASE)
        if len(cells) < 2:
            continue

        # Код детали — изображение (src может быть без кавычек)
        code_img = re.search(r'Codes\.ashx\?Key=([^\s>"\'&]+)', row_html)
        code_key = code_img.group(1) if code_img else ""

        # Описание (обычно второй td)
        description = ""
        for cell in cells:
            clean = re.sub(r"<[^>]+>", "", cell).strip()
            clean = clean.replace("&nbsp;", " ").replace("&lt;", "<").replace("&gt;", ">")
            # Пропускаем позиционный номер (чисто цифровой)
            if clean.isdigit():
                continue
            if clean and clean != "Цена" and not clean.startswith("Альтернативное"):
                description = clean
                break

        # Проверка на "нет информации"
        if "Нет информации" in row_html or "нет информации" in row_html:
            continue

        # Альтернативное предложение
        is_alternative = "Альтернативное" in row_html

        if code_key:
            parts.append({
                "code_key": code_key,  # оставляем URL-encoded для Codes.ashx
                "description": description,
                "is_alternative": is_alternative,
            })

    return parts


def ocr_code_image(code_key: str) -> str:
    """Скачать изображение кода и распознать через Tesseract."""
    url = f"http://www.elcats.ru/Codes.ashx?Key={code_key}"
    try:
        resp = get_session().get(url, timeout=10)
        if resp.status_code != 200 or len(resp.content) < 50:
            return ""
    except requests.RequestException:
        return ""

    # Сохраняем во временный файл
    tmp = Path(tempfile.gettempdir()) / f"elcats_code_{hash(code_key)}.png"
    tmp.write_bytes(resp.content)

    try:
        result = subprocess.run(
            ["tesseract", str(tmp), "stdout", "--psm", "7", "-l", "rus+eng"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        raw = result.stdout.strip()
        # Очищаем: оставляем только цифры и пробелы
        oem = re.sub(r"[^\d\s]", "", raw).strip()
        # Удаляем лишние пробелы, нормализуем формат
        oem = re.sub(r"\s+", " ", oem)
        return oem
    except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
        logger.debug("  OCR error: %s", exc)
        return ""
    finally:
        if tmp.exists():
            tmp.unlink()


# ─── Основной краулер ────────────────────────────────────────────

def crawl_catalog(output_path: Path, test_mode: bool = False, resume: bool = False) -> int:
    """Полный обход каталога.

    Возвращает количество найденных OEM-номеров.
    """
    # Загружаем прогресс, если нужен
    processed = set()
    if resume and RESUME_FILE.exists():
        try:
            processed = set(json.loads(RESUME_FILE.read_text()))
            logger.info("Возобновление: уже обработано %d подгрупп", len(processed))
        except (json.JSONDecodeError, KeyError):
            processed = set()

    results: list[dict[str, Any]] = []
    total_oems = 0
    subgroup_count = 0
    test_limit = 3 if test_mode else 9999

    for column in CATALOG_TREE["columns"]:
        col_name = column["name"]
        for group in column["groups"]:
            group_label = group["label"]
            for sg in group["subgroups"]:
                guid = sg["guid"]
                sub_label = sg["label"]
                subgroup_count += 1

                if guid in processed:
                    logger.debug(
                        "[%s/%s] %s — пропущено (уже обработано)",
                        subgroup_count, 186, sub_label[:40],
                    )
                    continue

                if subgroup_count > test_limit:
                    logger.info("Достигнут лимит, завершаем")
                    # Сохраняем результат и выходим
                    _save_results(output_path, results, processed)
                    return total_oems

                logger.info(
                    "[%s/%s] %s → %s → %s",
                    subgroup_count, 186,
                    col_name[:20], group_label[:30], sub_label[:40],
                )

                time.sleep(DELAY)

                # Шаг 1: Unit.aspx — получить список диаграмм
                unit_html = fetch_unit_page(guid)
                if not unit_html:
                    processed.add(guid)
                    if len(processed) % 5 == 0:
                        RESUME_FILE.write_text(json.dumps(list(processed)))
                    continue

                units = parse_units(unit_html)
                if not units:
                    logger.info("  Нет Unit'ов для этой подгруппы")
                    processed.add(guid)
                    if len(processed) % 5 == 0:
                        RESUME_FILE.write_text(json.dumps(list(processed)))
                    continue

                # Шаг 2: Для каждого Unit'а
                for unit in units:
                    unit_guid = unit["guid"]
                    unit_title = unit.get("title", "")
                    logger.info("  Unit: %s (%s)", unit_guid[:8], unit_title or "без названия")

                    time.sleep(DELAY)

                    # Parts.aspx
                    vs, vsg, ve = fetch_parts_page(unit_guid)
                    if not vs:
                        logger.warning("    Нет ViewState, пропускаем")
                        continue

                    # Шаг 3: Обход позиций (Поз № 1–20)
                    for pos_num in range(1, MAX_POSITIONS + 1):
                        time.sleep(DELAY * 0.5)

                        cb_response = callback_parts(vs, vsg, ve, unit_guid, str(pos_num))
                        if not cb_response:
                            break  # возможно, закончились позиции

                        parts_data = parse_callback_response(cb_response)
                        if not parts_data:
                            continue  # нет данных для этой позиции

                        # Шаг 4: OCR для каждой детали
                        for part in parts_data:
                            code_key = part["code_key"]
                            time.sleep(DELAY * 0.3)

                            oem = ocr_code_image(code_key)
                            if oem:
                                # Нормализация OEM
                                oem_clean = oem.replace(" ", "")
                                results.append({
                                    "category": f"{col_name} / {group_label} / {sub_label}",
                                    "group": group_label,
                                    "subgroup": sub_label,
                                    "unit_title": unit_title,
                                    "position": pos_num,
                                    "oem": oem_clean,
                                    "oem_formatted": oem,
                                    "description": part.get("description", ""),
                                    "is_alternative": part.get("is_alternative", False),
                                })
                                total_oems += 1
                                logger.info(
                                    "    Поз %s: OEM %s  %s",
                                    pos_num, oem, part.get("description", "")[:40],
                                )
                            else:
                                logger.debug("    Поз %s: код не распознан", pos_num)

                # Сохраняем прогресс (раз в 5 подгрупп для уменьшения I/O)
                processed.add(guid)
                if len(processed) % 5 == 0:
                    RESUME_FILE.write_text(json.dumps(list(processed)))

    # Финальное сохранение прогресса
    RESUME_FILE.write_text(json.dumps(list(processed)))
    # Сохраняем результат
    _save_results(output_path, results, processed, total_oems)
    return total_oems


def _save_results(
    output_path: Path,
    results: list[dict[str, Any]],
    processed: set,
    total_oems: int = 0,
) -> None:
    """Сохранить JSON-каталог."""
    total = total_oems if total_oems else sum(1 for r in results if r.get("oem"))
    catalog = {
        "modelGuid": MODEL_GUID,
        "name": "Renault Symbol / Thalia",
        "source": "http://www.elcats.ru/renault/",
        "elcats_model_url": f"{BASE_URL}/Group.aspx?Model={MODEL_GUID}",
        "parts": results,
        "statistics": {
            "total_oems": total,
            "total_subgroups_processed": len(processed),
            "total_subgroups_total": 186,
        },
    }

    output_path.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    logger.info("")
    logger.info("═" * 50)
    logger.info("Скачивание завершено!")
    logger.info("Файл: %s", output_path)
    logger.info("OEM-номеров: %d", total)
    logger.info("Обработано подгрупп: %d / 186", len(processed))
    logger.info("═" * 50)


def main():
    parser = argparse.ArgumentParser(
        description="Краулер каталога запчастей Renault с elcats.ru",
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=Path("renault_elcats_catalog.json"),
        help="Путь для сохранения JSON",
    )
    parser.add_argument("--test", action="store_true", help="Тест на 3 подгруппах")
    parser.add_argument("--resume", action="store_true", help="Продолжить прерванный запуск")
    parser.add_argument(
        "--delay", type=float, default=None,
        help="Задержка между запросами (сек)",
    )
    args = parser.parse_args()

    global DELAY
    if args.delay is not None:
        DELAY = args.delay

    # Проверка tesseract
    try:
        subprocess.run(["tesseract", "--version"], capture_output=True, timeout=5)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        logger.error("Tesseract не найден. Установи: sudo apt install tesseract-ocr tesseract-ocr-rus")
        return 1

    total = crawl_catalog(args.output, test_mode=args.test, resume=args.resume)
    return 0 if total > 0 else 0


if __name__ == "__main__":
    exit(main())
