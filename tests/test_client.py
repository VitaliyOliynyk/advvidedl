import pytest

from advvidedl.captcha import CaptchaError
from advvidedl.client import ViderClient

CAPTCHA = '<form method="post"><img src="/streaming/ca-pt-cha.png?1"><input name="captcha"></form>'
PAGE = '<ul class="browse_videos"><li><p class="title"><a href="/vid/+fxn8esm">Odcinek</a></p></li></ul>'


class FakeResponse:
    def __init__(self, text="", content=b"", status_code=404):
        self.text = text
        self.content = content
        self.status_code = status_code
        self.encoding = None

    def raise_for_status(self):
        pass


class FakeSession:
    """Zwraca kolejne strony z listy i zapisuje wysłane zapytania."""

    def __init__(self, pages):
        self.pages = list(pages)
        self.requests = []

    def request(self, method, url, data=None, timeout=None):
        self.requests.append((method, data))
        return FakeResponse(self.pages.pop(0))

    def get(self, url, timeout=None):
        assert url == "https://vider.info/streaming/ca-pt-cha.png?1"
        return FakeResponse(content=b"\x89PNG")


class FakeSolver:
    def __init__(self, name, answers):
        self.name = name
        self.answers = list(answers)
        self.calls = 0

    def solve(self, image):
        self.calls += 1
        return self.answers.pop(0)


URL = "https://vider.info/dir/+dse1v51"


def test_page_without_captcha_is_returned_directly():
    session = FakeSession([PAGE])
    client = ViderClient(session, FakeSolver("ai", []), FakeSolver("manual", []))

    assert client.get_page(URL) == PAGE
    assert session.requests == [("GET", None)]


def test_captcha_repeating_after_correct_answers_is_solved_again():
    session = FakeSession([CAPTCHA, CAPTCHA, CAPTCHA, PAGE])
    ai = FakeSolver("ai", ["AAAAA", "BBBBB", "CCCCC"])
    client = ViderClient(session, ai, FakeSolver("manual", []))

    assert client.get_page(URL) == PAGE
    assert session.requests[1:] == [
        ("POST", {"captcha": "AAAAA"}),
        ("POST", {"captcha": "BBBBB"}),
        ("POST", {"captcha": "CCCCC"}),
    ]


def test_switches_to_manual_after_ai_attempts():
    session = FakeSession([CAPTCHA] * 6 + [PAGE])
    ai = FakeSolver("ai", ["AAAAA"] * 4)
    manual = FakeSolver("manual", ["MMMMM", "NNNNN"])
    client = ViderClient(session, ai, manual, ai_attempts=4)

    assert client.get_page(URL) == PAGE
    assert ai.calls == 4
    assert manual.calls == 2


def test_failed_solve_fetches_a_fresh_captcha():
    session = FakeSession([CAPTCHA, CAPTCHA, PAGE])
    client = ViderClient(session, FakeSolver("ai", [None, "AAAAA"]), FakeSolver("manual", []))

    assert client.get_page(URL) == PAGE
    assert session.requests == [("GET", None), ("GET", None), ("POST", {"captcha": "AAAAA"})]


def test_without_ai_solver_uses_manual():
    session = FakeSession([CAPTCHA, PAGE])
    manual = FakeSolver("manual", ["MMMMM"])
    client = ViderClient(session, None, manual)

    assert client.get_page(URL) == PAGE
    assert manual.calls == 1


def test_gives_up_after_max_captcha():
    session = FakeSession([CAPTCHA] * 4)
    client = ViderClient(session, FakeSolver("ai", ["AAAAA"] * 3), FakeSolver("manual", []), max_captcha=3)

    with pytest.raises(CaptchaError):
        client.get_page(URL)
