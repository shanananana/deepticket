from deepticket.api.routers.uploads import _FILENAME_RE


def test_upload_filename_pattern() -> None:
    assert _FILENAME_RE.fullmatch("a" * 32 + ".png")
    assert _FILENAME_RE.fullmatch("b" * 32 + ".jpeg")
    assert _FILENAME_RE.fullmatch("c" * 32 + ".webp") is not None
    assert _FILENAME_RE.fullmatch("../etc/passwd") is None
    assert _FILENAME_RE.fullmatch("short.png") is None
