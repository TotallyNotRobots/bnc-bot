# SPDX-FileCopyrightText: 2019 Snoonet
# SPDX-FileCopyrightText: 2020-present linuxdaemon <linuxdaemon.irc@gmail.com>
#
# SPDX-License-Identifier: MIT

"""
Utility functions for working with asyncio
"""

import asyncio
from collections.abc import Awaitable
from datetime import timedelta
from functools import partial
from typing import Any, Callable, NoReturn, TypeVar, Union, cast

from typing_extensions import TypeGuard

_T = TypeVar("_T")


def is_coro(
    func: Union[Callable[..., Awaitable[_T]], Callable[..., _T]],
) -> TypeGuard[Callable[..., Awaitable[_T]]]:
    return asyncio.iscoroutinefunction(func)


async def call_func(
    func: Union[Callable[..., Awaitable[_T]], Callable[..., _T]],
    /,
    *args: Any,
    **kwargs: Any,
) -> _T:
    loop = asyncio.get_running_loop()
    if is_coro(func):
        return await func(*args, **kwargs)

    func = cast(Callable[..., _T], func)
    return await loop.run_in_executor(None, partial(func, *args, **kwargs))


async def timer(
    interval: Union[float, timedelta],
    func: Callable[..., Any],
    *args: Any,
    initial_interval: Union[float, timedelta, None] = None,
) -> NoReturn:
    if initial_interval is None:
        initial_interval = interval

    if isinstance(interval, timedelta):
        interval = interval.total_seconds()

    if isinstance(initial_interval, timedelta):
        initial_interval = initial_interval.total_seconds()

    await asyncio.sleep(initial_interval)
    while True:
        await call_func(func, *args)
        await asyncio.sleep(interval)
