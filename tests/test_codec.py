import re

import pytest

from advvidedl.codec import decode_file_code


def test_decodes_known_codes():
    assert decode_file_code("xn8esm") == 215430
    assert decode_file_code("8nn5v1") == 511796
    assert decode_file_code("8nncmm") == 511800


def test_matches_id_code_pairs_from_saved_page(directory_html):
    # Wykomentowana stara lista ma przy każdym filmie id="f-<ID>" i miniaturkę /i/<kod>/.
    tokens = re.findall(r'id="f-(\d+)"|img\.vider\.info/i/([a-z0-9]+)/', directory_html)
    pairs = []
    file_id = None
    for number, code in tokens:
        if number:
            file_id = int(number)
        elif file_id is not None:
            pairs.append((file_id, code))
            file_id = None
    assert len(pairs) >= 50
    for file_id, code in pairs:
        assert decode_file_code(code) == file_id


@pytest.mark.parametrize("code", ["", "xn8a", "XN8ESM"])
def test_rejects_invalid_codes(code):
    with pytest.raises(ValueError):
        decode_file_code(code)
