"""Interface en ligne de commande de Signal Matin."""
from __future__ import annotations

import argparse
import datetime as dt
import sys
import webbrowser
from pathlib import Path

from .config import ROOT, load_config, setting
from .connectors.google_calendar import authorize_google
from .ereader import SCREEN_PROFILES, generer_epub, generer_pdf_liseuse
from .ereader_server import (
    DailyPublisher,
    ReaderLibrary,
    ensure_access_token,
    ensure_pairing_code,
    parse_refresh_time,
    reader_urls,
    serve_reader,
)
from .mock_data import construire_demo
from .normalizer import charger_edition, ecrire_edition, normaliser_edition
from .pdf import generer_pdf
from .pipeline import build_live
from .printer import print_pdf
from .renderer import write_html


def _date(value: str) -> dt.date:
    try:
        return dt.date.fromisoformat(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("date attendue: AAAA-MM-JJ") from error


def _paths(date: dt.date, output: str = "") -> tuple[Path, Path, Path]:
    stem = f"{date.isoformat()}-signal-matin"
    pdf = Path(output) if output else ROOT / "output" / "pdf" / f"{stem}.pdf"
    if not pdf.is_absolute():
        pdf = ROOT / pdf
    return (
        pdf,
        ROOT / "output" / "preview" / f"{stem}.html",
        ROOT / "output" / "data" / f"{stem}.json",
    )


def _ereader_paths(
    date: dt.date, output: str = "", output_format: str = "epub",
) -> tuple[Path | None, Path | None]:
    stem = f"{date.isoformat()}-signal-matin"
    directory = ROOT / "output" / "ereader"
    epub = directory / f"{stem}.epub"
    pdf = directory / f"{stem}-eink.pdf"
    if output:
        selected = Path(output)
        if not selected.is_absolute():
            selected = ROOT / selected
        if output_format == "both":
            if selected.suffix:
                raise SystemExit("Avec --format both, --output doit être un dossier.")
            epub = selected / f"{stem}.epub"
            pdf = selected / f"{stem}-eink.pdf"
        elif output_format == "epub":
            epub = selected
        else:
            pdf = selected
    return (
        epub if output_format in {"epub", "both"} else None,
        pdf if output_format in {"pdf", "both"} else None,
    )


def _edition(args, config: dict):
    if args.input:
        return charger_edition(Path(args.input), mode=args.mode)
    demo = args.demo or (not args.live and bool(config.get("demo", not config)))
    if demo:
        return normaliser_edition(construire_demo(args.date), mode=args.mode)
    now = dt.datetime.combine(args.date, dt.datetime.now().astimezone().timetz())
    return build_live(config, now=now, mode=args.mode)


def _common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--config", default="config.yaml", help="fichier YAML local")
    parser.add_argument("--input", help="edition JSON deja normalisee")
    parser.add_argument("--date", type=_date, default=dt.date.today())
    parser.add_argument("--mode", choices=("auto", "compact", "standard", "extended"), default="auto")
    parser.add_argument("--output", default="", help="chemin de sortie personnalisé")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--demo", action="store_true", help="force les donnees fictives")
    group.add_argument("--live", action="store_true", help="force les connecteurs configures")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="signal-matin")
    sub = parser.add_subparsers(dest="command", required=True)
    for name, help_text in (
        ("preview", "genere et ouvre la version HTML"),
        ("generate", "genere JSON, HTML et PDF"),
        ("data", "genere uniquement le JSON normalise"),
        ("print", "genere puis imprime explicitement le PDF"),
    ):
        command = sub.add_parser(name, help=help_text)
        _common(command)
        if name == "preview":
            command.add_argument("--no-open", action="store_true")
        if name == "print":
            command.add_argument("--printer", default="")
            command.add_argument("--duplex", action="store_true")
            command.add_argument("--confirm", action="store_true")
    ereader = sub.add_parser("ereader", help="génère une édition EPUB ou PDF e-ink")
    _common(ereader)
    ereader.add_argument(
        "--format", choices=("epub", "pdf", "both"), default="epub",
        help="format liseuse à produire",
    )
    ereader.add_argument(
        "--screen", choices=tuple(SCREEN_PROFILES), default="medium",
        help="taille du PDF e-ink; sans effet sur l'EPUB reformatable",
    )
    serve = sub.add_parser(
        "serve", help="publie l'édition liseuse sur une page privée du réseau local")
    serve.add_argument("--config", default="config.yaml", help="fichier YAML local")
    serve.add_argument("--mode", choices=("auto", "compact", "standard", "extended"), default="auto")
    group = serve.add_mutually_exclusive_group()
    group.add_argument("--demo", action="store_true", help="force les données fictives")
    group.add_argument("--live", action="store_true", help="force les connecteurs configurés")
    serve.add_argument("--host", default="127.0.0.1", help="0.0.0.0 pour autoriser le Wi-Fi local")
    serve.add_argument("--port", type=int, default=8844)
    serve.add_argument("--refresh-at", default="08:00", help="mise à jour quotidienne HH:MM")
    serve.add_argument("--format", choices=("epub", "both"), default="epub")
    serve.add_argument("--screen", choices=tuple(SCREEN_PROFILES), default="medium")
    serve.add_argument("--output-dir", default="output/ereader")
    serve.add_argument(
        "--input-dir", default="",
        help="dossier facultatif contenant AAAA-MM-JJ-signal-matin.json",
    )
    serve.add_argument(
        "--show-url-only", action="store_true",
        help="affiche le favori privé sans démarrer un second serveur",
    )
    auth = sub.add_parser("auth-google", help="connecte Google Calendar en lecture seule")
    auth.add_argument("--config", default="config.yaml")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = load_config(args.config)
    if getattr(args, "mode", None) == "auto":
        # Densité fixée dans config.yaml (paper.density), sinon choix automatique.
        args.mode = str(setting(config, "paper.density", "auto") or "auto")
    if args.command == "auth-google":
        token = authorize_google(setting(config, "calendar.google", {}) or {}, ROOT)
        print(f"Jeton OAuth enregistre localement: {token}")
        return 0
    if args.command == "serve":
        output_dir = Path(args.output_dir)
        if not output_dir.is_absolute():
            output_dir = ROOT / output_dir
        library = ReaderLibrary(output_dir)
        token = ensure_access_token(output_dir)
        pairing_code = ensure_pairing_code(output_dir)
        try:
            refresh_at = parse_refresh_time(args.refresh_at)
        except ValueError as error:
            raise SystemExit(str(error)) from error

        urls = reader_urls(args.host, args.port)
        if args.show_url_only:
            print("Adresse Signal Matin :")
            for url in urls:
                print(f"  {url}")
            print(f"Code d'association temporaire : {pairing_code}")
            return 0

        def publish(date: dt.date) -> None:
            if args.input_dir:
                input_dir = Path(args.input_dir)
                if not input_dir.is_absolute():
                    input_dir = ROOT / input_dir
                input_path = input_dir / f"{date.isoformat()}-signal-matin.json"
                if not input_path.is_file():
                    raise FileNotFoundError(
                        f"édition normalisée du jour encore absente : {input_path}")
                edition = charger_edition(input_path, mode=args.mode)
            else:
                publication_args = argparse.Namespace(
                    input=None,
                    demo=args.demo,
                    live=args.live,
                    date=date,
                    mode=args.mode,
                )
                edition = _edition(publication_args, config)
            epub_path = output_dir / f"{date.isoformat()}-signal-matin.epub"
            generer_epub(edition, epub_path)
            if args.format == "both":
                generer_pdf_liseuse(
                    edition,
                    output_dir / f"{date.isoformat()}-signal-matin-eink.pdf",
                    profile=args.screen,
                )
            _, _, data_path = _paths(date)
            ecrire_edition(edition, data_path)
            print(f"Édition liseuse actualisée : {epub_path}", flush=True)

        publisher = DailyPublisher(library, publish, refresh_at)
        publisher.start()
        print("Signal Matin est disponible sur le réseau local :", flush=True)
        for url in urls:
            print(f"  {url}", flush=True)
        print(f"Code d'association temporaire : {pairing_code}", flush=True)
        print("Associe la liseuse, puis enregistre cette adresse dans ses favoris.", flush=True)
        try:
            serve_reader(library, host=args.host, port=args.port, token=token)
        finally:
            publisher.stop()
        return 0
    if args.input and args.demo:
        raise SystemExit("Choisis --input ou --demo, pas les deux.")
    edition = _edition(args, config)
    pdf_path, html_path, data_path = _paths(args.date, args.output)
    ecrire_edition(edition, data_path)
    if args.command == "ereader":
        epub_path, eink_pdf_path = _ereader_paths(args.date, args.output, args.format)
        if epub_path:
            generer_epub(edition, epub_path)
            print(f"EPUB liseuse généré : {epub_path}")
        if eink_pdf_path:
            generer_pdf_liseuse(edition, eink_pdf_path, profile=args.screen)
            print(f"PDF e-ink généré : {eink_pdf_path}")
        print(f"JSON : {data_path}")
        return 0
    if args.command == "data":
        print(f"JSON genere: {data_path}")
        return 0
    write_html(edition, html_path)
    if args.command == "preview":
        if not args.no_open:
            webbrowser.open(html_path.resolve().as_uri())
        print(f"Preview generee: {html_path}")
        return 0
    generer_pdf(edition, pdf_path, html_path=html_path)
    if args.command == "print":
        printer = args.printer or str(setting(config, "printing.printer", "") or "")
        duplex = args.duplex or bool(setting(config, "printing.duplex", False))
        result = print_pdf(
            pdf_path, printer=printer, duplex=duplex, execute=args.confirm)
        if not result.executed:
            print(f"Impression preparee pour {result.printer}; ajoute --confirm pour l'envoyer.")
            return 2
        print(f"{result.pages} pages envoyees a {result.printer}.")
        return 0
    print(f"PDF genere: {pdf_path}")
    print(f"Preview: {html_path}")
    print(f"JSON: {data_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
