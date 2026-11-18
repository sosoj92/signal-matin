"""Installation guidee de Signal Matin, sans cle API obligatoire."""
from __future__ import annotations

import argparse
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VENV = ROOT / ".venv"
IS_WINDOWS = sys.platform == "win32"


class StepFailed(Exception):
    """Une etape a echoue ; le message est deja lisible par une debutante."""


def venv_python(venv: Path = VENV) -> Path:
    return venv / ("Scripts/python.exe" if IS_WINDOWS else "bin/python")


def is_access_denied(text: str) -> bool:
    lowered = text.lower()
    return any(
        marker in lowered
        for marker in ("winerror 5", "errno 13", "accès refusé", "acces refuse", "access is denied", "permission denied")
    )


def location_warnings(root: Path, python: str, windows: bool = IS_WINDOWS) -> list[str]:
    """Repere les emplacements connus pour provoquer « [WinError 5] Acces refuse »."""
    if not windows:
        return []
    path = str(root).lower()
    warnings = []
    temp = os.environ.get("TEMP", "").lower()
    if ".zip" in path or "\\appdata\\local\\temp" in path or (temp and path.startswith(temp)):
        warnings.append(
            "Le dossier semble etre ouvert directement dans le ZIP (dossier temporaire).\n"
            "    Fais un clic droit sur le ZIP > « Extraire tout... », puis relance depuis le dossier extrait."
        )
    if "onedrive" in path:
        warnings.append(
            "Le dossier est synchronise par OneDrive, qui verrouille souvent les fichiers pendant l'installation.\n"
            "    Deplace le dossier hors de OneDrive, par exemple dans C:\\Users\\<ton nom>\\signal-matin."
        )
    if "\\windowsapps\\" in python.lower():
        warnings.append(
            "Python vient du Microsoft Store, dont les droits sont limites.\n"
            "    Si l'installation echoue, installe Python depuis https://www.python.org/downloads/."
        )
    return warnings


def access_denied_help(root: Path = ROOT) -> str:
    lines = [
        "Windows a refuse l'acces a un fichier ([WinError 5] Acces refuse). Le plus souvent :",
        "  1. une autre fenetre utilise deja Signal Matin : ferme les autres terminaux et l'apercu,",
        "     et si tu as installe la liseuse, arrete la tache avec :",
        "     Stop-ScheduledTask -TaskName \"Signal Matin - liseuse\"",
        "  2. le dossier est dans OneDrive, Documents ou Bureau, proteges par Windows :",
        "     deplace-le dans C:\\Users\\<ton nom>\\signal-matin (hors OneDrive) ;",
        "  3. l'antivirus bloque Python (Securite Windows > Protection contre les ransomwares >",
        "     « Dispositif d'acces controle aux dossiers ») : autorise python.exe ou change de dossier.",
        "Il n'est PAS necessaire d'ouvrir le terminal en administrateur.",
        "Ensuite, relance simplement : python scripts/setup.py",
        "(un environnement .venv incomplet sera recree automatiquement).",
    ]
    if "onedrive" in str(root).lower():
        lines.insert(1, "  -> Ton dossier est actuellement dans OneDrive : c'est la cause la plus probable.")
    return "\n".join(lines)


