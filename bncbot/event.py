# SPDX-FileCopyrightText: 2019 Snoonet
# SPDX-FileCopyrightText: 2020-present linuxdaemon <linuxdaemon.irc@gmail.com>
#
# SPDX-License-Identifier: MIT

from asyncio import AbstractEventLoop
from typing import TYPE_CHECKING, Optional, overload

from typing_extensions import Self

from bncbot.config import BNCData, BNCQueue, BNCUsers

if TYPE_CHECKING:
    from irclib.parser import Message, ParamList

    from bncbot.bot import Command
    from bncbot.conn import Conn


class Event:
    @overload
    def __init__(
        self,
        *,
        conn: "Conn",
        base_event: None = None,
        nick: str | None,
        user: str | None,
        host: str | None,
        mask: str | None,
        chan: str | None = None,
    ) -> None: ...

    @overload
    def __init__(
        self,
        *,
        conn: Optional["Conn"] = None,
        base_event: "Event",
        nick: str | None = None,
        user: str | None = None,
        host: str | None = None,
        mask: str | None = None,
        chan: str | None = None,
    ) -> None: ...

    def __init__(
        self,
        *,
        conn: Optional["Conn"] = None,
        base_event: Optional["Event"] = None,
        nick: str | None = None,
        user: str | None = None,
        host: str | None = None,
        mask: str | None = None,
        chan: str | None = None,
    ) -> None:
        if base_event:
            self.conn: Conn = conn or base_event.conn
            self.nick: str | None = nick or base_event.nick
            self.user: str | None = user or base_event.user
            self.host: str | None = host or base_event.host
            self.mask: str | None = mask or base_event.mask
            self.chan: str | None = chan or base_event.chan
        else:
            if conn is None:
                msg = "'conn' must be set or inherited"
                raise ValueError(msg)

            self.conn = conn
            self.nick = nick
            self.user = user
            self.host = host
            self.mask = mask
            self.chan = chan

    def message(self, message: str, target: str | None = None) -> None:
        if not target:
            if not self.chan:
                msg = "'target' must be set when Event.chan is None"
                raise ValueError(msg)

            target = self.chan

        self.conn.msg(target, message)

    def notice(self, message: str, target: str | None = None) -> None:
        if not target:
            if not self.nick:
                msg = "'target' must be set when Event.nick is None"
                raise ValueError(msg)

            target = self.nick

        self.conn.notice(target, message)

    @property
    def bnc_data(self) -> BNCData:
        return self.conn.bnc_data

    @property
    def bnc_queue(self) -> BNCQueue:
        return self.conn.bnc_queue

    @property
    def bnc_users(self) -> BNCUsers:
        return self.conn.bnc_users

    @property
    def event(self) -> Self:
        return self

    @property
    def loop(self) -> AbstractEventLoop:
        return self.conn.loop

    @property
    def is_admin(self) -> bool:
        if not self.mask:
            return False

        return self.conn.is_admin(self.mask)


class RawEvent(Event):
    @overload
    def __init__(
        self,
        *,
        conn: "Conn",
        base_event: None = None,
        nick: str | None,
        user: str | None,
        host: str | None,
        mask: str | None,
        chan: str | None = None,
        irc_rawline: "Message",
        irc_command: str,
        irc_paramlist: "ParamList",
    ) -> None: ...

    @overload
    def __init__(
        self,
        *,
        conn: Optional["Conn"] = None,
        base_event: "Event",
        nick: str | None = None,
        user: str | None = None,
        host: str | None = None,
        mask: str | None = None,
        chan: str | None = None,
        irc_rawline: Optional["Message"] = None,
        irc_command: str | None = None,
        irc_paramlist: Optional["ParamList"] = None,
    ) -> None: ...

    def __init__(
        self,
        *,
        conn: Optional["Conn"] = None,
        base_event: Event | None = None,
        nick: str | None = None,
        user: str | None = None,
        host: str | None = None,
        mask: str | None = None,
        chan: str | None = None,
        irc_rawline: Optional["Message"] = None,
        irc_command: str | None = None,
        irc_paramlist: Optional["ParamList"] = None,
    ) -> None:
        if base_event is not None:
            super().__init__(
                conn=conn,
                base_event=base_event,
                nick=nick,
                user=user,
                host=host,
                mask=mask,
                chan=chan,
            )
        else:
            if conn is None:
                msg = "'conn' must be set or inherited"
                raise ValueError(msg)

            super().__init__(
                conn=conn, nick=nick, user=user, host=host, mask=mask, chan=chan
            )

        self.irc_rawline = irc_rawline
        self.irc_command = irc_command
        self.irc_paramlist = irc_paramlist


class CommandEvent(Event):
    def __init__(
        self,
        *,
        conn: Optional["Conn"] = None,
        base_event: Event,
        nick: str | None = None,
        user: str | None = None,
        host: str | None = None,
        mask: str | None = None,
        chan: str | None = None,
        command: str,
        text: str | None = None,
        cmd_handler: "Command",
    ) -> None:
        super().__init__(
            conn=conn,
            base_event=base_event,
            nick=nick,
            user=user,
            host=host,
            mask=mask,
            chan=chan,
        )

        self.command = command
        self.text = text
        self.cmd_handler = cmd_handler

    def notice_doc(self) -> None:
        if not self.cmd_handler.doc:
            message = f"{self.conn.cmd_prefix}{self.command} requires additional arguments."
        else:
            message = (
                f"{self.conn.cmd_prefix}{self.command} {self.cmd_handler.doc}"
            )

        self.notice(message)
