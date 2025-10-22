# SPDX-FileCopyrightText: 2019 Snoonet
# SPDX-FileCopyrightText: 2020-present linuxdaemon <linuxdaemon.irc@gmail.com>
#
# SPDX-License-Identifier: MIT

import asyncio
import re
from collections import defaultdict
from collections.abc import Callable, Sequence
from functools import partial
from itertools import chain
from typing import TYPE_CHECKING, Any, NamedTuple, TypedDict, TypeVar

from bncbot import util
from bncbot.config import BNCQueue, BNCUsers
from bncbot.event import CommandEvent, RawEvent
from bncbot.util import chunk_str, sanitize_username

if TYPE_CHECKING:
    from bncbot.conn import Conn


class Command(NamedTuple):
    """
    A NamedTuple which represents a registered command
    """

    name: str
    func: Callable[..., Any]
    admin: bool = False
    param: bool = True
    doc: str | None = None


class Handlers(TypedDict):
    raw: dict[str, list[Callable[..., Any]]]
    command: dict[str, Command]


HANDLERS = Handlers(
    {"command": {}, "raw": defaultdict[str, list[Callable[..., Any]]](list)}
)

_T = TypeVar("_T")
_FuncT = TypeVar("_FuncT", bound=Callable[..., Any])


def raw(*cmds: str) -> Callable[[_FuncT], _FuncT]:
    """Register a function as a handler for all raw commands in [cmds]"""

    def _decorate(func: _FuncT, cmd_list: Sequence[str]) -> _FuncT:
        for cmd in cmd_list or ("",):
            HANDLERS["raw"][cmd].append(func)

        return func

    return partial(_decorate, cmd_list=cmds)


def command(
    name: str, *aliases: str, admin: bool = False, require_param: bool = True
) -> Callable[[_FuncT], _FuncT]:
    """Registers a function as a handler for a command"""

    def _decorate(func: _FuncT) -> _FuncT:
        doc = (
            func.__doc__.strip().splitlines()[0].strip()
            if func.__doc__
            else None
        )

        cmd = Command(name, func, admin, require_param, doc)
        HANDLERS["command"].update(
            {alias: cmd for alias in chain((name,), aliases)}
        )
        return func

    return _decorate


@raw()
async def on_raw(conn: "Conn", event: "RawEvent", irc_command: str) -> None:
    conn.logger.info("[incoming] %s", event.irc_rawline)
    for handler in conn.handlers.get("raw", {}).get(irc_command, []):
        await conn.launch_hook(event, handler)


@raw("JOIN")
def on_join(conn: "Conn", chan: str | None, nick: str | None) -> None:
    if (
        nick
        and chan
        and conn.log_chan
        and chan.lower() == conn.log_chan.lower()
        and nick.lower() == conn.nick.lower()
    ):
        conn.chan_log("Bot online.")


@raw("318")
async def on_whois_end(conn: "Conn", irc_paramlist: list[str]) -> None:
    to_remove = []
    for name, fut in conn.futures.items():
        if name.startswith("whois") and name.endswith(irc_paramlist[1]):
            conn.logger.debug("Cancelling future: %s", name)
            fut.set_result("")
            to_remove.append(name)

    for name in to_remove:
        del conn.futures[name]


@raw("330")
async def on_whois_acct(conn: "Conn", irc_paramlist: list[str]) -> None:
    if irc_paramlist[-1] == "is logged in as":
        fut = conn.futures.get(f"whois_acct_{irc_paramlist[1]}")
        if fut:
            fut.set_result(irc_paramlist[2])
            del conn.futures[f"whois_acct_{irc_paramlist[1]}"]


@raw("NOTICE")
async def on_notice(
    irc_paramlist: list[str], conn: "Conn", nick: str | None
) -> None:
    """Handle NickServ info responses"""
    message = irc_paramlist[-1]
    if nick and nick.lower() == "nickserv" and ":" in message:
        conn.logger.debug("Got nickserv message: %s", message)
        # Registered: May 30 00:53:54 2017 UTC (5 days, 19 minutes ago)
        message = message.strip()
        part, content = message.split(":", 1)
        content = content.strip()
        if part == "Registered" and "ns_info" in conn.futures:
            conn.logger.debug("Got registered time for nickserv info")
            conn.futures["ns_info"].set_result(content)
            del conn.futures["ns_info"]


