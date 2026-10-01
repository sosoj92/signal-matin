from signal_matin import cli
from signal_matin.config import load_config, setting


def test_environment_values_are_expanded(tmp_path, monkeypatch):
    monkeypatch.setenv("SIGNAL_TEST_TOKEN", "local-value")
    path = tmp_path / "config.yaml"
    path.write_text("service:\n  token: '${SIGNAL_TEST_TOKEN}'\n", encoding="utf-8")
    config = load_config(path)
    assert setting(config, "service.token") == "local-value"


def test_demo_edition_uses_configured_paper_identity(tmp_path):
    path = tmp_path / "config.yaml"
    path.write_text("paper:\n  title: Le Petit Matin\n  motto: Une devise fictive.\n",
                    encoding="utf-8")
    args = cli.build_parser().parse_args(
        ["data", "--demo", "--date", "2026-09-29", "--config", str(path)])
    edition = cli._edition(args, load_config(args.config)).edition
    assert (edition.title, edition.motto) == ("Le Petit Matin", "Une devise fictive.")
    assert edition.subtitle == "Le journal anti-scroll"
