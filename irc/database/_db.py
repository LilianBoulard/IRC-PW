from __future__ import annotations

from tinydb import TinyDB
from tinydb.table import Document, Table

from ..design import Singleton
from .._utils import get_hash
from ..commands import Command


class Database(Singleton):

    """
    Simple, generic interface to access a TinyDB file.
    Database logic is implemented in the Sami objects.
    """

    _db: TinyDB
    _table: Table

    def __enter__(self) -> Database:
        return self

    def __exit__(self) -> None:
        pass

    def init(self):
        self._db = TinyDB()  # FIXME
        self._table = self._db.table("")

    def is_known(self, command: str) -> bool:
        identifier = int(get_hash(command.encode()), 16)
        return self._table.contains(doc_id=identifier)

    def upsert(self, identifier: int, command: Command) -> None:
        """
        Takes any object from Sami and inserts/updates the information
        in the database.
        """
        self._table.upsert(Document(command.dict(), doc_id=identifier))
