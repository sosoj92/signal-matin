"""Diagnostic local lisible par une personne non technique."""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE_MODULES = ("yaml", "pydantic", "playwright", "pypdf", "icalendar")


def line(kind: str, message: str) -> None:
    print(f"[{kind}] {message}")


def main() -> int:
    failures = 0
    if sys.version_info >= (3, 11):
        line("OK", f"Python {sys.version_info.major}.{sys.version_info.minor}")
    else:
        line("ERREUR", "Python 3.11 ou plus recent est necessaire")
        failures += 1

    missing = [name for name in CORE_MODULES if importlib.util.find_spec(name) is None]
    if missing:
        line("ERREUR", "Dependances absentes : " + ", ".join(missing))
        failures += 1
    else:
        line("OK", "Dependances Python installees")

    browser_check = (
        "from playwright.sync_api import sync_playwright; "
        "p=sync_playwright().start(); b=p.chromium.launch(headless=True); "
        "b.close(); p.stop()"
    )
    browser = subprocess.run(
        [sys.executable, "-c", browser_check],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if browser.returncode == 0:
        line("OK", "Chromium est disponible pour creer les PDF")
    else:
        line("ERREUR", "Chromium manque : lance python -m playwright install chromium")
        failures += 1

    if (ROOT / "config.yaml").exists():
        line("OK", "config.yaml trouve")
    else:
        line("INFO", "config.yaml absent : le mode demo fonctionne quand meme")

    if failures:
        line("AIDE", "Relance python scripts/setup.py pour reparer l'installation")
        return 1
    line("OK", "Signal Matin est pret")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
