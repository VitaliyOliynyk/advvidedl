"""Wiersz poleceń: cały katalog (opcjonalnie od/do wskazanego filmu) albo jeden film."""

import argparse
import logging
import os
import sys
from pathlib import Path

import requests
from dotenv import find_dotenv, load_dotenv

from advvidedl import interactive
from advvidedl.captcha import CaptchaError, DeepSeekSolver, ManualSolver
from advvidedl.client import ViderClient, new_session
from advvidedl.download import DownloadError, assign_filenames, download_video, stream_url
from advvidedl.listing import Video, parse_directory, parse_video_code, parse_video_page, url_kind
from advvidedl.selection import SelectionError, select_range

logger = logging.getLogger("advvidedl")

DESCRIPTION = """\
Pobiera filmy z vider.info. Captchę rozwiązuje model DeepSeek (klucz w zmiennej
DEEPSEEK_API_KEY albo w pliku .env), a gdy to się nie uda, prosi o wpisanie kodu.

Tryb zależy od podanego adresu:
  katalog  https://vider.info/dir/+d...  wszystkie filmy z katalogu albo zakres
                                          od --start do --end
  film     https://vider.info/vid/+f...  jeden film

Uruchomiony bez parametrów program pyta o potrzebne dane (tryb interaktywny)."""

EPILOG = """\
Przykłady:
  wszystkie filmy z katalogu, zapisywane w bieżącym katalogu:
    advvidedl https://vider.info/dir/+dse1v51
  wszystkie filmy z katalogu, zapisywane we wskazanym katalogu (zostanie utworzony):
    advvidedl https://vider.info/dir/+dse1v51 -o "D:\\Filmy\\Pokemon"
  od filmu o podanej nazwie (wystarczy fragment) do końca katalogu:
    advvidedl https://vider.info/dir/+dse1v51 --start "League 05"
  od filmu o podanym adresie do końca katalogu:
    advvidedl https://vider.info/dir/+dse1v51 --start https://vider.info/vid/+fxn8xmn
  od jednego wskazanego filmu do drugiego (włącznie):
    advvidedl https://vider.info/dir/+dse1v51 -s "League 05" -e "League 07"
  od początku katalogu do wskazanego filmu:
    advvidedl https://vider.info/dir/+dse1v51 --end "League 10"
  podgląd listy, bez pobierania:
    advvidedl https://vider.info/dir/+dse1v51 -s "League 05" -e "League 07" --dry-run
  pojedynczy film:
    advvidedl https://vider.info/vid/+fxn8m5x -o filmy
  tryb interaktywny (bez parametrów; pytania o adres, katalog docelowy i zakres):
    advvidedl"""


class _HelpFormatter(argparse.RawDescriptionHelpFormatter):
    def add_usage(self, usage, actions, groups, prefix=None):
        return super().add_usage(usage, actions, groups, "Użycie: " if prefix is None else prefix)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="advvidedl",
        description=DESCRIPTION,
        epilog=EPILOG,
        formatter_class=_HelpFormatter,
        add_help=False,
    )
    what = parser.add_argument_group("Co pobrać")
    what.add_argument(
        "url",
        nargs="?",
        metavar="URL",
        help="adres katalogu (…/dir/+d…) albo filmu (…/vid/+f…); bez niego: tryb interaktywny",
    )
    what.add_argument(
        "-s",
        "--start",
        metavar="FILM",
        help="pierwszy film do pobrania: URL albo nazwa (cała lub fragment); domyślnie pierwszy w katalogu",
    )
    what.add_argument(
        "-e",
        "--end",
        metavar="FILM",
        help="ostatni film do pobrania (włącznie): URL albo nazwa; domyślnie ostatni w katalogu",
    )
    what.add_argument("--dry-run", action="store_true", help="tylko wyświetl listę filmów, niczego nie pobieraj")

    where = parser.add_argument_group("Gdzie zapisać")
    where.add_argument(
        "-o",
        "--output",
        type=Path,
        metavar="KATALOG",
        help="katalog docelowy (domyślnie bieżący); jeśli nie istnieje, zostanie utworzony",
    )

    captcha = parser.add_argument_group("Captcha / DeepSeek")
    captcha.add_argument(
        "--ai-attempts",
        type=int,
        default=4,
        metavar="N",
        help="liczba prób rozwiązania captchy przez DeepSeek, po których program poprosi o ręczne wpisanie kodu (domyślnie 4)",
    )
    captcha.add_argument(
        "--max-captcha",
        type=int,
        default=12,
        metavar="N",
        help="maksymalna liczba prób rozwiązania captchy dla jednej strony (domyślnie 12)",
    )
    captcha.add_argument(
        "--model",
        default=os.environ.get("DEEPSEEK_MODEL", "deepseek-flash"),
        help="model DeepSeek obsługujący obrazy (domyślnie deepseek-flash albo wartość zmiennej DEEPSEEK_MODEL)",
    )

    other = parser.add_argument_group("Inne")
    other.add_argument("-h", "--help", action="help", help="wyświetl tę pomoc i zakończ")
    return parser


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    # SDK openai loguje każde zapytanie HTTP na poziomie INFO
    logging.getLogger("httpx").setLevel(logging.WARNING)
    load_dotenv(find_dotenv(usecwd=True))
    parser = _build_parser()
    args = parser.parse_args(argv)

    interactive_mode = args.url is None
    if interactive_mode and not sys.stdin.isatty():
        # bez terminala nie ma kogo pytać (np. potok albo docker run bez -it)
        parser.print_help(sys.stderr)
        return 2
    if not interactive_mode:
        kind = url_kind(args.url)
        if kind is None:
            parser.error(f"to nie jest adres katalogu ani filmu vider.info: {args.url}")
        if kind == "video" and (args.start or args.end):
            parser.error("--start i --end działają tylko z adresem katalogu")
    try:
        return _run(args, interactive_mode)
    except KeyboardInterrupt:
        logger.error("\nPrzerwano. Uruchom ponownie, aby wznowić pobieranie.")
        return 130


