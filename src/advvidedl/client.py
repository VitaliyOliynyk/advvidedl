"""Pobieranie stron vider.info z automatycznym przechodzeniem captchy."""

import logging
from urllib.parse import urljoin

import requests

from advvidedl.captcha import CaptchaError, CaptchaSolver, captcha_image_url, is_captcha

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
)
TIMEOUT = 30


def new_session() -> requests.Session:
    """Sesja HTTP z nagłówkami przeglądarki, wspólna dla stron, captchy i plików."""
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": USER_AGENT,
            "Referer": "https://vider.info/",
            "Accept-Language": "pl-PL,pl;q=0.9,en;q=0.8",
        }
    )
    return session


class ViderClient:
    """Pobiera strony HTML; gdy trafi na captchę, rozwiązuje ją i ponawia.

    Captcha potrafi wrócić kilka razy także po poprawnej odpowiedzi, dlatego jest
    rozwiązywana w pętli: pierwsze ``ai_attempts`` prób robi model, kolejne użytkownik.
    """

    def __init__(
        self,
        session: requests.Session,
        ai_solver: CaptchaSolver | None,
        manual_solver: CaptchaSolver,
        ai_attempts: int = 4,
        max_captcha: int = 12,
    ) -> None:
        self.session = session
        self.ai_solver = ai_solver
        self.manual_solver = manual_solver
        self.ai_attempts = ai_attempts
        self.max_captcha = max_captcha

    def get_page(self, url: str) -> str:
        html = self._fetch("GET", url)
        attempt = 0
        while is_captcha(html):
            attempt += 1
            if attempt > self.max_captcha:
                raise CaptchaError(f"captcha nierozwiązana po {self.max_captcha} próbach")
            image = self.session.get(urljoin(url, captcha_image_url(html)), timeout=TIMEOUT)
            image.raise_for_status()
            solver = self._solver_for(attempt)
            code = solver.solve(image.content)
            logger.info("captcha %d/%d: %s -> %s", attempt, self.max_captcha, solver.name, code or "(brak)")
            if code is None:
                html = self._fetch("GET", url)
            else:
                html = self._fetch("POST", url, data={"captcha": code})
        return html

    def _solver_for(self, attempt: int) -> CaptchaSolver:
        if self.ai_solver is not None and attempt <= self.ai_attempts:
            return self.ai_solver
        return self.manual_solver

    def _fetch(self, method: str, url: str, data: dict[str, str] | None = None) -> str:
        response = self.session.request(method, url, data=data, timeout=TIMEOUT)
        # vider.info odpowiada 404 także na poprawne strony katalogów i filmów
        if response.status_code >= 500:
            response.raise_for_status()
        # nagłówek nie podaje kodowania, a strony są w UTF-8
        response.encoding = "utf-8"
        return response.text
