from typing import TYPE_CHECKING, Dict, Optional, Tuple

from irclib.parser import Message

from bncbot.event import RawEvent

if TYPE_CHECKING:
    from asyncirc.protocol import IrcProtocol

    from bncbot.conn import Conn

CMD_PARAMS: Dict[str, Tuple[str, ...]] = {
    "PRIVMSG": ("chan", "msg"),
    "NOTICE": ("chan", "msg"),
    "JOIN": ("chan",),
    "PART": ("chan", "msg"),
}


def make_event(conn: "Conn", line: "Message") -> RawEvent:
    cmd = line.command
    params = line.parameters
    assert line.prefix
    nick = line.prefix.nick
    chan: Optional[str] = None
    if cmd in CMD_PARAMS and "chan" in CMD_PARAMS[cmd]:
        chan = params[CMD_PARAMS[cmd].index("chan")]
        if chan.lower() == conn.nick.lower():
            chan = nick

    return RawEvent(
        conn=conn,
        nick=nick,
        user=line.prefix.user,
        host=line.prefix.host,
        mask=line.prefix.mask,
        chan=chan,
        irc_rawline=line,
        irc_command=cmd,
        irc_paramlist=params,
    )
