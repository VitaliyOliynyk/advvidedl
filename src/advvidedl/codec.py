"""Dekodowanie kodów plików vider.info (część linku po ``/vid/+f``) na numeryczne ID.

Kod to ID pliku zapisane cyfra po cyfrze szyfrem podstawieniowym, np. ``xn8esm`` -> ``215430``.
Tego ID używa serwer strumieni: ``https://stream.vider.info/video/<id>/v.mp4``.
"""

_DIGITS = {
    "m": "0",
    "n": "1",
    "x": "2",
    "s": "3",
    "e": "4",
    "8": "5",
    "1": "6",
    "5": "7",
    "c": "8",
    "v": "9",
}


def decode_file_code(code: str) -> int:
    """Zwraca numeryczne ID pliku dla kodu z linku ``/vid/+f<kod>``."""
    if not code:
        raise ValueError("pusty kod pliku")
    try:
        return int("".join(_DIGITS[ch] for ch in code))
    except KeyError as exc:
        raise ValueError(f"nieznany znak {exc.args[0]!r} w kodzie pliku {code!r}") from None
