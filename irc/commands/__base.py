from abc import ABC, abstractmethod


class Argument:
    name: str
    value: any
    required: bool


class Command(ABC):

    """
    Base class for commands.

    All commands should inherit this class.
    Commands should not inherit each other.
    """

    identifier: str
    arguments: list[Argument]

    @classmethod
    def parse(cls, command: str):
        start = f"/{cls.identifier}"
        assert command.startswith(start)
        # TODO

    @abstractmethod
    def action(self):
        pass


class Commands:

    def __init__(self):
        self._commands = {
            cls.identifier: cls
            for cls in Command.__subclasses__()
        }

    def __getitem__(self, item: str):
        if item in self.__dict__:
            return self.__dict__[item]
        return self._commands[item].get()
