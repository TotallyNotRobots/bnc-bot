# SPDX-FileCopyrightText: 2019 Snoonet
# SPDX-FileCopyrightText: 2020-present linuxdaemon <linuxdaemon.irc@gmail.com>
#
# SPDX-License-Identifier: MIT

from pathlib import Path

from pydantic import BaseModel, Field
from typing_extensions import Self


class FileBasedDataModel(BaseModel):
    @classmethod
    def load_config(cls, path: Path) -> Self:
        if path.exists():
            text = path.read_text(encoding="utf8")
            return cls.model_validate_json(text)

        return cls()

    def save_config(self, path: Path) -> None:
        text = self.model_dump_json(indent=4, by_alias=True)
        path.write_text(text, encoding="utf-8")


class BotConfig(FileBasedDataModel):
    user: str = "BNCServ"
    password: str = Field(default="", alias="pass")
    status_prefix: str = "*"
    server: str = "bnc.snoonet.org"
    port: int = 5457
    ssl: bool = True
    admins: list[str] = ["*!*@snoonet/staff/*", "*!*@snoonet/manager/*"]
    log_channel: str = "##log_channel"
    command_prefix: str = "."
    bind_host_net: str = "127.0.0.0/16"

    debug: bool = False
    log_to_file: bool = False
    nickserv_timeout: int | float = 30


BNCUsers = dict[str, str | None]
BNCQueue = dict[str, str]


class BNCData(FileBasedDataModel):
    queue: BNCQueue = {}
    users: BNCUsers = {}
