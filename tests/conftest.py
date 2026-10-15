from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def directory_html() -> str:
    return (FIXTURES / "directory.html").read_text(encoding="utf-8")


@pytest.fixture
def captcha_html() -> str:
    return (FIXTURES / "captcha.html").read_text(encoding="utf-8")
