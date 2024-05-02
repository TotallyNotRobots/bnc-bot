import pytest

from bncbot import util


@pytest.mark.parametrize(
    ["text", "result"],
    [
        ("foo", "foo"),
    ],
)
def test_sanitize_username(text: str, result: str) -> None:
    assert util.sanitize_username(text) == result
