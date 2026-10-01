"""Édition liseuse reformatable (EPUB 3) et PDF e-ink à fort contraste."""
from __future__ import annotations

import datetime as dt
import html
import re
import uuid
import zipfile
from dataclasses import dataclass
from pathlib import Path

from .models import BriefSource, DigestItem, MorningEdition, NewsItem, TaskItem, TechBrief
from .pdf import _launch_browser

MONTHS = (
    "janvier", "février", "mars", "avril", "mai", "juin", "juillet",
    "août", "septembre", "octobre", "novembre", "décembre",
)
WEEKDAYS = (
    "lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche",
)
SCREEN_PROFILES = {
    "small": ("90mm", "120mm"),
    "medium": ("108mm", "144mm"),
    "large": ("120mm", "160mm"),
}


@dataclass(frozen=True)
class EreaderChapter:
    slug: str
    title: str
    body: str


def _e(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def _date_fr(value: dt.date) -> str:
    return f"{WEEKDAYS[value.weekday()]} {value.day} {MONTHS[value.month - 1]} {value.year}"


def _time(value: dt.datetime | None) -> str:
    if value is None:
        return ""
    local = value.astimezone()
    return f"{local.hour:02d} h {local.minute:02d}" if local.minute else f"{local.hour:02d} h"


def _source(item: NewsItem) -> str:
    source_name = f'<span class="source-name">{_e(item.source.name)}</span>'
    source_date = ""
    if item.source.published_at:
        source_date = (
            f'<span class="source-date">'
            f'{_e(_date_fr(item.source.published_at.astimezone().date()))}</span>'
        )
    label = source_name + source_date
    if item.source.url:
        return f'<a href="{_e(str(item.source.url))}">{label}</a>'
    return label


def _news_article(item: NewsItem, *, lead: bool = False) -> str:
    expanded = item.expanded_summary.strip()
    detail = f"<p>{_e(expanded)}</p>" if expanded and expanded != item.summary else ""
    klass = "article story lead" if lead else "article story"
    return f"""
    <div class="story-page">
      <article class="{klass}">
        <header class="story-head">
          <p class="eyebrow">{_e(item.category)}</p>
          <h2>{_e(item.title)}</h2>
          <p class="meta">{_source(item)}</p>
        </header>
        <p class="standfirst">{_e(item.summary)}</p>
        {detail}
      </article>
    </div>"""


def _news_collection(items: list[NewsItem]) -> str:
    return "".join(_news_article(item) for item in items)


def _digest(item: DigestItem) -> str:
    source = ""
    if item.source:
        label = _e(item.source.name)
        source = (
            f'<p class="meta"><a href="{_e(str(item.source.url))}">{label}</a></p>'
            if item.source.url else f'<p class="meta">{label}</p>'
        )
    return f"""
    <article class="article">
      <h2>{_e(item.title)}</h2>
      {source}
      <p>{_e(item.summary)}</p>
    </article>"""


def _tasks(title: str, items: list[TaskItem]) -> str:
    if not items:
        return ""
    rows = []
    for item in items:
        due = f" — {_e(_time(item.due))}" if item.due else ""
        context = f" <span class=\"meta\">({_e(item.context)})</span>" if item.context else ""
        rows.append(f"<li><strong>{_e(item.title)}</strong>{context}{due}</li>")
    return f"<section><h2>{_e(title)}</h2><ol>{''.join(rows)}</ol></section>"


_BRIEF_REF = re.compile(r"\[(\d{1,2}(?:\s*[,;]\s*\d{1,2})*)\]")


def _brief_text(text: str, sources: dict[int, BriefSource]) -> str:
    """Echappe le texte ; [3] devient le nom du media, cliquable sur la liseuse."""
    def media(match: re.Match) -> str:
        ids: list[int] = []
        for value in re.split(r"\s*[,;]\s*", match.group(1)):
            if int(value) in sources and int(value) not in ids:
                ids.append(int(value))
        labels = [
            f'<a href="{_e(str(sources[i].url))}">{_e(sources[i].name)}</a>'
            if sources[i].url else _e(sources[i].name)
            for i in ids
        ]
        return f'<span class="meta">({" · ".join(labels)})</span>' if labels else ""
    return _BRIEF_REF.sub(media, _e(text))


def _brief(brief: TechBrief) -> str:
    sources = {source.id: source for source in brief.sources}

    def paragraphs(text: str) -> str:
        return "".join(
            f"<p>{_brief_text(part, sources)}</p>" for part in text.split("\n") if part.strip()
        )

    def bullets(rows: list[str]) -> str:
        return "<ul>" + "".join(f"<li>{_brief_text(row, sources)}</li>" for row in rows) + "</ul>"

    parts = [f"<section><h2>{_e(brief.title)}</h2>"]
    if brief.essentials:
        rows = "".join(f"<li>{_brief_text(line, sources)}</li>" for line in brief.essentials)
        parts.append(f"<h3>L’essentiel en 5 lignes</h3><ol>{rows}</ol>")
    parts.append("</section>")
    if brief.facts:
        facts = []
        for fact in brief.facts:
            source = sources.get(fact.source_id)
            meta = ""
            if source:
                name = (f'<a href="{_e(str(source.url))}">{_e(source.name)}</a>'
                        if source.url else _e(source.name))
                date = (f" · {_e(_date_fr(source.published_at.astimezone().date()))}"
                        if source.published_at else "")
                meta = f'<p class="meta">{name}{date}</p>'
            translation = f" ({_e(fact.translation)})" if fact.translation else ""
            why = (f"<p><strong>Pourquoi c’est important.</strong> {_brief_text(fact.why, sources)}</p>"
                   if fact.why else "")
            facts.append(
                f'<article class="article"><p>{_brief_text(fact.fact, sources)}</p>'
                f"<blockquote><p>« {_e(fact.quote)} »{translation}</p></blockquote>{meta}{why}</article>"
            )
        parts.append("<section><h2>Les informations du jour</h2>" + "".join(facts) + "</section>")
    for analysis in brief.analyses:
        confidence = (f'<p class="meta">Confiance : {_e(analysis.confidence)}</p>'
                      if analysis.confidence else "")
        blocks = "".join(
            f"<h3>{label}</h3>{paragraphs(text)}"
            for label, text in (
                ("Les faits", analysis.facts),
                ("Le contexte", analysis.context),
                ("Enjeux géopolitiques", analysis.geopolitics),
                ("Enjeux économiques", analysis.economics),
                ("Qui y gagne, qui y perd", analysis.stakes),
                ("Lectures divergentes", analysis.readings),
                ("Ce qui reste incertain", analysis.uncertain),
            ) if text
        )
        parts.append(
            f'<section class="article"><h2>Analyse · {_e(analysis.subject)}</h2>{confidence}{blocks}</section>'
        )
    if brief.threads:
        rows = [
            f"{thread.text} ({'établi par les sources' if thread.established else 'interprétation'})"
            for thread in brief.threads
        ]
        parts.append(f"<section><h2>Fil rouge</h2>{bullets(rows)}</section>")
    critique = "".join(
        f"<h3>{label}</h3>{bullets(rows)}"
        for label, rows in (
            ("Questions à se poser", brief.questions),
            ("Biais et angles morts de la couverture", brief.blind_spots),
            ("À surveiller", brief.watch),
        ) if rows
    )
    if critique:
        parts.append(f"<section><h2>Pour exercer mon esprit critique</h2>{critique}</section>")
    if brief.unknowns:
        parts.append(f"<section><h2>Ce que je n’ai pas pu établir</h2>{bullets(brief.unknowns)}</section>")
    return "".join(parts)


def _chapters(edition: MorningEdition) -> list[EreaderChapter]:
    chapters: list[EreaderChapter] = []
    meta = edition.edition
    weather = ""
    if edition.weather:
        temperatures = [
            f"{round(value)}°" for value in (
                edition.weather.temperature_c,
                edition.weather.low_c,
                edition.weather.high_c,
            ) if value is not None
        ]
        weather = f"""
        <section>
          <h2>Météo · {_e(edition.weather.location)}</h2>
          <p class="weather"><strong>{' / '.join(temperatures)}</strong> {_e(edition.weather.condition)}</p>
          <p>{_e(edition.weather.summary)}</p>
          {f'<p class="aside">{_e(edition.weather.advice)}</p>' if edition.weather.advice else ''}
        </section>"""
    lead = _news_article(edition.news.lead, lead=True) if edition.news.lead else ""
    cover_body = f"""
      <div class="cover-title">
        <p class="kicker">Le quotidien personnel</p>
        <h1>{_e(meta.title)}</h1>
        <p class="subtitle">{_e(meta.subtitle)}</p>
        <p>{_e(_date_fr(meta.date))} · N° {meta.number}</p>
        <blockquote>{_e(meta.motto)}</blockquote>
      </div>
      {f'<p class="intro">{_e(edition.personal.greeting)}</p>' if edition.personal.greeting else ''}
      {weather}
      {lead}
    """
    chapters.append(EreaderChapter("une", "La une", cover_body))

    agenda = ""
    if edition.agenda:
        rows = []
        for item in edition.agenda:
            when = "Toute la journée" if item.all_day else _time(item.start)
            location = f" · {_e(item.location)}" if item.location else ""
            note = f"<small>{_e(item.note)}</small>" if item.note else ""
            rows.append(
                f"<li><time>{_e(when)}</time> <strong>{_e(item.title)}</strong>"
                f"{location}{note}</li>"
            )
        agenda = f"<section><h2>Agenda</h2><ol class=\"agenda\">{''.join(rows)}</ol></section>"
    daily = "".join((
        agenda,
        _tasks("Priorités", edition.priorities),
        _tasks("Rappels", edition.reminders),
        f'<section><h2>Note personnelle</h2><p>{_e(edition.personal.note)}</p></section>'
        if edition.personal.note else "",
        f'<section><h2>Fenêtre libre</h2><p>{_e(edition.personal.free_window)}</p></section>'
        if edition.personal.free_window else "",
    ))
    if daily:
        chapters.append(EreaderChapter("journee", "Ma journée", daily))

    news_items = edition.news.all_secondary()
    if news_items:
        chapters.append(EreaderChapter(
            "actualites", "Actualités & monde",
            _news_collection(news_items),
        ))

    if edition.tech_brief:
        chapters.append(EreaderChapter("tech", "Brief Tech & IA", _brief(edition.tech_brief)))
    else:
        tech_body = _news_collection(edition.tech_news)
        if not tech_body:
            tech_body = "".join(_digest(item) for item in edition.tech)
        if tech_body:
            chapters.append(EreaderChapter("tech", "Technologie & IA", tech_body))

    curiosity = _news_collection(edition.curiosity_news)
    watch = "".join(_digest(item) for item in edition.watch)
    newsletters = "".join(_digest(item) for item in edition.newsletter_digest)
    social = "".join(_digest(item) for item in edition.social_digest)
    communities = "".join(_digest(item) for item in edition.community_digest)
    recs = "".join(
        f'<article class="article"><p class="eyebrow">{_e(item.kind)}</p>'
        f'<h2>{_e(item.title)}</h2><p>{_e(item.reason)}</p></article>'
        for item in edition.recommendations
    )
    veille_parts = []
    for title, content in (
        ("Curiosité", curiosity), ("À surveiller", watch),
        ("Newsletters", newsletters), ("Réseaux", social),
        ("Communautés", communities), ("Recommandations", recs),
    ):
        if content:
            veille_parts.append(f"<section><h2>{_e(title)}</h2>{content}</section>")
    if veille_parts:
        chapters.append(EreaderChapter("veille", "Veille & curiosité", "".join(veille_parts)))

    learning = edition.learning
    learn_parts = []
    if learning.french_word:
        word = learning.french_word
        learn_parts.append(
            f"<section><h2>Mot français · {_e(word.word)}</h2>"
            f"<p>{_e(word.definition)}</p><p class=\"aside\">{_e(word.example)}</p></section>"
        )
    if learning.tech_word:
        word = learning.tech_word
        learn_parts.append(
            f"<section><h2>Vocabulaire tech · {_e(word.word)}</h2>"
            f"<p>{_e(word.definition)}</p><p class=\"aside\">{_e(word.example)}</p></section>"
        )
    if learning.math:
        learn_parts.append(
            f"<section><h2>Calcul mental</h2><p class=\"challenge\">{_e(learning.math.question)}</p>"
            f"<p>Indice : {_e(learning.math.hint)}</p>"
            f"<p class=\"answer\">Réponse : {_e(learning.math.answer)}</p></section>"
        )
    if edition.extras.quiz:
        quiz = edition.extras.quiz
        learn_parts.append(
            f"<section><h2>Mini quiz</h2><p>{_e(quiz.question)}</p>"
            f"<p class=\"answer\">Réponse : {_e(quiz.answer)}</p></section>"
        )
    if learning.crossword and learning.crossword.entries:
        clues = []
        answers = []
        for entry in sorted(learning.crossword.entries, key=lambda value: value.number):
            direction = "Horizontal" if entry.direction == "across" else "Vertical"
            clues.append(f"<li><strong>{entry.number}.</strong> {_e(entry.clue)} ({direction})</li>")
            answers.append(f"{entry.number}. {_e(entry.answer)}")
        learn_parts.append(
            f"<section><h2>Mots croisés</h2><ul class=\"clues\">{''.join(clues)}</ul>"
            f"<p class=\"answer\">Solutions : {' · '.join(answers)}</p></section>"
        )
    if edition.extras.quote:
        quote = edition.extras.quote
        learn_parts.append(
            f"<blockquote>{_e(quote.text)}"
            f"<cite>{_e(quote.author)}</cite></blockquote>"
        )
    if learn_parts:
        chapters.append(EreaderChapter(
            "apprentissage", "Jeux & apprentissage", "".join(learn_parts),
        ))
    return chapters


EPUB_CSS = """
body { margin: 0 4%; color: #111; background: #fff; font-family: Georgia, serif;
  line-height: 1.55; }
h1 { margin: .3em 0; font-size: 2.2em; line-height: 1; }
h2 { margin: 1.4em 0 .35em; font-size: 1.35em; line-height: 1.15; }
p { margin: .55em 0; }
a { color: inherit; text-decoration: underline; }
section, article { break-inside: avoid; }
.cover-title { margin: 14vh 0 3em; text-align: center; }
.kicker, .eyebrow, .meta { font-family: sans-serif; font-size: .72em;
  letter-spacing: .08em; text-transform: uppercase; }
.source-name, .source-date { display: block; overflow-wrap: anywhere; }
.subtitle { font-style: italic; }
.intro, .standfirst { font-size: 1.08em; }
.article { border-top: .08em solid #111; padding-top: .65em; margin-top: 1.4em; }
.lead h2 { font-size: 1.75em; }
.aside, blockquote { border-left: .2em solid #111; padding-left: .8em;
  font-style: italic; }
blockquote cite { display: block; margin-top: .6em; font-size: .75em; }
ol, ul { padding-left: 1.4em; }
li { margin: .45em 0; }
li small { display: block; }
time { display: inline-block; min-width: 4.4em; font-weight: bold; }
.weather strong, .challenge { font-size: 1.35em; }
.answer { margin-top: 1.5em; border-top: .08em solid #111; padding-top: .5em; }
.clues { list-style: none; padding-left: 0; }
""".strip()


def _xhtml(title: str, body: str, *, stylesheet: str = "stylesheet.css") -> str:
    return f"""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="fr" lang="fr">
<head>
  <meta charset="utf-8" />
  <title>{_e(title)}</title>
  <link rel="stylesheet" type="text/css" href="{_e(stylesheet)}" />
</head>
<body>{body}</body>
</html>
"""


def generer_epub(edition: MorningEdition, path: Path) -> Path:
    """Crée un EPUB 3 autonome et reformatable, compatible avec les liseuses."""
    path.parent.mkdir(parents=True, exist_ok=True)
    chapters = _chapters(edition)
    identifier = uuid.uuid5(
        uuid.NAMESPACE_URL,
        f"signal-matin:{edition.edition.date.isoformat()}:{edition.edition.title}",
    )
    modified = edition.generated_at.astimezone(dt.UTC).replace(microsecond=0)
    modified_text = modified.isoformat().replace("+00:00", "Z")
    manifest = []
    spine = []
    nav_items = []
    ncx_items = []
    chapter_files: list[tuple[str, str]] = []
    for index, chapter in enumerate(chapters, start=1):
        filename = f"{index:03d}-{chapter.slug}.xhtml"
        item_id = f"chapter-{index}"
        manifest.append(
            f'<item id="{item_id}" href="{filename}" media-type="application/xhtml+xml" />'
        )
        spine.append(f'<itemref idref="{item_id}" />')
        nav_items.append(f'<li><a href="{filename}">{_e(chapter.title)}</a></li>')
        ncx_items.append(
            f'<navPoint id="nav-{index}" playOrder="{index}"><navLabel><text>'
            f'{_e(chapter.title)}</text></navLabel><content src="{filename}" /></navPoint>'
        )
        chapter_files.append((filename, _xhtml(chapter.title, chapter.body)))

    container = """<?xml version="1.0" encoding="utf-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml" />
  </rootfiles>
</container>
"""
    nav = _xhtml(
        "Sommaire",
        '<nav xmlns:epub="http://www.idpf.org/2007/ops" epub:type="toc" id="toc">'
        f'<h1>Sommaire</h1><ol>{"".join(nav_items)}</ol></nav>',
    )
    ncx = f"""<?xml version="1.0" encoding="utf-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <head><meta name="dtb:uid" content="urn:uuid:{identifier}" /></head>
  <docTitle><text>{_e(edition.edition.title)}</text></docTitle>
  <navMap>{''.join(ncx_items)}</navMap>
</ncx>
"""
    opf = f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="book-id" xml:lang="fr">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="book-id">urn:uuid:{identifier}</dc:identifier>
    <dc:title>{_e(edition.edition.title)} — {_e(_date_fr(edition.edition.date))}</dc:title>
    <dc:language>fr</dc:language>
    <dc:creator>Signal Matin</dc:creator>
    <meta property="dcterms:modified">{modified_text}</meta>
  </metadata>
  <manifest>
    <item id="css" href="stylesheet.css" media-type="text/css" />
    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav" />
    <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml" />
    {''.join(manifest)}
  </manifest>
  <spine toc="ncx">{''.join(spine)}</spine>
</package>
"""
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        archive.writestr("META-INF/container.xml", container, compress_type=zipfile.ZIP_DEFLATED)
        archive.writestr("OEBPS/stylesheet.css", EPUB_CSS, compress_type=zipfile.ZIP_DEFLATED)
        archive.writestr("OEBPS/nav.xhtml", nav, compress_type=zipfile.ZIP_DEFLATED)
        archive.writestr("OEBPS/toc.ncx", ncx, compress_type=zipfile.ZIP_DEFLATED)
        archive.writestr("OEBPS/content.opf", opf, compress_type=zipfile.ZIP_DEFLATED)
        for filename, content in chapter_files:
            archive.writestr(f"OEBPS/{filename}", content, compress_type=zipfile.ZIP_DEFLATED)
    return path


def render_ereader_html(edition: MorningEdition, profile: str = "medium") -> str:
    if profile not in SCREEN_PROFILES:
        raise ValueError(f"Profil liseuse inconnu : {profile}")
    width, height = SCREEN_PROFILES[profile]
    chapters = _chapters(edition)
    body = "".join(
        f'<section class="chapter"><header><p class="kicker">{_e(edition.edition.title)}</p>'
        f'<h1>{_e(chapter.title)}</h1></header>{chapter.body}</section>'
        for chapter in chapters
    )
    css = EPUB_CSS + f"""
    @page {{ size: {width} {height}; margin: 8mm 7mm 9mm; }}
    html, body {{ margin: 0; padding: 0; background: #fff; color: #000; }}
    body {{ font-size: 10.8pt; line-height: 1.46; }}
    .chapter {{ break-before: page; }}
    .chapter:first-child {{ break-before: auto; }}
    .chapter > header {{ border-bottom: .45mm solid #000; margin-bottom: 4mm; }}
    .chapter > header h1 {{ font-size: 22pt; }}
    article, section {{ break-inside: auto; }}
    .story-page {{ padding-top: 6mm; break-inside: auto; display: flow-root;
      box-decoration-break: clone; -webkit-box-decoration-break: clone; }}
    .story-page > article.story {{ margin-top: 0; }}
    h1, h2 {{ break-after: auto; break-inside: auto; }}
    .chapter > header h1 {{ break-after: avoid-page; break-inside: avoid; }}
    p {{ orphans: 3; widows: 3; }}
    a {{ text-decoration: none; }}
    .answer {{ break-before: avoid; font-size: .88em; overflow-wrap: anywhere; }}
    .source-date {{ display: none; }}
    """
    return f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><title>{_e(edition.edition.title)}</title>
<style>{css}</style></head><body>{body}</body></html>"""


def generer_pdf_liseuse(
    edition: MorningEdition,
    path: Path,
    *,
    profile: str = "medium",
) -> Path:
    """Génère un PDF e-ink 3:4, plus lisible qu'un A4 réduit."""
    from playwright.sync_api import sync_playwright

    if profile not in SCREEN_PROFILES:
        raise ValueError(f"Profil liseuse inconnu : {profile}")
    width, height = SCREEN_PROFILES[profile]
    path.parent.mkdir(parents=True, exist_ok=True)
    html_text = render_ereader_html(edition, profile=profile)
    with sync_playwright() as playwright:
        browser = _launch_browser(playwright)
        try:
            page = browser.new_page(viewport={"width": 900, "height": 1200})
            page.set_content(html_text, wait_until="load")
            page.evaluate("document.fonts.ready")
            page.emulate_media(media="print")
            page.pdf(
                path=str(path), width=width, height=height,
                print_background=True, prefer_css_page_size=True,
                display_header_footer=False,
                margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
            )
        finally:
            browser.close()
    return path
