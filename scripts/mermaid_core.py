#!/usr/bin/env python3
"""
Общий модуль для работы с Mermaid-диаграммами через mmdc.

Содержит:
  - find_mmdc()      — поиск mmdc в PATH и node_modules
  - render_svg()     — рендер одного mermaid-блока в SVG
  - MERMAID_RE       — регулярное выражение для поиска ```mermaid блоков
"""
import hashlib
import logging
import os
import re
import subprocess
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

MERMAID_RE = re.compile(r'```mermaid\s*\n(.*?)```', re.DOTALL)
MIN_SVG_SIZE = 50
MMDC_TIMEOUT = 30
MAX_RETRIES = 3


def find_mmdc() -> str | None:
    """Найти исполняемый файл mmdc в node_modules или PATH."""
    candidates = [
        Path("node_modules/.bin/mmdc"),
        Path("../node_modules/.bin/mmdc"),
    ]
    for c in candidates:
        if c.is_file():
            return str(c.resolve())
    for p in os.environ.get("PATH", "").split(os.pathsep):
        mmdc = Path(p) / "mmdc"
        if mmdc.is_file():
            return str(mmdc)
    return None


def render_svg(mermaid_source: str, output: Path) -> bool:
    """
    Рендерит mermaid-диаграмму в SVG через mmdc с повторными попытками.

    Args:
        mermaid_source: Исходный код диаграммы (Mermaid DSL)
        output: Путь к выходному SVG файлу

    Returns:
        True если рендер успешен, иначе False
    """
    mmdc = find_mmdc()
    if not mmdc:
        logger.error("mmdc не найден. Установите: npm install @mermaid-js/mermaid-cli")
        return False

    for attempt in range(1, MAX_RETRIES + 1):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".mmd",
                                         delete=False, encoding="utf-8") as tmp:
            tmp.write(mermaid_source)
            tmp_path = tmp.name

        try:
            r = subprocess.run(
                [mmdc, "-i", tmp_path, "-o", str(output),
                 "-b", "transparent", "-w", "1200"],
                capture_output=True, text=True, timeout=MMDC_TIMEOUT,
            )
            if r.returncode != 0:
                logger.warning(
                    "Попытка %d/%d: mmdc вернул код %d: %s",
                    attempt, MAX_RETRIES, r.returncode, r.stderr[:200],
                )
                if attempt < MAX_RETRIES:
                    continue
                return False
            ok = output.exists() and output.stat().st_size >= MIN_SVG_SIZE
            if not ok and attempt < MAX_RETRIES:
                logger.warning("Попытка %d/%d: mmdc создал некорректный SVG", attempt, MAX_RETRIES)
                continue
            return ok
        except subprocess.TimeoutExpired:
            logger.warning("Попытка %d/%d: mmdc timeout (%ds)", attempt, MAX_RETRIES, MMDC_TIMEOUT)
            if attempt >= MAX_RETRIES:
                return False
        except OSError as e:
            logger.warning("Попытка %d/%d: Ошибка mmdc: %s", attempt, MAX_RETRIES, e)
            if attempt >= MAX_RETRIES:
                return False
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    return False


def hash_mermaid(source: str) -> str:
    """SHA256 хеш mermaid-источника (первые 16 символов)."""
    return hashlib.sha256(source.encode()).hexdigest()[:16]
