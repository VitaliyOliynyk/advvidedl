"""Pobieranie plików MP4 z serwera strumieni, ze wznawianiem przerwanych pobrań."""

import logging
import re
from pathlib import Path

import requests
from tqdm import tqdm

from advvidedl.listing import Video

logger = logging.getLogger(__name__)

STREAM_URL = "https://stream.vider.info/video/{file_id}/v.mp4?uid=0"
CHUNK_SIZE = 1024 * 1024
TIMEOUT = 60
RETRIES = 3

_INVALID_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


class DownloadError(Exception):
    """Serwer zwrócił coś innego niż oczekiwany plik."""


def stream_url(file_id: int) -> str:
    return STREAM_URL.format(file_id=file_id)


def safe_filename(title: str) -> str:
    """Tytuł jako nazwa pliku .mp4, bezpieczna w Windows."""
    name = _INVALID_CHARS.sub("_", title).strip()
    name = re.sub(r"\.mp4$", "", name, flags=re.IGNORECASE).rstrip(". ")
    return (name or "video") + ".mp4"


def assign_filenames(videos: list[Video]) -> list[tuple[Video, str]]:
    """Nazwy plików dla filmów; powtarzające się tytuły dostają dopisek ``[id]``."""
    names = [safe_filename(video.title) for video in videos]
    counts: dict[str, int] = {}
    for name in names:
        counts[name.lower()] = counts.get(name.lower(), 0) + 1
    return [
        (video, f"{name[:-4]} [{video.file_id}].mp4" if counts[name.lower()] > 1 else name)
        for video, name in zip(videos, names)
    ]


def download_video(session: requests.Session, video: Video, path: Path) -> bool:
    """Pobiera film do ``path``. Zwraca False, gdy plik już istnieje.

    Dane trafiają najpierw do ``<nazwa>.part``; zerwane połączenie jest wznawiane od
    miejsca przerwania (także przy następnym uruchomieniu programu).
    """
    if path.exists():
        return False
    part = path.with_name(path.name + ".part")
    for attempt in range(1, RETRIES + 1):
        try:
            _download_part(session, stream_url(video.file_id), part, path.name)
            break
        except (requests.ConnectionError, requests.Timeout, requests.exceptions.ChunkedEncodingError) as exc:
            if attempt == RETRIES:
                raise
            logger.warning("  zerwane połączenie (%s), wznawiam (%d/%d)", exc.__class__.__name__, attempt, RETRIES - 1)
    part.replace(path)
    return True


def _download_part(session: requests.Session, url: str, part: Path, label: str) -> None:
    offset = part.stat().st_size if part.exists() else 0
    headers = {"Range": f"bytes={offset}-"}
    with session.get(url, headers=headers, stream=True, timeout=TIMEOUT) as response:
        if response.status_code == 416:
            total = _total_size(response)
            if total is not None and offset == total:
                return
            raise DownloadError(f"serwer odrzucił wznowienie od bajtu {offset}")
        response.raise_for_status()
        if response.headers.get("Content-Type", "").startswith("text/"):
            raise DownloadError(f"serwer zwrócił stronę zamiast filmu ({response.url})")
        if response.status_code == 206:
            total = _total_size(response)
            mode = "ab"
        else:
            # serwer zignorował Range: zaczynamy od zera
            total = int(response.headers.get("Content-Length", 0)) or None
            offset = 0
            mode = "wb"
        with (
            open(part, mode) as file,
            tqdm(
                total=total,
                initial=offset,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
                desc=label[:40],
                leave=False,
            ) as bar,
        ):
            for chunk in response.iter_content(CHUNK_SIZE):
                file.write(chunk)
                bar.update(len(chunk))
    size = part.stat().st_size
    if total is not None and size != total:
        raise requests.exceptions.ChunkedEncodingError(f"niekompletny plik: {size} z {total} B")


def _total_size(response: requests.Response) -> int | None:
    """Całkowity rozmiar pliku z nagłówka ``Content-Range: bytes a-b/<total>``."""
    _, _, total = response.headers.get("Content-Range", "").rpartition("/")
    return int(total) if total.isdigit() else None
