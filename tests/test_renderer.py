import datetime as dt
from pathlib import Path

from pypdf import PdfReader

from signal_matin.mock_data import construire_demo
from signal_matin.models import DensityMode
from signal_matin.normalizer import normaliser_edition
from signal_matin.pdf import generer_pdf, inspecter_html
from signal_matin.renderer import _truncate, render_html


EXPECTED_PAGES = {
    DensityMode.COMPACT: 4,
    DensityMode.STANDARD: 7,
    DensityMode.EXTENDED: 7,
}


def test_html_has_expected_pages_and_sections():
    demo = construire_demo(dt.date(2026, 9, 26))
    for mode, count in EXPECTED_PAGES.items():
        edition = normaliser_edition(demo, mode=mode)
        html = render_html(edition)
        assert html.count('class="sheet ') == count
        assert "Signal Matin" in html
        assert "En bref, en detail" in html


def test_no_major_overflow():
    demo = construire_demo(dt.date(2026, 9, 26))
    for mode, count in EXPECTED_PAGES.items():
        edition = normaliser_edition(demo, mode=mode)
        layout = inspecter_html(render_html(edition))
        assert len(layout) == count
        assert not [page for page in layout if page["overflow"]]


def test_pdf_is_a4(tmp_path):
    edition = normaliser_edition(
        construire_demo(dt.date(2026, 9, 26)), mode="standard")
    path = generer_pdf(edition, tmp_path / "signal-matin.pdf")
    reader = PdfReader(str(path))
    assert len(reader.pages) == EXPECTED_PAGES[DensityMode.STANDARD]
    for page in reader.pages:
        assert abs(float(page.mediabox.width) - 595.28) < 1.0
        assert abs(float(page.mediabox.height) - 841.89) < 1.0


def test_tech_pagination_depends_on_text_volume():
    edition = normaliser_edition(
        construire_demo(dt.date(2026, 9, 26)), mode="standard")
    assert len(edition.tech_news) == 5
    assert "tech-continuation-page" not in render_html(edition)

    long_items = [
        item.model_copy(update={"expanded_summary": "Texte developpe. " * 70})
        for item in edition.tech_news
    ]
    html = render_html(edition.model_copy(update={"tech_news": long_items}))
    assert "Technologie &amp; IA - suite" in html
    assert "tech-continuation-page" in html


def test_extra_news_tech_and_curiosity_create_pages_without_omission():
    edition = normaliser_edition(
        construire_demo(dt.date(2026, 9, 26)), mode="standard")
    source_item = edition.news.all_secondary()[0]
    news_items = [
        source_item.model_copy(update={"title": f"Sujet actualite unique {index}"})
        for index in range(20)
    ]
    tech_items = [
        edition.tech_news[index % len(edition.tech_news)].model_copy(
            update={"title": f"Sujet technologie unique {index}"}
        )
        for index in range(9)
    ]
    curiosity_items = [
        edition.curiosity_news[index % len(edition.curiosity_news)].model_copy(
            update={"title": f"Sujet curiosite unique {index}"}
        )
        for index in range(8)
    ]
    edition = edition.model_copy(update={
        "news": edition.news.model_copy(update={
            "world": news_items[:12],
            "france": news_items[12:],
            "economy": [], "society": [], "science": [], "culture": [],
        }),
        "tech_news": tech_items,
        "curiosity_news": curiosity_items,
    })
    html = render_html(edition)
    assert html.count('class="sheet ') == 10
    for item in [*news_items, *tech_items, *curiosity_items]:
        assert item.title in html
    assert "tech-continuation is-four" in html
    assert "curiosity-continuation is-four" in html


def test_large_daily_variation_creates_balanced_continuation_pages():
    edition = normaliser_edition(
        construire_demo(dt.date(2026, 9, 26)), mode="extended")
    css = (
        (Path(__file__).resolve().parents[1] / "web" / "signal_matin.css")
        .read_text(encoding="utf-8")
        + """
        .page-news .news-opening { min-height: 190mm; }
        .page-news .news-followups { min-height: 190mm; columns: 1; }
        .page-news .news-followups .news-card { min-height: 90mm; padding-bottom: 8mm; }
        .page-news .news-followups .news-card p { font-size: 13pt; line-height: 1.65; }
        """
    )
    layout = inspecter_html(render_html(edition, css=css))
    assert len(layout) > EXPECTED_PAGES[DensityMode.EXTENDED]
    assert not [page for page in layout if page["overflow"]]
    adaptive = [page for page in layout if page["adaptive"]]
    assert adaptive
    assert all(page["used_ratio"] >= 0.52 or page["sparse"] for page in adaptive)


def test_delayed_print_reuses_real_task_action():
    script = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "programmer_impression_signal_matin.ps1"
    ).read_text(encoding="utf-8")
    assert "$SourceAction.Execute" in script
    assert "$SourceAction.Arguments" in script
    assert "Start-ScheduledTask -TaskName $TacheSource" not in script


def test_truncate_prefers_a_sentence_end():
    text = "Première phrase assez longue pour compter. Deuxième phrase qui dépasse la limite."
    assert _truncate(text, 60) == "Première phrase assez longue pour compter."
    # Pas de fin de phrase utile : coupe au mot, avec points de suspension.
    assert _truncate("Un. " + "mot " * 30, 40).endswith("...")
    assert _truncate("Court.", 60) == "Court."
