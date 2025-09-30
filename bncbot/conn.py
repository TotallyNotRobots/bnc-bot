# SPDX-FileCopyrightText: 2019 Snoonet
# SPDX-FileCopyrightText: 2020-present linuxdaemon <linuxdaemon.irc@gmail.com>
#
# SPDX-License-Identifier: MIT

import asyncio
import inspect
import ipaddress
import logging
import logging.config
from collections import defaultdict
from datetime import timedelta
from fnmatch import fnmatch
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Union

from asyncirc.protocol import IrcProtocol
from asyncirc.server import Server
from irclib.parser import Message

from bncbot import irc, util
from bncbot.async_util import call_func, timer
from bncbot.bot import Handlers
from bncbot.config import BNCData, BNCQueue, BNCUsers, BotConfig

if TYPE_CHECKING:
    from bncbot.event import Event


class Conn:
    def __init__(self, handlers: Handlers) -> None:
        self.run_dir = Path().resolve()
        self._protocol: Optional[IrcProtocol] = None
        self.handlers = handlers
        self.futures: dict[str, "asyncio.Future[Any]"] = {}
        self.locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        self.loop = asyncio.get_running_loop()
        self.bnc_data = BNCData.load_config(self.data_file)
        self.stopped_future: "asyncio.Future[bool]" = asyncio.Future()
        self.get_users_state: int = 0
        self.config = BotConfig.load_config(self.config_file)
        if not self.log_dir.exists():
            self.log_dir.mkdir()

        self.setup_logger()
        self.logger = logging.getLogger("bncbot")

    def setup_logger(self) -> None:
        do_debug: bool = self.config.debug
        log_to_file: bool = self.config.log_to_file
        formatters = {
            "brief": {
                "format": "[%(asctime)s] [%(levelname)s] %(message)s",
                "datefmt": "%H:%M:%S",
            },
            "full": {
                "format": "[%(asctime)s] [%(levelname)s] %(message)s",
                "datefmt": "%Y-%m-%d][%H:%M:%S",
            },
        }

        handlers: dict[str, dict[str, Any]] = {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "brief",
                "level": "DEBUG",
                "stream": "ext://sys.stdout",
            }
        }

        bncbot_handlers = ["console"]
        asyncio_handlers = ["console"]
        loggers: dict[str, dict[str, Any]] = {
            "bncbot": {"level": "DEBUG", "handlers": bncbot_handlers},
            "asyncio": {"level": "DEBUG", "handlers": asyncio_handlers},
        }

        logging_conf: dict[str, Any] = {
            "version": 1,
            "formatters": formatters,
            "handlers": handlers,
            "loggers": loggers,
        }

        if log_to_file:
            handlers["file"] = {
                "class": "logging.handlers.RotatingFileHandler",
                "maxBytes": 1000000,
                "backupCount": 5,
                "formatter": "full",
                "level": "INFO",
                "encoding": "utf-8",
                "filename": self.log_dir / "bot.log",
            }

            bncbot_handlers.append("file")

            if do_debug:
                handlers["debug_file"] = {
                    "class": "logging.handlers.RotatingFileHandler",
                    "maxBytes": 1000000,
                    "backupCount": 5,
                    "formatter": "full",
                    "encoding": "utf-8",
                    "level": "DEBUG",
                    "filename": self.log_dir / "debug.log",
                }

                asyncio_handlers.append("debug_file")

        logging.config.dictConfig(logging_conf)

    def load_data(self, update: bool = False) -> None:
        """Load cached BNC information from the file"""
        self.save_data()
        if update and not self.bnc_users:
            asyncio.run_coroutine_threadsafe(
                self.get_user_hosts(), loop=self.loop
            )

    def save_data(self) -> None:
        self.bnc_data.save_config(self.data_file)

    async def run(self) -> bool:
        await self.connect()
        self.load_data(True)
        self.start_timers()
        restart = await self.stopped_future
        return restart

    def create_timer(
        self,
        interval: Union[float, timedelta],
        func: Callable[..., Any],
        *args: Any,
        initial_interval: Optional[Union[float, timedelta]] = None,
    ) -> None:
        asyncio.ensure_future(
            timer(interval, func, *args, initial_interval=initial_interval),
            loop=asyncio.get_running_loop(),
        )

    def start_timers(self) -> None:
        self.create_timer(timedelta(hours=8), self.get_user_hosts)

    def send(self, *parts: str) -> None:
        if not self._protocol:
            raise ValueError("Tried to send on closed protocol")

        self._protocol.send(" ".join(parts))

    def module_msg(self, name: str, cmd: str) -> None:
        self.msg(self.prefix + name, cmd)

    async def get_user_hosts(self) -> None:
        """Should only be run periodically to keep the user list in sync"""
        self.get_users_state = 0
        self.bnc_users.clear()
        user_list_fut: "asyncio.Future[None]" = asyncio.Future()
        self.futures["user_list"] = user_list_fut
        self.send("znc listusers")
        await user_list_fut

        for user in self.bnc_users:
            bindhost_fut: "asyncio.Future[str]" = asyncio.Future()
            self.futures["bindhost"] = bindhost_fut
            self.module_msg("controlpanel", f"Get BindHost {user}")
            self.bnc_users[user] = await bindhost_fut

        self.save_data()
        self.load_data()
        host_map = defaultdict(list)
        for user, host in self.bnc_users.items():
            host_map[host].append(user)

        hosts = {
            host: users
            for host, users in host_map.items()
            if host and len(users) > 1
        }

        if hosts:
            self.chan_log(f"WARNING: Duplicate BindHosts found: {hosts}")

    async def connect(self) -> None:
        servers = [
            Server(
                self.config.server,
                self.config.port,
                self.config.ssl,
                self.config.password,
            )
        ]

        self._protocol = IrcProtocol(
            servers,
            "bnc",
            user=self.config.user,
            loop=asyncio.get_running_loop(),
            logger=self.logger,
        )

        self._protocol.register("*", self.handle_line)
        await self._protocol.connect()

    def close(self) -> None:
        if self._protocol:
            self._protocol.quit()

    async def shutdown(self, restart: bool = False) -> None:
        self.chan_log(
            f"Bot {'shutting down' if not restart else 'restarting'}..."
        )
        await asyncio.sleep(1)
        self.close()
        await asyncio.sleep(1)
        self.stopped_future.set_result(restart)

    async def handle_line(self, proto: "IrcProtocol", line: "Message") -> None:
        raw_event = irc.make_event(self, line)
        for handler in self.handlers.get("raw", {}).get("", []):
            await self.launch_hook(raw_event, handler)

    async def launch_hook(
        self, event: "Event", func: Callable[..., None]
    ) -> bool:
        try:
            params = [
                getattr(event, name)
                for name in inspect.signature(func).parameters.keys()
            ]
            await call_func(func, *params)
        except Exception as e:
            self.logger.exception("Error occurred in hook")
            self.chan_log(
                f"Error occurred in hook {func.__name__} '{type(e).__name__}: {e}'"
            )
            return False

        return True

    def is_admin(self, mask: str) -> bool:
        return any(fnmatch(mask.lower(), pat.lower()) for pat in self.admins)

    async def is_bnc_admin(self, name: str) -> bool:
        lock = self.locks["controlpanel_bncadmin"]
        async with lock:
            fut: "asyncio.Future[bool]" = self.futures.setdefault(
                "bncadmin", asyncio.Future()
            )
            self.module_msg("controlpanel", f"Get Admin {name}")
            res = await fut

        return res

    def add_queue(self, nick: str, registered_time: str) -> None:
        self.bnc_queue[nick] = registered_time
        self.save_data()

    def rem_queue(self, nick: str) -> None:
        if nick in self.bnc_queue:
            del self.bnc_queue[nick]
            self.save_data()

    def chan_log(self, msg: str) -> None:
        if self.log_chan:
            self.msg(self.log_chan, msg)

    def add_user(self, nick: str) -> bool:
        if not util.is_username_valid(nick):
            username = util.sanitize_username(nick)
            self.chan_log(
                f"WARNING: Invalid username '{nick}'; sanitizing to {username}"
            )
        else:
            username = nick

        passwd = util.gen_pass()
        try:
            host = self.get_bind_host()
        except ValueError:
            return False

        self.module_msg("controlpanel", f"cloneuser BNCClient {username}")
        self.module_msg("controlpanel", f"Set Password {username} {passwd}")
        self.module_msg("controlpanel", f"Set BindHost {username} {host}")
        self.module_msg("controlpanel", f"Set Nick {username} {nick}")
        self.module_msg("controlpanel", f"Set AltNick {username} {nick}_")
        self.module_msg("controlpanel", f"Set Ident {username} {nick}")
        self.module_msg("controlpanel", f"Set Realname {username} {nick}")
        self.send("znc saveconfig")
        self.module_msg("controlpanel", f"reconnect {username} Snoonet")
        self.msg(
            "MemoServ",
            f"SEND {nick} Your BNC auth is Username: {username} Password: "
            f"{passwd} (Ports: 5457 for SSL - 5456 for NON-SSL) Help: "
            f"/server bnc.snoonet.org 5456 and /PASS {username}:{passwd}",
        )
        self.bnc_users[username] = host
        self.save_data()
        return True

    def get_bind_host(self) -> str:
        for _ in range(50):
            host = str(util.get_random_address(self.bind_host_net))
            if host not in self.bnc_users.values():
                return host

        self.chan_log("ERROR: get_bind_host() has hit a bindhost collision")
        raise ValueError

    def msg(self, target: str, *messages: str) -> None:
        for message in messages:
            self.send(f"PRIVMSG {target} :{message}")

    def notice(self, target: str, *messages: str) -> None:
        for message in messages:
            self.send(f"NOTICE {target} :{message}")

    @property
    def admins(self) -> list[str]:
        return self.config.admins

    @property
    def bnc_queue(self) -> BNCQueue:
        return self.bnc_data.queue

    @property
    def bnc_users(self) -> BNCUsers:
        return self.bnc_data.users

    @property
    def prefix(self) -> str:
        return self.config.status_prefix

    @property
    def cmd_prefix(self) -> str:
        return self.config.command_prefix

    @property
    def log_chan(self) -> Optional[str]:
        return self.config.log_channel

    @property
    def bind_host_net(self) -> util.IPNetwork:
        return ipaddress.ip_network(self.config.bind_host_net)

    @property
    def log_dir(self) -> Path:
        return self.run_dir / "logs"

    @property
    def data_file(self) -> Path:
        return self.run_dir / "bnc.json"

    @property
    def config_file(self) -> Path:
        return self.run_dir / "config.json"

    @property
    def nick(self) -> str:
        assert self._protocol
        return str(self._protocol.nick)

    @nick.setter
    def nick(self, value: str) -> None:
        assert self._protocol
        self._protocol.nick = value
