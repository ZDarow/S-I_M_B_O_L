#!/usr/bin/env python3
"""
Общие функции для краулеров каталогов запчастей.

Содержит:
  - get_session() — HTTP-сессия с единым User-Agent
  - save_json()   — сохранение JSON с едиными параметрами
  - CrawlerConfig — dataclass конфигурации краулера
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests

logger = logging.getLogger(__name__)

# ─── HTTP-сессия (ленивая, thread-safe через глобал) ─────────────
_session: requests.Session | None = None


def get_session() -> requests.Session:
    """Создать (или вернуть существующую) HTTP-сессию с единым User-Agent."""
    global _session
    if _session is None:
        _session = requests.Session()
        _session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
        })
    return _session


# ─── Сохранение JSON ─────────────────────────────────────────────

def save_json(output_path: Path, data: Any, *, indent: int = 2) -> None:
    """Сохранить словарь/список в JSON-файл с едиными параметрами."""
    output_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=indent),
        encoding="utf-8",
    )


# ─── Конфигурация краулера ───────────────────────────────────────

@dataclass
class CrawlerConfig:
    """Конфигурация для запуска краулера (замена модульным глобалам)."""
    delay: float = 0.3
    test_mode: bool = False
    resume: bool = False
    output: Path = Path("catalog.json")
