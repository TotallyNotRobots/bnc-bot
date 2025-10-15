# SPDX-FileCopyrightText: 2019 Snoonet
# SPDX-FileCopyrightText: 2020-present linuxdaemon <linuxdaemon.irc@gmail.com>
#
# SPDX-License-Identifier: MIT

import asyncio
import os
import signal
import sys
import time
from types import FrameType

import aiofiles

from bncbot import bot
from bncbot.conn import Conn


async def async_main() -> bool:
    async with aiofiles.open(".bncbot.pid", "w", encoding="utf8") as pid_file:
        await pid_file.write(str(os.getpid()))

    conn = Conn(bot.HANDLERS)

    original_sigint = signal.getsignal(signal.SIGINT)

    def handle_sig(sig: int, frame: FrameType | None) -> None:
        if sig == signal.SIGINT:
            if conn:
                asyncio.run_coroutine_threadsafe(conn.shutdown(), conn.loop)

            signal.signal(signal.SIGINT, original_sigint)

    signal.signal(signal.SIGINT, handle_sig)

    return await conn.run()


def main() -> None:
    # store the original working directory, for use when restarting
    original_wd = os.path.realpath(".")
    restart = asyncio.run(async_main())
    if restart:
        time.sleep(1)
        os.chdir(original_wd)
        args = sys.argv
        for f in [sys.stdout, sys.stderr]:
            f.flush()

        os.execv(sys.executable, [sys.executable] + args)