def run(command: list[str], label: str) -> None:
    """Lance une commande en affichant sa sortie, et explique clairement un echec."""
    print(f"\n==> {label}", flush=True)
    tail: list[str] = []
    try:
        process = subprocess.Popen(
            command,
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except OSError as error:
        raise StepFailed(_explain(label, str(error))) from error
    assert process.stdout is not None
    for line in process.stdout:
        print(line, end="", flush=True)
        tail = (tail + [line])[-40:]
    if process.wait() != 0:
        raise StepFailed(_explain(label, "".join(tail)))


def _explain(label: str, output: str) -> str:
    message = f"L'etape « {label} » a echoue."
    if is_access_denied(output):
        return message + "\n\n" + access_denied_help()
    return message + "\nLis le message ci-dessus, puis relance python scripts/setup.py."


def check_folder_writable(root: Path = ROOT) -> None:
    try:
        with tempfile.NamedTemporaryFile(dir=root, prefix=".signal-matin-test-", delete=True):
            pass
    except OSError as error:
        raise StepFailed(
            f"Impossible d'ecrire dans le dossier {root} ({error}).\n\n" + access_denied_help(root)
        ) from error


def _force_remove(function, path, _excinfo) -> None:
    # Sous Windows, certains fichiers sont en lecture seule : on retire l'attribut puis on reessaie.
    os.chmod(path, stat.S_IWRITE)
    function(path)


def remove_venv(venv: Path = VENV) -> None:
    for attempt in range(3):
        try:
            if sys.version_info >= (3, 12):
                shutil.rmtree(venv, onexc=_force_remove)
            else:
                shutil.rmtree(venv, onerror=_force_remove)
            return
        except FileNotFoundError:
            return
        except OSError as error:
            if attempt == 2:
                raise StepFailed(
                    f"Impossible de supprimer l'ancien environnement {venv} ({error}).\n"
                    "Un programme l'utilise probablement encore.\n\n" + access_denied_help()
                ) from error
            time.sleep(2)


def venv_works(venv: Path = VENV) -> bool:
    python = venv_python(venv)
    if not python.exists():
        return False
    try:
        result = subprocess.run([str(python), "-c", "import sys"], capture_output=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0


def ensure_venv() -> None:
    if Path(sys.executable).resolve().is_relative_to(VENV.resolve()):
        # setup.py est lance avec le Python de .venv : on ne peut pas le recreer pendant qu'il tourne.
        return
    if venv_works():
        return
    if VENV.exists():
        print("\nL'environnement .venv est incomplet (installation precedente interrompue) : il va etre recree.")
        remove_venv()
    run([sys.executable, "-m", "venv", str(VENV)], "Creation de l'environnement Python")


def install(args: argparse.Namespace) -> None:
    check_folder_writable()
    ensure_venv()

    python = str(venv_python())
    # Pas de « pip install --upgrade pip » : sous Windows, pip ne peut pas toujours se remplacer
    # lui-meme (fichiers verrouilles), et la version fournie avec Python 3.11+ suffit.
    run([python, "-m", "pip", "install", "--disable-pip-version-check", "-e", "."],
        "Installation de Signal Matin et de ses dependances")
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


def _safe_console() -> None:
    # Une console Windows en cp1252 ne sait pas afficher certains caracteres (barre de progression
    # de Playwright, guillemets...) : on les remplace au lieu de faire planter l'installation.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="replace")
        except (AttributeError, ValueError):
            pass


def main() -> int:
    _safe_console()
    parser = argparse.ArgumentParser(description="Installation guidee de Signal Matin")
    parser.add_argument("--yes", action="store_true", help="ne pose aucune question")
    parser.add_argument("--skip-preview", action="store_true", help="n'ouvre pas la demo")
    args = parser.parse_args()

    if sys.version_info < (3, 11):
        raise SystemExit("Python 3.11 ou plus recent est necessaire.")

    print("Signal Matin - installation guidee")
    print("Aucune cle API et aucune imprimante ne sont necessaires pour la demo.")
    print(f"Dossier : {ROOT}")
    for warning in location_warnings(ROOT, sys.executable):
        print(f"\n[ATTENTION] {warning}")

    if not args.yes:
        answer = input("\nContinuer ? [O/n] ").strip().lower()
        if answer not in {"", "o", "oui", "y", "yes"}:
            print("Installation annulee, aucun fichier n'a ete modifie.")
            return 0

    try:
        install(args)
    except StepFailed as error:
        print(f"\n[ERREUR] {error}", file=sys.stderr)
        return 1
    except PermissionError as error:
        print(f"\n[ERREUR] {error}\n\n{access_denied_help()}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
