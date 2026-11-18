import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("signal_setup", ROOT / "scripts" / "setup.py")
setup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(setup)


def test_access_denied_is_detected_in_french_and_english():
    assert setup.is_access_denied("PermissionError: [WinError 5] Accès refusé: 'C:\\x\\.venv'")
    assert setup.is_access_denied("ERROR: [WinError 5] Access is denied")
    assert not setup.is_access_denied("ERROR: No matching distribution found")


def test_onedrive_zip_and_store_python_are_flagged_on_windows():
    warnings = setup.location_warnings(
        Path(r"C:\Users\ana\OneDrive\Documents\signal-matin-main.zip\signal-matin-main"),
        r"C:\Users\ana\AppData\Local\Microsoft\WindowsApps\python.exe",
        windows=True,
    )
    joined = "\n".join(warnings)
    assert "ZIP" in joined and "OneDrive" in joined and "Microsoft Store" in joined


def test_simple_folder_has_no_warning():
    assert setup.location_warnings(Path(r"C:\Users\ana\signal-matin"), r"C:\Python312\python.exe", windows=True) == []
    assert setup.location_warnings(Path("/home/ana/OneDrive/x"), "/usr/bin/python3", windows=False) == []


def test_broken_venv_is_detected_and_removed(tmp_path):
    venv = tmp_path / ".venv"
    (venv / "Scripts").mkdir(parents=True)
    (venv / "Scripts" / "leftover.txt").write_text("x")
    assert not setup.venv_works(venv)
    setup.remove_venv(venv)
    assert not venv.exists()