@raw("PRIVMSG")
async def on_privmsg(
    event: "RawEvent",
    irc_paramlist: list[str],
    conn: "Conn",
    nick: str | None,
    host: str | None,
    bnc_users: BNCUsers,
    is_admin: bool,
) -> None:
    message = irc_paramlist[-1]
    if nick and nick.startswith(conn.prefix) and host == "znc.in":
        znc_module = nick[len(conn.prefix) :]
        if znc_module == "status" and (
            user_lsit_fut := conn.futures.get("user_list")
        ):
            match = re.match(
                r"^\|\s*(.+?)\s*\|\s*\d+\s*\|\s*\d+\s*\|$", message
            )

            if match:
                user = match.group(1)
                bnc_users[user] = None
            elif re.match(r"^([=+]+|[-+]+)$", message):
                conn.get_users_state += 1
                if conn.get_users_state == 3:
                    user_lsit_fut.set_result(None)
                    del conn.futures["user_list"]
        elif (
            znc_module == "controlpanel"
            and (bindhost_fut := conn.futures.get("bindhost"))
            and message.startswith("BindHost = ")
        ):
            _, _, host = message.partition("=")
            bindhost_fut.set_result(host.strip())
            del conn.futures["bindhost"]
        elif (
            znc_module == "controlpanel"
            and (bncadmin_fut := conn.futures.get("bncadmin"))
            and message.startswith("Admin = ")
        ):
            _, _, val = message.partition("=")
            bncadmin_fut.set_result(val.strip() == "true")
            del conn.futures["bncadmin"]
    elif message[0] in conn.cmd_prefix:
        cmd, _, text = message[1:].partition(" ")
        text = text.strip()
        handler: Command | None = conn.handlers.get("command", {}).get(cmd)
        if not handler or (handler.admin and not is_admin):
            return

        cmd_event = CommandEvent(
            base_event=event, command=cmd, text=text, cmd_handler=handler
        )

        if handler.param and not text:
            cmd_event.notice_doc()
            return

        await conn.launch_hook(cmd_event, handler.func)


@raw("NICK")
async def on_nick(
    conn: "Conn", irc_paramlist: list[str], nick: str | None
) -> None:
    if nick and nick.lower() == conn.nick.lower():
        conn.nick = irc_paramlist[0]


@command("acceptbnc", admin=True)
async def cmd_acceptbnc(
    text: str, conn: "Conn", bnc_queue: BNCQueue, event: "CommandEvent"
) -> None:
    """<user> - Accepts [user]'s BNC request and sends their login info via a MemoServ memo"""
    nick = text.split(None, 1)[0]
    if nick not in bnc_queue:
        event.message(f"{nick} is not in the BNC queue.")
        return

    conn.rem_queue(nick)
    if conn.add_user(nick):
        conn.chan_log(
            f"{nick} has been set with BNC access and memoserved credentials."
        )
    else:
        conn.chan_log(
            f"Error occurred when attempting to add {nick} to the BNC"
        )


@command("denybnc", admin=True)
async def cmd_denybnc(
    text: str, event: "CommandEvent", bnc_queue: BNCQueue, conn: "Conn"
) -> None:
    """<user> - Deny [user]'s BNC request"""
    nick = text.split()[0]
    if nick not in bnc_queue:
        event.message(f"{nick} is not in the BNC queue.")
        return

    conn.rem_queue(nick)
    event.message(
        f"SEND {nick} Your BNC auth could not be added at this time", "MemoServ"
    )

    conn.chan_log(f"{nick} has been denied. Memoserv sent.")


@command("bncrefresh", admin=True, require_param=False)
async def cmd_bncrefresh(
    conn: "Conn", event: "CommandEvent", nick: str
) -> None:
    """- Refresh BNC account data (Warning: operation is slow)"""
    event.message("Updating user list")
    conn.chan_log(f"{nick} is updating the BNC user list...")
    await conn.get_user_hosts()
    conn.chan_log("BNC user list updated.")


@command("bncqueue", "bncq", admin=True, require_param=False)
async def cmd_bncqueue(bnc_queue: BNCQueue, event: "CommandEvent") -> None:
    """- View the current BNC queue"""
    if bnc_queue:
        for nick, reg_time in bnc_queue.items():
            event.message(f"BNC Queue: {nick} Registered {reg_time}")
    else:
        event.message("BNC request queue is empty")


@command("delbnc", admin=True)
async def cmd_delbnc(
    text: str,
    conn: "Conn",
    bnc_users: BNCUsers,
    chan: str,
    event: "CommandEvent",
    nick: str,
) -> None:
    """<user> - Delete [user]'s BNC account"""
    acct = text.split()[0]
    if acct not in bnc_users:
        event.message(f"{acct} is not a current BNC user")
        return

    conn.module_msg("controlpanel", f"deluser {acct}")
    conn.send("znc saveconfig")
    del bnc_users[acct]
    conn.chan_log(f"{nick} removed BNC: {acct}")
    if chan != conn.log_chan:
        event.message("BNC removed")

    conn.save_data()


