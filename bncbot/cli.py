# SPDX-FileCopyrightText: 2019 Snoonet
# SPDX-FileCopyrightText: 2020-present linuxdaemon <linuxdaemon.irc@gmail.com>
#
# SPDX-License-Identifier: MIT

import asyncio
import logging
from pathlib import Path
from typing import Annotated

import typer

from bncbot import bot
from bncbot.conn import Conn

app = typer.Typer(help="Command help")


async def async_main(data_path: Path, config: Path) -> None:
    conn = Conn(bot.HANDLERS, data_path=data_path, config=config)

    await conn.run()


@app.command()
def run(
    data_dir: Annotated[
        Path | None,
        typer.Option(
            dir_okay=True,
            file_okay=False,
            writable=True,
            help="Directory where BNC state data should be stored. Defaults to the current working directory.",
        ),
    ] = None,
    config: Annotated[
        Path | None,
        typer.Option(
            dir_okay=False,
            file_okay=True,
            exists=True,
            readable=True,
            help="Config file to read. Defaults to $DATA_DIR/config,json",
        ),
    ] = None,
) -> None:
    if data_dir is None:
        data_dir = Path.cwd()

    if config is None:
        config = data_dir / "config.json"

    if not data_dir.exists():
        data_dir.mkdir(parents=True)

    try:
        asyncio.run(async_main(data_dir, config))
    finally:
        logging.shutdown()
