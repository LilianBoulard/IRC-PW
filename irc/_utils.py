from __future__ import annotations

import time

from hashlib import md5


def get_time() -> int:
    """
    Returns the current time as a UNIX timestamp (seconds since the epoch).
    """
    return round(time.time(), None)


def get_hash(value: bytes) -> str:
    return md5(value).hexdigest()
