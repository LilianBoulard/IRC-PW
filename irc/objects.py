from __future__ import annotations

import pydantic

from typing import Optional

from .database import Database


class BaseObject(pydantic.BaseModel):

    __table_name__: str

    @classmethod
    def all(cls) -> set[BaseObject]:
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

    __table_name__ = "away_reg"

    nickname: str
    message: Optional[str]
