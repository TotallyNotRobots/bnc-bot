# SPDX-FileCopyrightText: 2019 Snoonet
# SPDX-FileCopyrightText: 2020-present linuxdaemon <linuxdaemon.irc@gmail.com>
#
# SPDX-License-Identifier: MIT

from unittest.mock import MagicMock

from irclib.parser import Message

from bncbot import irc
from bncbot.conn import Conn


def make_mock_conn() -> Conn:
    mock = MagicMock()
    mock.configure_mock(nick="mybot")
    mock.mock_add_spec(spec=Conn, spec_set=True)
    return mock


async def test_make_event_no_chan() -> None:
    conn = make_mock_conn()
    event = irc.make_event(conn, Message.parse(":server.tld PING foo"))
    assert event.nick == "server.tld"


async def test_make_event_private_message() -> None:
    conn = make_mock_conn()
    conn.nick = "mybot"
    event = irc.make_event(
        conn, Message.parse(":server.tld PRIVMSG MyBot :this is a test")
    )
    assert event.chan == "server.tld"


async def test_make_event() -> None:
    conn = make_mock_conn()
    conn.nick = "mybot"
    event = irc.make_event(
        conn, Message.parse(":server.tld PRIVMSG #foo :this is a test")
    )
    assert event.chan == "#foo"
