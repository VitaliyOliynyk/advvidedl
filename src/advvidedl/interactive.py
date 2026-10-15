"""Tryb interaktywny: pytania o parametry, których nie podano w wierszu poleceń."""

import sys
from pathlib import Path

from advvidedl.listing import Video, url_kind
from advvidedl.selection import SelectionError, check_order, find_video

START_PROMPT = "Od którego filmu zacząć? (numer, nazwa lub URL; Enter = od pierwszego): "
END_PROMPT = "Na którym filmie skończyć? (numer, nazwa lub URL; Enter = do ostatniego): "


def ask(prompt: str) -> str:
    """Zadaje pytanie. EOF (Ctrl+Z / Ctrl+D) przerywa program tak jak Ctrl+C."""
    try:
        return input(prompt).strip()
    except EOFError:
        raise KeyboardInterrupt from None


def _say(message: str) -> None:
    print(message, file=sys.stderr)


def ask_url() -> str:
    """Pyta o adres, dopóki nie dostanie adresu katalogu albo filmu."""
    while True:
        url = ask("Podaj adres katalogu albo filmu vider.info: ").strip('"')
        if url_kind(url) is not None:
            return url
        _say("To nie jest adres katalogu (https://vider.info/dir/+d…) ani filmu (https://vider.info/vid/+f…).")


def ask_output() -> Path:
    """Pyta o katalog docelowy; Enter oznacza katalog bieżący."""
    answer = ask("Katalog docelowy (Enter = bieżący): ").strip('"')
    return Path(answer) if answer else Path(".")


def print_videos(videos: list[Video]) -> None:
    """Wypisuje ponumerowaną listę filmów (numeracja od 1)."""
    width = len(str(len(videos)))
    for number, video in enumerate(videos, start=1):
        print(f"  {number:>{width}}. {video.title}")


def ask_video(videos: list[Video], prompt: str) -> int | None:
    """Indeks filmu wskazanego numerem z listy, nazwą albo URL-em; None po samym Enterze."""
    while True:
        answer = ask(prompt)
        if not answer:
            return None
        if answer.isdigit():
            number = int(answer)
            if 1 <= number <= len(videos):
                return number - 1
            _say(f"Podaj numer od 1 do {len(videos)}.")
            continue
        try:
            return find_video(videos, answer)
        except SelectionError as exc:
            _say(str(exc))


def ask_range(videos: list[Video], start: str | None = None, end: str | None = None) -> tuple[int, int]:
    """Pierwszy i ostatni film (włącznie); pyta tylko o te końce, których nie podano."""
    if start:
        first = find_video(videos, start)
    else:
        first = ask_video(videos, START_PROMPT)
        first = 0 if first is None else first
    while True:
        if end:
            last = find_video(videos, end)
        else:
            last = ask_video(videos, END_PROMPT)
            last = len(videos) - 1 if last is None else last
        try:
            check_order(videos, first, last)
            return first, last
        except SelectionError as exc:
            if end:
                raise
            _say(str(exc))


def confirm(prompt: str) -> bool:
    """Pytanie tak/nie; Enter oznacza „tak”."""
    return ask(f"{prompt} [T/n] ").casefold() not in ("n", "nie", "no")
