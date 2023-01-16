from __future__ import annotations

import time
import click

from hashlib import md5
from colorama import Fore
from collections import defaultdict
from typing import Callable, Iterable
from abc import abstractmethod
from typing import Protocol, runtime_checkable, TypeVar, Hashable

from .design import Singleton


_T = TypeVar("_T")


@runtime_checkable
class SupportsComparison(Protocol):
    """An ABC with abstract methods for comparison."""

    __slots__ = ()

    @abstractmethod
    def __eq__(self, other: SupportsComparison) -> bool:
        pass

    @abstractmethod
    def __gt__(self, other: SupportsComparison) -> bool:
        pass

    @abstractmethod
    def __lt__(self, other: SupportsComparison) -> bool:
        pass


def get_time() -> int:
    """
    Returns the current time as a UNIX timestamp (seconds since the epoch).
    """
    return round(time.time(), None)


def get_hash(value: bytes) -> str:
    return md5(value).hexdigest()


def iter_to_dict(iterable: Iterable[_T], /, key: Callable) -> dict[Hashable, list[_T]]:
    """
    Takes an iterable, such as a list, and returns a dictionary mapping
    each value (the result of the function `value`) to an entry.

    Examples
    --------
    >>> iter_to_dict(["this", "is", "a", "test"], value=lambda val: len(val))
    {4: ["this", "test"], 2: ["is"], 1: ["a"]}
    >>> iter_to_dict(["1", "test", "5", "yes"], value=str.isnumeric)
    {True: ["1", "5"], False: ["test", "yes"]}
    """
    final = defaultdict(list)
    for value in iterable:
        final[key(value)].append(value)
    return dict(final)


class Printer(Singleton):

    def __init__(self, verbose: int = 3):
        self.verbose = verbose

    def info(self, message: str):
        if self.verbose >= 1:
            click.echo(f"{message}")

    def error(self, message: str):
        if self.verbose >= 2:
            click.echo(f"{Fore.LIGHTRED_EX}{message}")

    def warning(self, message: str):
        if self.verbose >= 3:
            click.echo(f"{Fore.LIGHTYELLOW_EX}{message}")

    def debug(self, message: str):
        if self.verbose >= 4:
            click.echo(f"{Fore.LIGHTBLUE_EX}{message}")
