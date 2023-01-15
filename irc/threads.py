from __future__ import annotations

import threading as th

from abc import ABC, abstractmethod

from ._events import global_stop_event


class BaseThread(ABC, th.Thread):

    def __init__(self, **kwargs):
        self._local_stop_event = th.Event()

        super().__init__(
            name=self.__class__.__name__,
            daemon=True,
            **kwargs,
        )

    def start(self):
        super().start()

    @property
    def running(self) -> bool:
        return (
            not global_stop_event.is_set()
            and not self._local_stop_event.is_set()
        )

    def stop(self):
        self._local_stop_event.set()

    @abstractmethod
    def run(self):
        raise NotImplementedError
