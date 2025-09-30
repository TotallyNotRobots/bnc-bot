# SPDX-FileCopyrightText: 2019 Snoonet
# SPDX-FileCopyrightText: 2020-present linuxdaemon <linuxdaemon.irc@gmail.com>
#
# SPDX-License-Identifier: MIT

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
