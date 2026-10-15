"""Wykrywanie strony z captchą i rozwiązywanie jej (model DeepSeek albo ręcznie w konsoli)."""

import base64
import logging
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Protocol

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

CODE_LENGTH = 5

PROMPT = (
    "The image shows a captcha code of exactly 5 characters "
    "(uppercase letters A-Z and digits 0-9). "
    "Reply with only those 5 characters, without spaces or any other text."
)


class CaptchaError(Exception):
    """Nie udało się przejść captchy."""


class CaptchaSolver(Protocol):
    name: str

    def solve(self, image: bytes) -> str | None:
        """Zwraca kod z obrazka albo None, gdy się nie udało."""


def is_captcha(html: str) -> bool:
    """Czy vider.info zamiast treści pokazał stronę z captchą."""
    return BeautifulSoup(html, "html.parser").select_one('input[name="captcha"]') is not None


def captcha_image_url(html: str) -> str:
    """Adres obrazka captchy (zwykle względny, np. ``/streaming/ca-pt-cha.png?<czas>``)."""
    field = BeautifulSoup(html, "html.parser").select_one('input[name="captcha"]')
    form = field.find_parent("form") if field else None
    image = form.find("img", src=True) if form else None
    if image is None:
        raise CaptchaError("na stronie z captchą nie ma obrazka")
    return image["src"]


def normalize_code(text: str) -> str:
    """Wielkie litery, tylko A-Z i 0-9."""
    return re.sub(r"[^A-Z0-9]", "", text.upper())


def _image_type(image: bytes) -> tuple[str, str]:
    """Typ MIME i rozszerzenie pliku na podstawie nagłówka obrazka."""
    if image.startswith(b"\xff\xd8"):
        return "image/jpeg", ".jpg"
    if image.startswith(b"GIF8"):
        return "image/gif", ".gif"
    return "image/png", ".png"


class DeepSeekSolver:
    """Odczytuje captchę modelem DeepSeek z obsługą obrazów (API zgodne z OpenAI)."""

    name = "DeepSeek"

    def __init__(self, api_key: str, model: str, base_url: str = "https://api.deepseek.com") -> None:
        from openai import OpenAI

        self.model = model
        self.client = OpenAI(api_key=api_key, base_url=base_url, timeout=60, max_retries=1)

    def solve(self, image: bytes) -> str | None:
        from openai import OpenAIError

        mime, _ = _image_type(image)
        data_url = f"data:{mime};base64,{base64.b64encode(image).decode('ascii')}"
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=0,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": PROMPT},
                            {"type": "image_url", "image_url": {"url": data_url}},
                        ],
                    }
                ],
            )
        except OpenAIError as exc:
            logger.warning("DeepSeek: błąd API: %s", exc)
            return None
        answer = response.choices[0].message.content or ""
        code = normalize_code(answer)
        if len(code) != CODE_LENGTH:
            logger.warning("DeepSeek: nieprawidłowa odpowiedź %r", answer)
            return None
        return code


class ManualSolver:
    """Zapisuje obrazek captchy, otwiera go, jeśli jest ekran, i prosi o wpisanie kodu.

    Bez ekranu (np. w Dockerze) wystarczy otworzyć zapisany plik: katalog wyjściowy
    jest zwykle zamontowany z hosta.
    """

    name = "ręcznie"

    def __init__(self, image_dir: Path) -> None:
        self.image_dir = image_dir

    def solve(self, image: bytes) -> str | None:
        _, suffix = _image_type(image)
        path = self.image_dir / f"vider-captcha{suffix}"
        path.write_bytes(image)
        logger.info("Obrazek captchy: %s", path.resolve())
        _open_image(path)
        try:
            return normalize_code(input("Wpisz kod z obrazka: ")) or None
        except EOFError:
            raise CaptchaError("brak konsoli do ręcznego wpisania captchy (w Dockerze użyj -it)") from None
        finally:
            try:
                path.unlink()
            except OSError:
                pass


def _open_image(path: Path) -> None:
    """Otwiera obrazek w domyślnej przeglądarce obrazów systemu, o ile jest ekran."""
    try:
        if sys.platform == "win32":
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"):
            subprocess.Popen(["xdg-open", str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError:
        pass