def _run(args: argparse.Namespace, interactive_mode: bool) -> int:
    if interactive_mode:
        args.url = interactive.ask_url()
        if url_kind(args.url) == "video" and (args.start or args.end):
            logger.error("Błąd: --start i --end działają tylko z adresem katalogu")
            return 2
    if args.output is None:
        args.output = interactive.ask_output() if interactive_mode else Path(".")

    session = new_session()
    client = ViderClient(session, _ai_solver(args), ManualSolver(_captcha_dir(args.output)), args.ai_attempts, args.max_captcha)
    try:
        html = client.get_page(args.url)
    except CaptchaError as exc:
        logger.error("Błąd: %s", exc)
        return 1
    except requests.RequestException as exc:
        logger.error("Błąd pobierania %s: %s", args.url, exc)
        return 1

    if url_kind(args.url) == "video":
        named = assign_filenames([parse_video_page(html, parse_video_code(args.url))])
    else:
        videos = parse_directory(html)
        if not videos:
            logger.error("Nie znaleziono żadnych filmów pod adresem %s", args.url)
            return 1
        logger.info("Znaleziono filmów w katalogu: %d", len(videos))
        try:
            if interactive_mode and not (args.start and args.end):
                interactive.print_videos(videos)
                first, last = interactive.ask_range(videos, args.start, args.end)
            else:
                first, last = select_range(videos, args.start, args.end)
        except SelectionError as exc:
            logger.error("Błąd: %s", exc)
            return 2
        # nazwy liczone dla całego katalogu, żeby nie zależały od wybranego zakresu
        named = assign_filenames(videos)[first : last + 1]
        if len(named) < len(videos):
            logger.info("Wybrane filmy: %d, od „%s” do „%s”", len(named), videos[first].title, videos[last].title)

    if args.dry_run:
        for video, name in named:
            print(f"{video.file_id}\t{name}\t{stream_url(video.file_id)}")
        return 0
    if interactive_mode and not interactive.confirm(f"Pobrać wybrane filmy ({len(named)}) do {args.output.resolve()}?"):
        return 0
    return _download_all(session, named, args.output)


def _ai_solver(args: argparse.Namespace) -> DeepSeekSolver | None:
    api_key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not api_key:
        logger.warning("Brak DEEPSEEK_API_KEY: captchę trzeba będzie wpisać ręcznie.")
        return None
    return DeepSeekSolver(api_key, args.model) if args.ai_attempts > 0 else None


def _captcha_dir(output: Path) -> Path:
    """Najbliższy istniejący katalog na drodze do ``output`` (w Dockerze widoczny z hosta)."""
    resolved = output.resolve()
    return next(path for path in (resolved, *resolved.parents) if path.is_dir())


def _download_all(session: requests.Session, named: list[tuple[Video, str]], output: Path) -> int:
    output.mkdir(parents=True, exist_ok=True)
    failed: list[str] = []
    for index, (video, name) in enumerate(named, start=1):
        logger.info("[%d/%d] %s", index, len(named), name)
        try:
            if not download_video(session, video, output / name):
                logger.info("  już istnieje, pomijam")
        except (requests.RequestException, DownloadError, OSError) as exc:
            logger.error("  BŁĄD: %s", exc)
            failed.append(name)

    logger.info("Gotowe. Pobrane: %d, błędy: %d. Katalog: %s", len(named) - len(failed), len(failed), output.resolve())
    for name in failed:
        logger.info("  nie pobrano: %s", name)
    return 1 if failed else 0
