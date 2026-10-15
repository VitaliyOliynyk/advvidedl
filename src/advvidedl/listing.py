"""Wyciąganie listy filmów ze strony katalogu ``/dir/``."""

import logging
import re
from dataclasses import dataclass

from bs4 import BeautifulSoup

from advvidedl.codec import decode_file_code

logger = logging.getLogger(__name__)

_CODE_RE = re.compile(r"/vid/\+f([a-z0-9]+)")


@dataclass(frozen=True)
class Video:
    """Film z katalogu: kod z linku, numeryczne ID pliku i tytuł."""

    code: str
    file_id: int
    title: str

    @property
    def page_url(self) -> str:
        return f"https://vider.info/vid/+f{self.code}"


def parse_directory(html: str) -> list[Video]:
    """Zwraca filmy z katalogu w kolejności ze strony, bez duplikatów."""
    soup = BeautifulSoup(html, "html.parser")
    # Główna lista; #search_files_result to pusty szablon wyników wyszukiwarki.
    links = soup.select('ul.browse_videos:not(#search_files_result) p.title a[href*="/vid/+f"]')
    if not links:
        links = soup.select('a[href*="/vid/+f"]')

    videos: dict[str, Video] = {}
    for link in links:
        match = _CODE_RE.search(link["href"])
        if not match:
            continue
        code = match.group(1)
        title = link.get_text(" ", strip=True) or link.get("title", "").strip()
        if code in videos:
            # pierwszy link bywa samą miniaturką; tytuł bierzemy z kolejnego
            if title and videos[code].title == code:
                videos[code] = Video(code, videos[code].file_id, title)
            continue
        try:
            file_id = decode_file_code(code)
        except ValueError as exc:
            logger.warning("Pomijam link %s: %s", link["href"], exc)
            continue
        videos[code] = Video(code, file_id, title or code)
    return list(videos.values())
