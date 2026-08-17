# SPDX-FileCopyrightText: 2019 Snoonet
# SPDX-FileCopyrightText: 2020-present linuxdaemon <linuxdaemon.irc@gmail.com>
#
# SPDX-License-Identifier: MIT

from pathlib import Path
from unittest import mock

from bncbot.config import BNCData, BotConfig
from bncbot.conn import Conn


def _make_conn(config: BotConfig, run_dir: Path = Path()) -> Conn:
    conn = Conn.__new__(Conn)
    conn.config = config
    conn.run_dir = run_dir
    conn.bnc_data = BNCData()
    return conn


def test_client_connect_info_defaults() -> None:
    conn = _make_conn(BotConfig())
    assert conn.client_connect_info() == (
        "(Ports: 5457 for SSL - 5456 for NON-SSL) "
        "Help: /server bnc.snoonet.org 5456"
    )


def test_client_connect_info_custom_config() -> None:
    conn = _make_conn(
        BotConfig(
            server="bnc.example.org",
            client_ssl_port=6697,
            client_non_ssl_port=6667,
        )
    )
    assert conn.client_connect_info() == (
        "(Ports: 6697 for SSL - 6667 for NON-SSL) "
        "Help: /server bnc.example.org 6667"
    )


def test_add_user_reconnects_to_configured_network(tmp_path: Path) -> None:
    conn = _make_conn(BotConfig(bnc_network="MyNetwork"), run_dir=tmp_path)

    with mock.patch.object(conn, "send") as mock_send:
        assert conn.add_user("somenick") is True

    reconnect_cmds = [
        call.args[0]
        for call in mock_send.call_args_list
        if "reconnect somenick" in call.args[0]
    ]
    assert reconnect_cmds == [
        "PRIVMSG *controlpanel :reconnect somenick MyNetwork"
    ]
    assert conn.bnc_users["somenick"] is not None
