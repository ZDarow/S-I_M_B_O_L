#!/usr/bin/env python3
"""
Скрипт слияния трёх OEM-каталогов в единый master-справочник.

Источники:
  1. scripts/oem_catalog.json           — ручной каталог (101 OEM)
  2. scripts/renault_elcats_catalog.json — elcats.ru (1131 деталь, 811 OEM)
  3. scripts/renault_catcar_catalog.json — catcar.info (1560 деталей, 1181 OEM)

Результат:
  scripts/renault_master_catalog.json — единый справочник с дедупликацией по OEM

Использование:
  python3 scripts/merge_oem_catalogs.py
  python3 scripts/merge_oem_catalogs.py --output master_catalog.json
"""

import json
import argparse
import logging
from pathlib import Path
from typing import Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

SCRIPTS_DIR = Path(__file__).resolve().parent

SOURCES: dict[str, Path] = {
    "manual": SCRIPTS_DIR / "oem_catalog.json",
    "elcats": SCRIPTS_DIR / "renault_elcats_catalog.json",
    "catcar": SCRIPTS_DIR / "renault_catcar_catalog.json",
}

DEFAULT_OUTPUT = SCRIPTS_DIR / "renault_master_catalog.json"


def load_catalog(path: Path, source_name: str) -> list[dict[str, Any]]:
    """Загрузить JSON-каталог, вернуть список деталей."""
    if not path.exists():
        logger.warning("Файл %s не найден, пропускаю источник '%s'", path, source_name)
        return []

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        logger.error("Ошибка парсинга %s: %s", path, e)
        return []

    # Нормализация: разные каталоги имеют разную структуру
    # - dict с ключом "parts": { "parts": [...] }
    # - dict с ключом "oems": { "oems": [...] }
    # - список с элементами, у которых есть ключ "parts": [{"parts": [...]}, ...]
    # - плоский список: [{...}, {...}]
    if isinstance(data, list):
        # Проверяем, не список ли это категорий с вложенными parts
        if data and isinstance(data[0], dict) and "parts" in data[0]:
            parts = []
            for entry in data:
                entry_parts = entry.get("parts", [])
                category = entry.get("category", entry.get("name", ""))
                for p in entry_parts:
                    p["category"] = category
                    parts.append(p)
        else:
            parts = data
    elif isinstance(data, dict):
        parts = data.get("parts", data.get("oems", []))
    else:
        logger.error("Неизвестный формат в %s", path)
        return []

    if not isinstance(parts, list):
        logger.error("Поле parts не является списком в %s", path)
        return []

    logger.info(
        "Загружено %d деталей из '%s' (%s)",
        len(parts), source_name, path.name,
    )
    return parts


def extract_oem(part: dict[str, Any]) -> str:
    """Извлечь OEM-номер из детали (поле oem или number или code)."""
    oem = part.get("oem") or part.get("number") or part.get("code") or ""
    # Очищаем от мусора
    oem = str(oem).strip().replace(" ", "").replace("-", "")
    return oem


def merge_catalogs(output_path: Path) -> dict[str, Any]:
    """Слить все каталоги в один master-справочник с дедупликацией по OEM."""
    all_parts: list[dict[str, Any]] = []
    source_stats: dict[str, int] = {}
    oem_set: set[str] = set()

    for source_name, path in SOURCES.items():
        parts = load_catalog(path, source_name)
        source_stats[source_name] = len(parts)

        for part in parts:
            oem = extract_oem(part)
            if not oem:
                continue

            # Убираем старый OEM и добавляем пометку источника
            clean_part = {
                "oem": oem,
                "name": part.get("name", part.get("description", part.get("title", ""))),
                "source_parts": [source_name],
            }

            # Категория/группа, если есть
            for key in ("category", "group", "subgroup", "grp_name", "parts_group"):
                val = part.get(key)
                if val:
                    clean_part[key] = val
                    break

            if oem in oem_set:
                # Находим существующую запись и добавляем источник
                for existing in all_parts:
                    if existing["oem"] == oem:
                        if source_name not in existing["source_parts"]:
                            existing["source_parts"].append(source_name)
                        break
            else:
                oem_set.add(oem)
                all_parts.append(clean_part)

    # Сортируем по OEM
    all_parts.sort(key=lambda p: p["oem"])

    catalog: dict[str, Any] = {
        "name": "Renault Symbol / Thalia — Master OEM Catalog",
        "version": "1.0.0",
        "description": (
            "Единый справочник OEM-номеров, собранный из трёх источников: "
            "ручной каталог, elcats.ru, catcar.info"
        ),
        "sources": {
            "manual": "Ручной сбор (101 оригинальный OEM)",
            "elcats": "elcats.ru — 1131 деталь, 811 OEM",
            "catcar": "catcar.info — 1560 деталей, 1181 OEM",
        },
        "statistics": {
            "total_unique_oems": len(all_parts),
            "total_parts_loaded": sum(source_stats.values()),
            "oems_found_in_1_source": sum(
                1 for p in all_parts if len(p["source_parts"]) == 1
            ),
            "oems_found_in_2_sources": sum(
                1 for p in all_parts if len(p["source_parts"]) == 2
            ),
            "oems_found_in_all_3_sources": sum(
                1 for p in all_parts if len(p["source_parts"]) == 3
            ),
            "per_source": source_stats,
        },
        "parts": all_parts,
    }

    output_path.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    logger.info("")
    logger.info("═" * 55)
    logger.info("СЛИЯНИЕ ЗАВЕРШЕНО")
    logger.info("Файл: %s", output_path)
    logger.info("Уникальных OEM: %d", len(all_parts))
    logger.info("  в 1 источнике: %d", catalog["statistics"]["oems_found_in_1_source"])
    logger.info("  в 2 источниках: %d", catalog["statistics"]["oems_found_in_2_sources"])
    logger.info("  во всех 3: %d", catalog["statistics"]["oems_found_in_all_3_sources"])
    logger.info("═" * 55)

    return catalog


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Слияние OEM-каталогов в единый master-справочник",
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Путь для сохранения JSON (по умолч.: %(default)s)",
    )
    args = parser.parse_args()

    merge_catalogs(args.output)
    return 0


if __name__ == "__main__":
    exit(main())
