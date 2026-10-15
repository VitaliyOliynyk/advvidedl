"""Wiersz poleceń: ``advvidedl <url_katalogu> [-o KATALOG]``."""

import argparse
import logging
import os
import re
import sys
import tempfile
from pathlib import Path

import requests
from dotenv import find_dotenv, load_dotenv

from advvidedl.captcha import CaptchaError, DeepSeekSolver, ManualSolver
from advvidedl.client import ViderClient, new_session
from advvidedl.download import DownloadError, assign_filenames, download_video, stream_url
from advvidedl.listing import parse_directory

logger = logging.getLogger("advvidedl")

_DIR_URL_RE = re.compile(r"^https?://(www\.)?vider\.(info|pl)/dir/", re.IGNORECASE)


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="advvidedl",
        description="Pobiera wszystkie filmy z katalogu vider.info. Captchę rozwiązuje model DeepSeek.",
    )
    parser.add_argument("url", help="adres katalogu, np. https://vider.info/dir/+dse1v51")
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("."),
        help="katalog docelowy (domyślnie bieżący); jeśli nie istnieje, zostanie utworzony",
    )
    parser.add_argument("--dry-run", action="store_true", help="tylko wypisz listę filmów, nic nie pobieraj")
    parser.add_argument(
        "--ai-attempts",
        type=int,
        default=4,
        help="ile razy captchę rozwiązuje DeepSeek, zanim program poprosi o wpisanie kodu (domyślnie 4)",
    )
    parser.add_argument(
        "--max-captcha",
        type=int,
        default=12,
        help="maksymalna liczba podejść do captchy na jedną stronę (domyślnie 12)",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("DEEPSEEK_MODEL", "deepseek-flash"),
        help="model DeepSeek z obsługą obrazów (domyślnie deepseek-flash albo $DEEPSEEK_MODEL)",
    )
    args = parser.parse_args(argv)
    if not _DIR_URL_RE.match(args.url):
        parser.error(f"to nie wygląda na adres katalogu vider.info: {args.url}")
    return args


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    load_dotenv(find_dotenv(usecwd=True))
    args = _parse_args(argv)
    try:
        return _run(args)
    except KeyboardInterrupt:
        logger.error("\nPrzerwano. Uruchom ponownie, aby wznowić pobieranie.")
        return 130


def _run(args: argparse.Namespace) -> int:
    api_key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    ai_solver = None
    if api_key and args.ai_attempts > 0:
        ai_solver = DeepSeekSolver(api_key, args.model)
    elif not api_key:
        logger.warning("Brak DEEPSEEK_API_KEY: captchę trzeba będzie wpisać ręcznie.")

    if not args.dry_run:
        args.output.mkdir(parents=True, exist_ok=True)
    captcha_dir = args.output if args.output.is_dir() else Path(tempfile.gettempdir())

    session = new_session()
    client = ViderClient(session, ai_solver, ManualSolver(captcha_dir), args.ai_attempts, args.max_captcha)
    try:
        html = client.get_page(args.url)
    except CaptchaError as exc:
        logger.error("Błąd: %s", exc)
        return 1
    except requests.RequestException as exc:
        logger.error("Błąd pobierania %s: %s", args.url, exc)
        return 1

    videos = parse_directory(html)
    if not videos:
        logger.error("Nie znaleziono żadnych filmów na %s", args.url)
        return 1
    logger.info("Znaleziono filmów: %d", len(videos))
    named = assign_filenames(videos)

    if args.dry_run:
        for video, name in named:
            print(f"{video.file_id}\t{name}\t{stream_url(video.file_id)}")
        return 0

    failed: list[str] = []
    for index, (video, name) in enumerate(named, start=1):
        logger.info("[%d/%d] %s", index, len(named), name)
        try:
            if not download_video(session, video, args.output / name):
                logger.info("  już istnieje, pomijam")
        except (requests.RequestException, DownloadError, OSError) as exc:
            logger.error("  BŁĄD: %s", exc)
            failed.append(name)

    logger.info("Gotowe: %d OK, %d błędów. Katalog: %s", len(named) - len(failed), len(failed), args.output.resolve())
    for name in failed:
        logger.info("  nie pobrano: %s", name)
    return 1 if failed else 0
