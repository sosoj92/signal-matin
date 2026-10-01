import pytest

from signal_matin import cli
from signal_matin.config import load_config, setting


def test_environment_values_are_expanded(tmp_path, monkeypatch):
    monkeypatch.setenv("SIGNAL_TEST_TOKEN", "local-value")
    path = tmp_path / "config.yaml"
    path.write_text("service:\n  token: '${SIGNAL_TEST_TOKEN}'\n", encoding="utf-8")
    config = load_config(path)
    assert setting(config, "service.token") == "local-value"



class _Stop(Exception):
    """Interrompt la commande une fois la densité choisie."""


def test_paper_density_applies_only_when_mode_is_auto(tmp_path, monkeypatch):
    path = tmp_path / "config.yaml"
    path.write_text("paper:\n  density: compact\n", encoding="utf-8")
    seen = []

    def record(args, config):
        seen.append(args.mode)
        raise _Stop

    monkeypatch.setattr(cli, "_edition", record)
    for extra in ([], ["--mode", "standard"]):
        with pytest.raises(_Stop):
            cli.main(["data", "--demo", "--config", str(path), *extra])
    assert seen == ["compact", "standard"]
