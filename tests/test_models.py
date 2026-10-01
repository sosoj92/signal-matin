import datetime as dt

import pytest
from pydantic import ValidationError

from signal_matin.mock_data import construire_demo
from signal_matin.models import DensityMode, MorningEdition
from signal_matin.normalizer import normaliser_edition
from signal_matin.pipeline import build_live


def test_news_requires_a_source():
    raw = construire_demo(dt.date(2026, 9, 26)).model_dump(mode="json")
    del raw["news"]["lead"]["source"]
    with pytest.raises(ValidationError):
        MorningEdition.model_validate(raw)


def test_density_can_be_forced():
    edition = construire_demo(dt.date(2026, 9, 26))
    for mode in DensityMode:
        assert normaliser_edition(edition, mode=mode).edition.density == mode


def test_every_module_can_be_absent():
    config = {
        "modules": {
            "weather": False, "calendar": False, "tasks": False,
            "news": False, "tech": False, "rss": False,
            "games": False, "tech_vocabulary": False,
            "recommendations": False,
        }
    }
    edition = build_live(
        config, now=dt.datetime(2026, 9, 26, 8, tzinfo=dt.UTC))
    assert edition.weather is None
    assert edition.agenda == []
    assert edition.news.lead is None
