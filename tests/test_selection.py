import pytest

from advvidedl.listing import Video, parse_directory
from advvidedl.selection import SelectionError, find_video, select_range


@pytest.fixture
def videos() -> list[Video]:
    from conftest import FIXTURES

    return parse_directory((FIXTURES / "directory_live.html").read_text(encoding="utf-8"))


def test_find_by_url(videos):
    assert find_video(videos, "https://vider.info/vid/+fxn8xmn") == 4
    assert find_video(videos, " https://www.vider.pl/vid/+fxn8xmn/ ") == 4


def test_url_outside_directory(videos):
    with pytest.raises(SelectionError, match="nie należy"):
        find_video(videos, "https://vider.info/vid/+f8nn5v1")


def test_find_by_exact_title(videos):
    assert find_video(videos, "Pokemon Indigo League 05- Spotkanie w Marmorii") == 4


def test_find_by_fragment_ignoring_case(videos):
    assert find_video(videos, "league 05") == 4
    assert find_video(videos, "SPOTKANIE W MARMORII") == 4
    assert find_video(videos, "Pokemon Indigo League 05- Spotkanie w Marmorii.mp4") == 4


def test_ambiguous_fragment_lists_candidates(videos):
    with pytest.raises(SelectionError) as error:
        find_video(videos, "League 1")
    message = str(error.value)
    assert "pasuje do" in message
    assert "Pokemon Indigo League 10- Bulbasaur i ukryta osada" in message


def test_exact_title_wins_over_fragment():
    videos = [Video("n", 1, "Odcinek 1"), Video("x", 2, "Odcinek 10")]

    assert find_video(videos, "odcinek 1") == 0


def test_missing_title(videos):
    with pytest.raises(SelectionError, match="nie znaleziono"):
        find_video(videos, "Digimon")


def test_range_defaults_to_whole_directory(videos):
    assert select_range(videos, None, None) == (0, len(videos) - 1)


def test_range_from_start_to_end_of_directory(videos):
    assert select_range(videos, "League 05", None) == (4, len(videos) - 1)


def test_range_from_beginning_to_end_film(videos):
    assert select_range(videos, None, "League 07") == (0, 6)


def test_range_between_films(videos):
    assert select_range(videos, "League 05", "https://vider.info/vid/+fxn8xms") == (4, 6)


def test_range_in_wrong_order(videos):
    with pytest.raises(SelectionError, match="przed startowym"):
        select_range(videos, "League 07", "League 05")
