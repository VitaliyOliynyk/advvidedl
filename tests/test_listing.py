import pytest

from advvidedl.listing import Video, parse_directory, parse_video_code, parse_video_page, url_kind
from conftest import FIXTURES


@pytest.mark.parametrize(
    ("url", "kind", "code"),
    [
        ("https://vider.info/dir/+dse1v51", "dir", None),
        ("https://vider.info/vid/+fxn8m5x", "video", "xn8m5x"),
        ("https://www.vider.pl/vid/+fxn8m5x/", "video", "xn8m5x"),
        ("http://vider.info/vid/+fxn8m5x?autoplay=1", "video", "xn8m5x"),
        ("https://vider.info/", None, None),
        ("https://example.com/vid/+fxn8m5x", None, "xn8m5x"),
        ("League 05", None, None),
    ],
)
def test_url_kind_and_video_code(url, kind, code):
    assert url_kind(url) == kind
    assert parse_video_code(url) == code


def test_parses_live_video_page():
    html = (FIXTURES / "video_live.html").read_text(encoding="utf-8")

    assert parse_video_page(html, "xn8m5x") == Video(
        "xn8m5x", 215072, "Pokemon Indigo League 01- Pokemon wybieram cię !"
    )


def test_video_page_title_fallbacks():
    assert parse_video_page('<h1 itemprop="name"> Tytuł z nagłówka </h1>', "xn8m5x").title == "Tytuł z nagłówka"
    assert parse_video_page("<html></html>", "xn8m5x").title == "xn8m5x"


def test_parses_saved_directory(directory_html):
    videos = parse_directory(directory_html)

    assert len(videos) == 78
    assert videos[0] == Video("8nn5v1", 511796, "Sonic X S01E01")
    assert videos[1].title == "Sonic X S01E02"
    assert len({video.code for video in videos}) == len(videos)


def test_parses_live_directory_without_sidebar():
    html = (FIXTURES / "directory_live.html").read_text(encoding="utf-8")

    videos = parse_directory(html)

    assert len(videos) == 81
    assert videos[0] == Video("xn8m5x", 215072, "Pokemon Indigo League 01- Pokemon wybieram cię !")
    # „Ostatnio odtwarzane video online” z innych katalogów nie trafia na listę
    assert "xn8vv5" not in {video.code for video in videos}


def test_falls_back_to_any_video_link():
    html = """
    <a href="/vid/+fxn8esm"><img src="x.png"></a>
    <a href="/vid/+fxn8esm">Odcinek 1</a>
    <a href="https://vider.info/vid/+fxn8es5" title="Odcinek 2"></a>
    <a href="/dir/+dse1v51">katalog</a>
    """
    videos = parse_directory(html)

    assert [(v.file_id, v.title) for v in videos] == [(215430, "Odcinek 1"), (215437, "Odcinek 2")]


def test_skips_links_in_html_comments():
    html = '<!-- <a href="/vid/+fxn8esm">stary</a> --><a href="/vid/+f8nn5v1">nowy</a>'

    assert [v.code for v in parse_directory(html)] == ["8nn5v1"]


def test_empty_page_has_no_videos():
    assert parse_directory("<html><body></body></html>") == []
