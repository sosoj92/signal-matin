"""Agenda provenant de fichiers ou d'URL ICS."""
from __future__ import annotations

import datetime as dt
import urllib.request
from pathlib import Path

from ..models import AgendaItem, DataSourceStatus, DataState


def _read(source: str, root: Path) -> bytes:
    if source.startswith(("https://", "http://")):
        request = urllib.request.Request(source, headers={"User-Agent": "Signal-Matin/1.0"})
        with urllib.request.urlopen(request, timeout=12) as response:
            return response.read(2_000_000)
    path = Path(source).expanduser()
    if not path.is_absolute():
        path = root / path
    return path.read_bytes()


def _datetime(value, timezone: dt.tzinfo) -> tuple[dt.datetime | None, bool]:
    if isinstance(value, dt.datetime):
        return (value.astimezone() if value.tzinfo else value.replace(tzinfo=timezone)), False
    if isinstance(value, dt.date):
        return dt.datetime.combine(value, dt.time.min, tzinfo=timezone), True
    return None, False


def collect_ics(
    sources: list, now: dt.datetime, root: Path,
) -> tuple[list[AgendaItem], DataSourceStatus]:
    if not sources:
        return [], DataSourceStatus(
            name="Agenda ICS", state=DataState.DISABLED, detail="Aucune source ICS configuree.",
        )
    try:
        from icalendar import Calendar
    except ImportError:
        return [], DataSourceStatus(
            name="Agenda ICS", state=DataState.UNAVAILABLE,
            detail="Installe la dependance icalendar.",
        )
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + dt.timedelta(days=1)
    events: list[AgendaItem] = []
    failures = 0
    for entry in sources:
        source = str(entry.get("source") if isinstance(entry, dict) else entry)
        label = str(entry.get("name") or entry.get("nom") or "ICS") if isinstance(entry, dict) else "ICS"
        try:
            calendar = Calendar.from_ical(_read(source, root))
            for component in calendar.walk("VEVENT"):
                start, all_day = _datetime(component.decoded("DTSTART"), now.tzinfo or dt.UTC)
                if start is None or not (day_start <= start < day_end):
                    continue
                end_raw = component.get("DTEND")
                end, _ = _datetime(end_raw.dt, now.tzinfo or dt.UTC) if end_raw else (None, False)
                events.append(AgendaItem(
                    title=str(component.get("SUMMARY") or "Sans titre"),
                    start=start, end=end, all_day=all_day,
                    location=str(component.get("LOCATION") or ""), note=label,
                ))
        except Exception:
            failures += 1
    events.sort(key=lambda item: item.start or day_start)
    return events[:24], DataSourceStatus(
        name="Agenda ICS",
        state=DataState.LIVE if events else DataState.UNAVAILABLE,
        detail=f"{len(sources) - failures}/{len(sources)} calendriers lus",
        item_count=len(events[:24]),
    )
