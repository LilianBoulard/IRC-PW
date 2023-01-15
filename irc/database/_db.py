from __future__ import annotations

from typing import Callable, Optional, TypeVar
from pathlib import Path
from tinydb import TinyDB
from tinydb.table import Document
from functools import wraps

from ..design import Singleton
from .._utils import SupportsComparison


_T = TypeVar("_T")


def _get_table_name(obj) -> str:
    return obj.__table_name__


class Database(Singleton):

    """
    Simple, generic interface to access a TinyDB file.
    Database logic is implemented in the objects.
    """

    _db: TinyDB

    def __enter__(self) -> Database:
        return self

    def __exit__(self, *_, **__) -> None:
        pass

    def search(self, *args, **kwargs):
        return self._db.search(*args, **kwargs)

    def init(self):
        self._db = TinyDB(Path(__file__).parent.parent / "database.tinydb")  # FIXME

    def get_by_id(self, obj: _T, identifier: int) -> Document:
        return self._db.table(_get_table_name(obj)).get(doc_id=identifier)

    def get_all(self, obj: _T) -> list[Document]:
        return self._db.table(_get_table_name(obj)).all()

    def is_known(self, obj: _T) -> bool:
        return self._db.table(_get_table_name(obj)).contains(doc_id=obj.id)

    def get_last(
        self, obj: _T, key: Callable[[_T], SupportsComparison]
    ) -> Optional[Document]:
        return sorted(self._db.table(_get_table_name(obj)).all(), key=key)[0]

    def upsert(self, obj: _T) -> None:
        """
        Takes any object from Sami and inserts/updates the information
        in the database.
        """
        self._db.table(_get_table_name(obj)).upsert(Document(obj.dict(), doc_id=obj.id))

    def remove(self, obj: _T) -> None:
        self._db.table(_get_table_name(obj)).remove(obj.id)
