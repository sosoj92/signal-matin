"""Installation guidee de Signal Matin, sans cle API obligatoire."""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENV = ROOT / ".venv"


def venv_python() -> Path:
    return VENV / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")


def run(command: list[str], label: str) -> None:
    print(f"\n==> {label}")
    subprocess.run(command, cwd=ROOT, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Installation guidee de Signal Matin")
    parser.add_argument("--yes", action="store_true", help="ne pose aucune question")
    parser.add_argument("--skip-preview", action="store_true", help="n'ouvre pas la demo")
    args = parser.parse_args()

    if sys.version_info < (3, 11):
        raise SystemExit("Python 3.11 ou plus recent est necessaire.")

    print("Signal Matin - installation guidee")
    print("Aucune cle API et aucune imprimante ne sont necessaires pour la demo.")
    if not args.yes:
        answer = input("Continuer ? [O/n] ").strip().lower()
        if answer not in {"", "o", "oui", "y", "yes"}:
            print("Installation annulee, aucun fichier n'a ete modifie.")
            return 0

    if not venv_python().exists():
        run([sys.executable, "-m", "venv", str(VENV)], "Creation de l'environnement Python")

    python = str(venv_python())
    run([python, "-m", "pip", "install", "--upgrade", "pip"], "Mise a jour de pip")
    run([python, "-m", "pip", "install", "-e", "."], "Installation de Signal Matin et de ses dependances")
    run([python, "-m", "playwright", "install", "chromium"], "Installation du navigateur PDF")

    config = ROOT / "config.yaml"
    if not config.exists():
        shutil.copyfile(ROOT / "config.example.yaml", config)
        print("\nConfiguration de demonstration creee : config.yaml")
    else:
        print("\nConfiguration existante conservee : config.yaml")

    run([python, "scripts/doctor.py"], "Verification de l'installation")
    if not args.skip_preview:
        run([python, "main.py", "--preview", "--demo"], "Ouverture du journal de demonstration")

    print("\nInstallation terminee.")
    print(f"Pour rouvrir la demo : {python} main.py --preview --demo")
    print("Pour obtenir un PDF : remplace --preview par --generate.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
