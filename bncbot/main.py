import asyncio
import os
import signal
import sys
import time
from types import FrameType
from typing import Optional

from bncbot import bot
from bncbot.conn import Conn


async def async_main() -> bool:
    with open(".bncbot.pid", "w", encoding="utf8") as pid_file:
        pid_file.write(str(os.getpid()))

    conn = Conn(bot.HANDLERS)

    original_sigint = signal.getsignal(signal.SIGINT)

    def handle_sig(sig: int, frame: Optional[FrameType]) -> None:
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
