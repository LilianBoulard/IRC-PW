from __future__ import annotations

import pydantic

from json import JSONDecoder, JSONEncoder
from typing import Optional, TypeVar
from tinydb.queries import where

from .database import Database
from ._utils import get_time


_T = TypeVar("_T")


class BaseObject(pydantic.BaseModel):

    __table_name__: str

    @classmethod
    def all(cls: type[_T]) -> set[_T]:
        """
        Queries the database and gets every message.
        Optionally, a name can be passed, in which case only messages
        from this channel will be returned.
        """
        with Database() as db:
            objects = set()
            for dbo in db.get_all(cls):
                try:
                    objects.update(cls(**dbo))
                except pydantic.ValidationError:
                    continue
        return objects

    def upsert(self) -> None:
        with Database() as db:
            db.upsert(self)

    @classmethod
    def from_name(cls: type[_T], name: str) -> Optional[_T]:
        with Database() as db:
            dbos = []
            for doc in db.search(where("name") == name):
                try:
                    dbos.append(cls(**doc))
                except pydantic.ValidationError:
                    continue
            if len(dbos) == 1:
                return dbos[0]
            else:
                return


class User(BaseObject):

    __table_name__ = "users"

    name: str


class Command(pydantic.BaseModel):

    __table_name__ = "commands"

    author: str  # Nickname
    recipient: str  # Channel or nickname
    identifier: str
    parameters: dict[str, str]

    def __repr__(self) -> str:
        return (
            f"command"
            f":{self.author}"
            f":{self.recipient}"
            f":{self.identifier}"
            f":{JSONEncoder().encode(self.parameters)}"
            f":{get_time()}"
        )

    @classmethod
    def from_repr(cls, command: str):
        if not command.startswith("command:"):
            raise pydantic.ValidationError
        author, recipient, command, *parameters, timestamp = command.split(':')
        # In case there was some colon in the parameters section,
        # let's construct it back
        parameters = ':'.join(parameters)
        assert command == cls.identifier
        return cls(
            author=author,
            recipient=recipient,
            identifier=cls.identifier,
            parameters=JSONDecoder().decode(parameters),
        )


class ClientCommand(pydantic.BaseModel):
    """
    Special state of a command, where parameters are not named,
    but positional.
    """

    author: str
    identifier: str
    parameters: list[str]


class Message(BaseObject):

    __table_name__ = "messages"

    author: str
    channel: str
    content: str
    timestamp: int

    @classmethod
    def all(cls, /, channel: Optional[str] = None) -> set[Message]:
        dbos = super().all()
        if channel:
            return {
                dbo for dbo in dbos
                if dbo.channel == channel
            }
        else:
            return dbos


class AwayRegister(BaseObject):
    """
    A simple register used to store whether a user is away.
    """

    __table_name__ = "away_reg"

    nickname: str
    message: Optional[str]


class ClientChannel(BaseObject):

    __table_name__ = "channel"

    name: str
    key: str


class ServerChannel(BaseObject):

    __table_name__ = "channel"

    name: str
    host: str  # Server hosting the channel
    key: str
    members: list[str]  # Only populated on the host
