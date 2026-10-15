from advvidedl.download import assign_filenames, safe_filename, stream_url
from advvidedl.listing import Video


def test_stream_url():
    assert stream_url(215430) == "https://stream.vider.info/video/215430/v.mp4?uid=0"


def test_safe_filename():
    assert safe_filename("Pokemon Indigo League 01- Pokemon wybieram cię !") == (
        "Pokemon Indigo League 01- Pokemon wybieram cię !.mp4"
    )
    assert safe_filename('A: "b"/c?') == "A_ _b__c_.mp4"
    assert safe_filename("Sonic X S01E01.mp4") == "Sonic X S01E01.mp4"
    assert safe_filename("koniec... ") == "koniec.mp4"
    assert safe_filename("???") == "___.mp4"
    assert safe_filename("  ") == "video.mp4"


def test_duplicate_titles_get_id_suffix():
    videos = [Video("a", 1, "Odcinek"), Video("b", 2, "odcinek"), Video("c", 3, "Inny")]

    assert [name for _, name in assign_filenames(videos)] == [
        "Odcinek [1].mp4",
        "odcinek [2].mp4",
        "Inny.mp4",
    ]
