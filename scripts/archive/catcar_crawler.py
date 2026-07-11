#!/usr/bin/env python3
"""Краулер каталога запчастей Renault c catcar.info.

Извлекает OEM-номера, названия деталей и доп. информацию
в JSON-формат, совместимый с elcats-каталогом.

Использование:
  python3 scripts/catcar_crawler.py --output scripts/renault_catcar_catalog.json
  python3 scripts/catcar_crawler.py --test    # тест на 3 подгруппах
  python3 scripts/catcar_crawler.py --resume  # докачка
"""

import argparse
import base64
import json
import logging
import re
import tempfile
import time
import urllib.parse
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

from _crawler_common import get_session

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# ─── Константы ────────────────────────────────────────────────────
BASE_URL = "https://www.catcar.info/renault"
MODEL_NAME = "Renault Symbol / Thalia"
MODEL_ID = "1435"
DELAY = 0.3  # секунд между запросами
RESUME_FILE = Path(tempfile.gettempdir()) / "catcar_progress.json"

CATEGORIES = {
    "M": "Механические узлы",
    "C": "Кузов",
    "I": "Элементы из кожи - Электрика",
}

BASE_PARAMS: dict[str, Any] = {
    "st": "40",
    "sts": {"10": "Модель", "20": "Symbol-Thalia", "30": "LU3R"},
    "noprs": MODEL_ID,
    "brand": "Renault",
    "nopr": MODEL_ID,
    "type": "LU3R",
    "img": "",
    "grp_id": "37",
    "subGrp_id": "37A",
}

# ─── Кодирование l-параметра ─────────────────────────────────────
def encode_l(st: str, sts: dict, cat_id: str, grp_id: str = "",
             subGrp_id: str = "") -> str:
    """Собрать l-параметр для перехода на нужный уровень."""
    parts = [f"st=={st}", f"sts=={json.dumps(sts, ensure_ascii=False, separators=(',', ':'))}"]

    # Базовые параметры (берём из BASE_PARAMS или переопределяем)
    val_map = {
        "noprs": BASE_PARAMS["noprs"],
        "brand": BASE_PARAMS["brand"],
        "nopr": BASE_PARAMS["nopr"],
        "type": BASE_PARAMS["type"],
        "cat_id": cat_id,
        "img": BASE_PARAMS["img"],
    }
    for key in ("noprs", "brand", "nopr", "type", "cat_id", "img"):
        parts.append(f"{key}=={val_map[key]}")
    if grp_id:
        parts.append(f"grp_id=={grp_id}")
    if subGrp_id:
        parts.append(f"subGrp_id=={subGrp_id}")
    return base64.b64encode("||".join(parts).encode()).decode()


def decode_l(l_val: str) -> dict[str, Any]:
    """Распарсить l-параметр в словарь."""
    # URL-декодируем, т.к. в HTML href %3D может заменять =
    l_val = urllib.parse.unquote(l_val)
    try:
        raw = base64.b64decode(l_val).decode("utf-8")
    except Exception:
        return {}
    result: dict[str, Any] = {}
    for pair in raw.split("||"):
        if "==" in pair:
            k, v = pair.split("==", 1)
            result[k] = v
    if "sts" in result:
        try:
            result["sts"] = json.loads(result["sts"])
        except (json.JSONDecodeError, TypeError):
            pass
    return result


# ─── Парсинг страниц ───────────────────────────────────────────────

def parse_groups(html: str) -> list[dict[str, Any]]:
    """Извлечь группы и подгруппы из страницы категории."""
    groups = []
    soup = BeautifulSoup(html, "lxml")
    for row in soup.select("div.rowblocks.hr-bottom"):
        name_el = row.select_one(".blocks.vertical-align .blocks__title")
        group_name = name_el.get_text(strip=True) if name_el else "?"
        # Извлекаем номер группы из атрибута name
        grp_match = re.search(r'name="(\d+)"', str(row))
        grp_id = grp_match.group(1) if grp_match else ""

        subgroups = []
        for a in row.select("a.blocks__item"):
            href = a.get("href", "")
            title_el = a.select_one(".blocks__title")
            img_el = a.select_one(".blocks__img img")

            sub_name = title_el.get_text(strip=True) if title_el else ""
            sub_icon = img_el.get("src", "") if img_el else ""

            if "?l=" in href:
                l_val = href.split("?l=")[1].split("&")[0]
                params = decode_l(l_val)
                sub_id = params.get("subGrp_id", "")
                if sub_id:
                    subgroups.append({
                        "subGrp_id": sub_id,
                        "name": sub_name,
                        "icon": sub_icon,
                        "l_param": l_val,
                    })

        groups.append({
            "grp_id": grp_id,
            "name": group_name,
            "subgroups": subgroups,
        })
    return groups


def parse_parts(html: str) -> list[dict[str, Any]]:
    """Извлечь детали из страницы подгруппы.

    Парсит таблицу с колонками: Код, Номер, Замены, Название,
    Дополнительная информация.
    """
    parts = []
    soup = BeautifulSoup(html, "lxml")

    # Парсим таблицу через BeautifulSoup (каждая строка = набор td)
    for tr in soup.find_all("tr"):
        cells = tr.find_all("td")
        if len(cells) < 4:
            continue

        # Пропускаем заголовок
        header_text = tr.get_text(" ", strip=True)
        if header_text.startswith("Код") or header_text.startswith("Код Номер"):
            continue

        # Извлекаем данные
        pos = cells[0].get_text(strip=True)
        oem = cells[1].get_text(strip=True)
        replacements = cells[2].get_text(strip=True) if len(cells) > 2 else ""
        name = cells[3].get_text(strip=True) if len(cells) > 3 else ""

        additional = ""
        if len(cells) > 4:
            additional = cells[4].get_text(strip=True)

        # Валидация: OEM должен быть цифровым
        if not oem or not re.match(r"^\d{6,12}$", oem.replace(" ", "")):
            continue

        parts.append({
            "position": pos,
            "oem": oem,
            "replacements": replacements,
            "name": name,
            "additional_info": additional,
        })

    return parts


