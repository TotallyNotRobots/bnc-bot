def test_importing_main() -> None:
    import bncbot.__main__  # pylint: disable=import-outside-toplevel

    assert bncbot.__main__
