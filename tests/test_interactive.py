from pathlib import Path

import pytest

from advvidedl import interactive
from advvidedl.listing import Video
from advvidedl.selection import SelectionError

VIDEOS = [
    Video("xn8m5x", 215072, "Odcinek 01- Start"),
    Video("xn8m5s", 215073, "Odcinek 02- Dalej"),
    Video("xn8nve", 215194, "Odcinek 03- Koniec"),
]


def answer(monkeypatch, *answers):
    """Podstawia kolejne odpowiedzi użytkownika i zwraca listę zadanych pytań."""
    remaining = list(answers)
    prompts = []

    def fake_input(prompt=""):
        prompts.append(prompt)
        if not remaining:
            raise EOFError
        return remaining.pop(0)

    monkeypatch.setattr("builtins.input", fake_input)
    return prompts


def test_ask_url_repeats_until_valid(monkeypatch):
    prompts = answer(monkeypatch, "abc", "https://vider.info/vid/+fxn8m5x")

    assert interactive.ask_url() == "https://vider.info/vid/+fxn8m5x"
    assert len(prompts) == 2


def test_ask_output(monkeypatch):
    answer(monkeypatch, "", '"D:\\Moje Filmy"')

    assert interactive.ask_output() == Path(".")
    assert interactive.ask_output() == Path("D:\\Moje Filmy")


def test_ask_video_by_number_name_url_and_enter(monkeypatch):
    answer(monkeypatch, "2", "koniec", "https://vider.info/vid/+fxn8m5x", "")

    assert interactive.ask_video(VIDEOS, "?") == 1
    assert interactive.ask_video(VIDEOS, "?") == 2
    assert interactive.ask_video(VIDEOS, "?") == 0
    assert interactive.ask_video(VIDEOS, "?") is None


def test_ask_video_repeats_after_bad_answer(monkeypatch):
    prompts = answer(monkeypatch, "9", "odcinek", "nic takiego", "3")

    assert interactive.ask_video(VIDEOS, "?") == 2
    assert len(prompts) == 4


def test_ask_range_defaults(monkeypatch):
    answer(monkeypatch, "", "")

    assert interactive.ask_range(VIDEOS) == (0, 2)


def test_ask_range_repeats_end_before_start(monkeypatch):
    answer(monkeypatch, "3", "1", "")

    assert interactive.ask_range(VIDEOS) == (2, 2)


def test_ask_range_asks_only_missing_end(monkeypatch):
    prompts = answer(monkeypatch, "2")

    assert interactive.ask_range(VIDEOS, start="Start") == (0, 1)
    assert prompts == [interactive.END_PROMPT]


def test_ask_range_with_given_end_before_start(monkeypatch):
    answer(monkeypatch, "3")

    with pytest.raises(SelectionError):
        interactive.ask_range(VIDEOS, end="Start")


def test_confirm(monkeypatch):
    answer(monkeypatch, "", "t", "n", "NIE")

    assert [interactive.confirm("?") for _ in range(4)] == [True, True, False, False]


def test_eof_interrupts(monkeypatch):
    answer(monkeypatch)

    with pytest.raises(KeyboardInterrupt):
        interactive.ask_url()


def test_print_videos(capsys):
    interactive.print_videos(VIDEOS)

    assert capsys.readouterr().out.splitlines()[0] == "  1. Odcinek 01- Start"
