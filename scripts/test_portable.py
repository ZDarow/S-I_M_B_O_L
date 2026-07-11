#!/usr/bin/env python3
"""
Заглушка обратной совместимости — тесты перенесены в scripts/tests/.

Запуск:
    python3 -m pytest scripts/tests/ -v
    python3 -m pytest scripts/tests/test_serve.py -v
"""

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

# Импорт всех тестов для обратной совместимости (pytest обнаружит их)
from tests.test_sitemap import TestSitemap  # noqa: F401, E402
from tests.test_mermaid import (  # noqa: F401, E402
    TestMermaidCore,
    TestMermaidPreprocess,
    TestMermaidMdbookPreprocessor,
)
from tests.test_serve import TestServe, TestServeMain, TestServeHandler  # noqa: F401, E402
from tests.test_bundle import TestBundlePortable  # noqa: F401, E402
from tests.test_pdf import TestPdfA4  # noqa: F401, E402
from tests.test_crawlers import (  # noqa: F401, E402
    TestGenerateIllustrations,
    TestCatcarCrawler,
    TestElcatsCrawler,
    TestMergeOemCatalogs,
)

if __name__ == "__main__":
    import subprocess
    cmd = [sys.executable, "-m", "pytest", str(SCRIPTS_DIR / "tests"), "-v"]
    print(f"Запуск: {' '.join(cmd)}")
    sys.exit(subprocess.call(cmd))
