# SPDX-FileCopyrightText: 2019 Snoonet
# SPDX-FileCopyrightText: 2020-present linuxdaemon <linuxdaemon.irc@gmail.com>
#
# SPDX-License-Identifier: MIT


def test_importing_main() -> None:
    import bncbot.__main__  # noqa: PLC0415

    assert bncbot.__main__ is not None
