# SPDX-FileCopyrightText: 2019 Snoonet
# SPDX-FileCopyrightText: 2020-present linuxdaemon <linuxdaemon.irc@gmail.com>
#
# SPDX-License-Identifier: MIT

import asyncio
import logging

from bncbot import bot
from bncbot.conn import Conn


async def async_main() -> None:
    conn = Conn(bot.HANDLERS)

    await conn.run()


def main() -> None:
    try:
        asyncio.run(async_main())
    finally:
        logging.shutdown()
