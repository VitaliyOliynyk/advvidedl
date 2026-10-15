"""Wybór zakresu filmów z katalogu: od filmu startowego do końcowego."""

from advvidedl.listing import Video, parse_video_code

_MAX_LISTED = 10


class SelectionError(ValueError):
    """Nie da się jednoznacznie wskazać filmu albo zakresu."""


def find_video(videos: list[Video], query: str) -> int:
    """Indeks filmu wskazanego adresem albo nazwą.

    Nazwa może być pełnym tytułem albo jego fragmentem (wielkość liter nie ma znaczenia).
    Pełny tytuł wygrywa z fragmentem; fragment pasujący do kilku filmów to błąd.
    """
    query = query.strip()
    code = parse_video_code(query)
    if code is not None:
        for index, video in enumerate(videos):
            if video.code == code:
                return index
        raise SelectionError(f"film {query} nie należy do tego katalogu")

    needle = query.casefold()
    if needle.endswith(".mp4"):
        needle = needle[:-4]
    if not needle:
        raise SelectionError("pusta nazwa filmu")
    exact = [index for index, video in enumerate(videos) if video.title.casefold() == needle]
    matches = exact or [index for index, video in enumerate(videos) if needle in video.title.casefold()]
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise SelectionError(f"nie znaleziono filmu „{query}”")
    listed = "\n".join(f"  - {videos[index].title}" for index in matches[:_MAX_LISTED])
    if len(matches) > _MAX_LISTED:
        listed += f"\n  … i {len(matches) - _MAX_LISTED} więcej"
    raise SelectionError(
        f"„{query}” pasuje do {len(matches)} filmów:\n{listed}\nPodaj dokładniejszą nazwę albo URL filmu."
    )


def select_range(videos: list[Video], start: str | None, end: str | None) -> tuple[int, int]:
    """Indeksy pierwszego i ostatniego filmu (włącznie).

    Bez ``start`` zaczynamy od pierwszego filmu, bez ``end`` kończymy na ostatnim.
    """
    if not videos:
        raise SelectionError("katalog jest pusty")
    first = find_video(videos, start) if start else 0
    last = find_video(videos, end) if end else len(videos) - 1
    check_order(videos, first, last)
    return first, last


def check_order(videos: list[Video], first: int, last: int) -> None:
    if first > last:
        raise SelectionError(
            f"film końcowy „{videos[last].title}” jest w katalogu przed startowym „{videos[first].title}”"
        )