@command("bncresetpass", admin=True)
async def cmd_resetpass(
    conn: "Conn", text: str, bnc_users: BNCUsers, event: "CommandEvent"
) -> None:
    """<user> - Resets [user]'s BNC account password and sends them the new info in a MemoServ memo"""
    nick = text.split()[0]
    if nick not in bnc_users:
        event.message(f"{nick} is not a BNC user.")
        return

    passwd = util.gen_pass()
    conn.module_msg("controlpanel", f"Set Password {nick} {passwd}")
    conn.send("znc saveconfig")
    event.message(f"BNC password reset for {nick}")
    event.message(
        f"SEND {nick} [New Password!] Your BNC auth is Username: {nick} "
        f"Password: {passwd} (Ports: 5457 for SSL - 5456 for NON-SSL) "
        f"Help: /server bnc.snoonet.org 5456 and /PASS {nick}:{passwd}",
        "MemoServ",
    )


@command("addbnc", "bncadd", admin=True)
async def cmd_addbnc(
    text: str, conn: "Conn", bnc_users: BNCUsers, event: "CommandEvent"
) -> None:
    """<user> - Add a BNC account for [user] and MemoServ [user] the login credentials"""
    acct = text.split()[0]
    if acct in bnc_users:
        event.message("A BNC account with that name already exists")
    elif conn.add_user(acct):
        conn.chan_log(
            f"{acct} has been set with BNC access and memoserved credentials."
        )
    else:
        conn.chan_log(
            f"Error occurred when attempting to add {acct} to the BNC"
        )


@command("bncsetadmin", admin=True)
async def cmd_setadmin(
    text: str, bnc_users: BNCUsers, event: "CommandEvent", conn: "Conn"
) -> None:
    """<user> - Makes [user] a BNC admin"""
    acct = text.split()[0]
    if acct in bnc_users:
        conn.module_msg("controlpanel", f"Set Admin {acct} true")
        conn.send("znc saveconfig")
        event.message(f"{acct} has been set as a BNC admin")
    else:
        event.message(f"{acct} does not exist as a BNC account")


@command("requestbnc", "bncrequest", require_param=False)
async def cmd_requestbnc(
    nick: str,
    conn: "Conn",
    event: "CommandEvent",
    bnc_users: BNCUsers,
    bnc_queue: BNCQueue,
) -> None:
    """- Submits a request for a BNC account"""
    acct_fut: asyncio.Future[str] = asyncio.Future()
    conn.futures[f"whois_acct_{nick}"] = acct_fut
    conn.send("WHOIS", nick)
    acct = await acct_fut
    if not acct:
        event.message(
            "You must be identified with services to request a BNC account",
            nick,
        )
        return

    conn.logger.info("Got account %s for nick %s", acct, nick)

    username = acct
    username = sanitize_username(username)

    if username in bnc_users:
        event.message(
            "It appears you already have a BNC account. If this is in error, please contact staff in #help",
            nick,
        )
        return

    if acct in bnc_queue:
        event.message(
            "It appears you have already submitted a BNC request. If this is in error, please contact staff in #help",
            nick,
        )
        return

    conn.logger.debug("Starting to get NickServ info for %s", nick)
    async with conn.locks["ns_info"]:
        conn.logger.debug("NickServ info lock acquired")
        ns_info_fut: asyncio.Future[str] = asyncio.Future()
        conn.futures["ns_info"] = ns_info_fut
        event.message(f"INFO {acct}", "NickServ")
        registered_time = await ns_info_fut

    conn.add_queue(acct, registered_time)
    event.message("BNC request submitted.", nick)
    conn.chan_log(f"{acct} added to bnc queue. Registered {registered_time}")


@command("genbindhost", require_param=False, admin=True)
async def cmd_genbindhost(conn: "Conn", event: "CommandEvent") -> None:
    """- Generate a unique bind host and return it"""
    try:
        out = conn.get_bind_host()
    except ValueError:
        out = "Unable to generate unique bindhost"

    event.message(out)


@command("help", require_param=False)
async def cmd_help(event: "CommandEvent", text: str, is_admin: bool) -> None:
    """[command] - Display help for [command] or list all commands if none is specified"""
    if not text:
        # no param, display all available commands
        cmds = HANDLERS.get("command", {}).items()
        aliases = list(
            alias for alias, cmd in cmds if not cmd.admin or is_admin
        )
        aliases.sort()
        msg = f"Available Commands: {', '.join(aliases)}"
        for chunk in chunk_str(msg):
            event.notice(chunk)

        event.notice("For detailed help about a command, use 'help <command>'")
    else:
        cmd = HANDLERS.get("command", {}).get(text.lower())
        if not cmd or (cmd.admin and not is_admin):
            message = "No such command."
        elif not cmd.doc:
            message = f"Command '{text}' has no additional documentation."
        else:
            message = f"{text} {cmd.doc}"

        event.notice(message)
