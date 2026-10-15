import io
import sys

import pytest

from advvidedl.cli import main


def test_help_lists_parameters_and_examples(capsys):
    with pytest.raises(SystemExit) as exit_info:
        main(["--help"])

    assert exit_info.value.code == 0
    out = capsys.readouterr().out
    assert out.startswith("Użycie: advvidedl")
    for text in ("--start FILM", "--end FILM", "--output KATALOG", "--dry-run", "Przykłady:"):
        assert text in out


@pytest.mark.parametrize(
    "argv",
    [
        ["https://vider.info/vid/+fxn8m5x", "--start", "League 05"],
        ["https://vider.info/vid/+fxn8m5x", "-e", "League 05"],
        ["https://example.com/dir/+dse1v51"],
    ],
)
def test_invalid_arguments(argv, capsys):
    with pytest.raises(SystemExit) as exit_info:
        main(argv)

    assert exit_info.value.code == 2


def test_without_url_and_terminal_prints_help(monkeypatch, capsys):
    monkeypatch.setattr(sys, "stdin", io.StringIO())

    assert main([]) == 2
    assert "Użycie: advvidedl" in capsys.readouterr().err
