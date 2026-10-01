"""Orchestration: connecteurs -> edition normalisee."""
from __future__ import annotations

import datetime as dt
from pathlib import Path

from .config import ROOT, setting
from .connectors import (
    collect_google_calendar,
    collect_ics,
    collect_rss,
    collect_tasks,
    collect_weather,
)
from .daily_learning import construire_apprentissage_du_jour
from .models import (
    DataSourceStatus,
    DataState,
    DigestItem,
    EditionMeta,
    Extras,
    Importance,
    LearningPage,
    MorningEdition,
    NewsBundle,
    NewsItem,
    PersonalBlock,
    QuoteBlock,
    Recommendation,
    SourceRef,
)
from .normalizer import normaliser_edition


def _enabled(config: dict, name: str, default: bool = True) -> bool:
    return bool(setting(config, f"modules.{name}", default))


def _disabled(name: str) -> DataSourceStatus:
    return DataSourceStatus(name=name, state=DataState.DISABLED, detail="Module desactive.")


def _bundle(items: list[NewsItem]) -> NewsBundle:
    lead = items[0].model_copy(update={"importance": Importance.HIGH}) if items else None
    groups = {key: [] for key in ("world", "france", "economy", "society", "science", "culture")}
    aliases = {
        "monde": "world", "international": "world", "france": "france",
        "politique": "france", "economie": "economy", "économie": "economy",
        "societe": "society", "société": "society", "science": "science",
        "sciences": "science", "culture": "culture",
    }
    for item in items[1:]:
        key = aliases.get(item.category.casefold(), "society")
        groups[key].append(item)
    return NewsBundle(lead=lead, **groups)


def _recommendations(values: list) -> list[Recommendation]:
    result: list[Recommendation] = []
    for value in values or []:
        if isinstance(value, str):
            result.append(Recommendation(title=value))
        elif isinstance(value, dict) and value.get("title"):
            source = None
            if value.get("source"):
                source = SourceRef(name=str(value.get("source")), url=value.get("url"))
            result.append(Recommendation(
                title=str(value["title"]), kind=str(value.get("kind") or "A decouvrir"),
                reason=str(value.get("reason") or ""), source=source,
            ))
    return result


def build_live(
    config: dict, *, now: dt.datetime | None = None, mode: str = "auto",
    root: Path = ROOT,
) -> MorningEdition:
    now = now or dt.datetime.now().astimezone()
    statuses: list[DataSourceStatus] = []

    if _enabled(config, "weather"):
        weather, status = collect_weather(setting(config, "weather", {}) or {})
    else:
        weather, status = None, _disabled("Meteo")
    statuses.append(status)

    agenda = []
    if _enabled(config, "calendar"):
        ics_events, ics_status = collect_ics(
            setting(config, "calendar.ics", []) or [], now, root)
        statuses.append(ics_status)
        agenda.extend(ics_events)
        google_config = setting(config, "calendar.google", {}) or {}
        if bool(google_config.get("enabled", False)):
            google_events, google_status = collect_google_calendar(google_config, now, root)
            statuses.append(google_status)
            agenda.extend(google_events)
    else:
        statuses.append(_disabled("Agenda"))
    agenda.sort(key=lambda item: item.start or now)

    if _enabled(config, "tasks"):
        priorities, reminders, task_status = collect_tasks(setting(config, "tasks", {}) or {})
    else:
        priorities, reminders, task_status = [], [], _disabled("Taches")
    statuses.append(task_status)

    if _enabled(config, "news") and _enabled(config, "rss"):
        news_items, news_status = collect_rss(
            setting(config, "news.feeds", []) or [], now,
            limit=int(setting(config, "news.limit", 12) or 12),
            max_age_hours=int(setting(config, "news.max_age_hours", 72) or 72),
            status_name="Actualites",
        )
    else:
        news_items, news_status = [], _disabled("Actualites")
    statuses.append(news_status)

    if _enabled(config, "tech") and _enabled(config, "rss"):
        tech_news, tech_status = collect_rss(
            setting(config, "tech.feeds", []) or [], now,
            limit=int(setting(config, "tech.limit", 6) or 6),
            max_age_hours=int(setting(config, "tech.max_age_hours", 96) or 96),
            status_name="Technologie & IA",
        )
    else:
        tech_news, tech_status = [], _disabled("Technologie & IA")
    statuses.append(tech_status)

    tech_digest = [DigestItem(
        title=item.title, summary=item.summary, source=item.source,
        importance=item.importance,
    ) for item in tech_news]
    curiosities = [
        item for item in news_items
        if item.category.casefold() in {"science", "sciences", "culture"}
    ][:4]
    recommendations = (
        _recommendations(setting(config, "recommendations", []) or [])
        if _enabled(config, "recommendations") else []
    )
    quote_text = str(setting(config, "personal.quote.text", "") or "").strip()
    quote = QuoteBlock(
        text=quote_text,
        author=str(setting(config, "personal.quote.author", "") or ""),
    ) if quote_text else None

    date = now.date()
    edition = MorningEdition(
        generated_at=now,
        demo=False,
        edition=EditionMeta(
            date=date,
            number=max(1, (date - dt.date(2026, 1, 1)).days + 1),
            title=str(setting(config, "paper.title", "Signal Matin") or "Signal Matin"),
            subtitle=str(setting(config, "paper.subtitle", "Le journal anti-scroll") or ""),
            motto=str(setting(config, "paper.motto", "Voir clair avant de voir l'ecran.") or ""),
        ),
        sources=statuses,
        weather=weather,
        agenda=agenda[:24], priorities=priorities[:12], reminders=reminders[:16],
        news=_bundle(news_items),
        tech=tech_digest, tech_news=tech_news,
        curiosity_news=curiosities,
        recommendations=recommendations,
        personal=PersonalBlock(
            greeting=str(setting(config, "personal.greeting", "Bonjour.") or "Bonjour."),
            note=str(setting(config, "personal.note", "") or ""),
            free_window=str(setting(config, "personal.free_window", "") or ""),
        ),
        extras=Extras(quote=quote),
        learning=(construire_apprentissage_du_jour(date)
                  if _enabled(config, "games") or _enabled(config, "tech_vocabulary")
                  else LearningPage()),
    )
    return normaliser_edition(edition, mode=mode)