# ─── Основной краулер ──────────────────────────────────────────────

def crawl_catalog(output_path: Path, test_mode: bool = False,
                  resume: bool = False) -> int:
    """Полный обход каталога catcar.info."""
    processed: set[str] = set()
    if resume and RESUME_FILE.exists():
        try:
            processed = set(json.loads(RESUME_FILE.read_text()))
            logger.info("Возобновление: уже обработано %d подгрупп", len(processed))
        except (json.JSONDecodeError, KeyError):
            processed = set()

    results: list[dict[str, Any]] = []
    total_oems = 0
    subgroup_count = 0
    test_limit = 3 if test_mode else 999999

    for cat_id, cat_name in CATEGORIES.items():
        logger.info("Категория: %s (%s)", cat_id, cat_name)

        # Строим l-параметр для категории
        sts = {"10": "Модель", "20": "Symbol-Thalia", "30": "LU3R", "40": cat_name}
        l_val = encode_l("40", sts, cat_id)

        html = get_session().get(f"{BASE_URL}/?l={l_val}", timeout=30).text
        time.sleep(DELAY)

        groups = parse_groups(html)
        logger.info("  Найдено групп: %d", len(groups))

        for group in groups:
            grp_id = group["grp_id"]
            grp_name = group["name"]

            for sg in group["subgroups"]:
                sub_id = sg["subGrp_id"]
                sub_name = sg["name"]
                subgroup_count += 1

                key = f"{cat_id}/{grp_id}/{sub_id}"
                if key in processed:
                    logger.debug("  [%d] %s — пропущено", subgroup_count, sub_name[:50])
                    continue

                if subgroup_count > test_limit:
                    logger.info("Достигнут лимит, завершаем")
                    _save_results(output_path, results, processed, total_oems)
                    return total_oems

                logger.info(
                    "  [%d] %s / %s → %s",
                    subgroup_count, cat_name[:12], grp_name[:20], sub_name[:40],
                )

                # Используем l_param из подгруппы (уже готовый)
                sg_l = sg["l_param"]
                try:
                    html = get_session().get(f"{BASE_URL}/?l={sg_l}", timeout=30).text
                except requests.RequestException as exc:
                    logger.warning("    Ошибка: %s", exc)
                    continue

                time.sleep(DELAY)

                parts = parse_parts(html)
                if not parts:
                    logger.debug("    Деталей не найдено")
                    # Отмечаем как обработанную, чтобы не перезапрашивать
                    processed.add(key)
                    if len(processed) % 5 == 0:
                        RESUME_FILE.write_text(json.dumps(list(processed)))
                    continue

                for part in parts:
                    results.append({
                        "source": "catcar.info",
                        "category": f"{cat_name} / {grp_name} / {sub_name}",
                        "group": grp_name,
                        "subgroup": sub_name,
                        "subGrp_id": sub_id,
                        "grp_id": grp_id,
                        "cat_id": cat_id,
                        "position": part["position"],
                        "oem": part["oem"],
                        "name": part["name"],
                        "replacements": part["replacements"],
                        "additional_info": part["additional_info"],
                    })
                    total_oems += 1
                    logger.info(
                        "    Поз %s: OEM %s  %s",
                        part["position"], part["oem"], part["name"][:50],
                    )

                # Сохраняем прогресс (раз в 5 подгрупп для уменьшения I/O)
                processed.add(key)
                if len(processed) % 5 == 0:
                    RESUME_FILE.write_text(json.dumps(list(processed)))

    # Финальное сохранение прогресса
    RESUME_FILE.write_text(json.dumps(list(processed)))
    _save_results(output_path, results, processed, total_oems)
    return total_oems


def _save_results(output_path: Path, results: list[dict[str, Any]],
                  processed: set, total_oems: int = 0) -> None:
    """Сохранить JSON-каталог."""
    catalog = {
        "source": "https://www.catcar.info/renault/",
        "model": MODEL_NAME,
        "model_id": MODEL_ID,
        "model_url": BASE_URL,
        "parts": results,
        "statistics": {
            "total_oems": total_oems or len(results),
            "total_subgroups_processed": len(processed),
        },
    }
    output_path.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    logger.info("")
    logger.info("=" * 50)
    logger.info("Скачивание завершено!")
    logger.info("Файл: %s", output_path)
    logger.info("OEM-номеров: %d", total_oems or len(results))
    logger.info("Обработано подгрупп: %d", len(processed))
    logger.info("=" * 50)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Краулер каталога запчастей Renault с catcar.info",
    )
    parser.add_argument(
        "--output", "-o", type=Path,
        default=Path("scripts/renault_catcar_catalog.json"),
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

    crawl_catalog(args.output, test_mode=args.test, resume=args.resume)
    return 0


if __name__ == "__main__":
    exit(main())
