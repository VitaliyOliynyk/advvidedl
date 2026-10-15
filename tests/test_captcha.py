import pytest

from advvidedl import captcha
from advvidedl.captcha import CaptchaError, ManualSolver, captcha_image_url, is_captcha, normalize_code

LIVE_CAPTCHA_FORM = """
<form method="post" style="width:300px; margin:0 auto;">
<!--  <div class="g-recaptcha" data-sitekey="x"></div>-->
  <img src="/streaming/ca-pt-cha.png?1792092399" width="300" height="200">
  <input type="text" value="" class="text-class" name="captcha" autocomplete="off">
  <input type="submit" class="myButton2" value="Wchodzę">
</form>
"""


def test_detects_saved_captcha_page(captcha_html):
    assert is_captcha(captcha_html)
    assert captcha_image_url(captcha_html).endswith("ca-pt-cha.png")


def test_detects_live_captcha_form():
    assert is_captcha(LIVE_CAPTCHA_FORM)
    assert captcha_image_url(LIVE_CAPTCHA_FORM) == "/streaming/ca-pt-cha.png?1792092399"


def test_directory_page_is_not_captcha(directory_html):
    assert not is_captcha(directory_html)


def test_captcha_without_image_raises():
    with pytest.raises(CaptchaError):
        captcha_image_url('<form><input name="captcha"></form>')


def test_normalize_code():
    assert normalize_code(" q1o-lp\n") == "Q1OLP"
    assert normalize_code("Kod: 2LPPN.") == "KOD2LPPN"


def test_manual_solver_saves_image_and_reads_code(tmp_path, monkeypatch):
    opened = []
    monkeypatch.setattr(captcha, "_open_image", lambda path: opened.append(path.read_bytes()))
    monkeypatch.setattr("builtins.input", lambda prompt: " qiolp ")

    assert ManualSolver(tmp_path).solve(b"\x89PNG data") == "QIOLP"
    assert opened == [b"\x89PNG data"]
    assert list(tmp_path.iterdir()) == []


def test_manual_solver_without_console(tmp_path, monkeypatch):
    monkeypatch.setattr(captcha, "_open_image", lambda path: None)

    def no_input(prompt):
        raise EOFError

    monkeypatch.setattr("builtins.input", no_input)

    with pytest.raises(CaptchaError):
        ManualSolver(tmp_path).solve(b"\x89PNG data")
