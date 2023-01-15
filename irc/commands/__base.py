import pydantic

from abc import ABC, abstractmethod
from argparse import ArgumentParser

from ..design import Singleton
from .._utils import get_time


class Command(ABC, pydantic.BaseModel):

    """
    Base class for commands.

    All commands should inherit this class.
    Commands should not inherit each other.
    """

    nickname: str
    identifier: str
    parameters: list[str]
    _argument_parser: ArgumentParser

    def __repr__(self) -> str:
        return (
            f"command"
            f":{self.nickname}"
            f":{self.identifier}"
            f":{[repr(parameter) for parameter in self.parameters]}"
            f":{get_time()}"
        )

    @classmethod
    def parse(cls, command: str):
        """
        Parse the representation of a command (see `__repr__`).
        """
        if not command.startswith("command:"):
            raise pydantic.ValidationError
        nickname, command, *parameters, timestamp = command.split(':')
        # In case there was some colon in the parameters section,
        # let's construct it back
        parameters = ':'.join(parameters)
        assert command == cls.identifier
        return cls(
            nickname=nickname,
            identifier=cls.identifier,
            parameters=eval(parameters),  # FIXME: Extremely dangerous
        )

    @abstractmethod
    def client_action(self):
        pass

    @abstractmethod
    def server_action(self):
        pass


class Commands(Singleton):

    _commands: dict[str, Command]

    def init(self):
        self._commands = {
            cls.identifier: cls
            for cls in Command.__subclasses__()
        }

    def __contains__(self, item: str) -> bool:
        return item in self._commands

    def __getitem__(self, item: str) -> Command:
        if item in self.__dict__:
            return self.__dict__[item]
        return self._commands[item]


class Response(pydantic.BaseModel):

    nickname: str
    content: str

    def __repr__(self) -> str:
        return (
            f"response"
            f":{self.nickname}"
            f":{self.content}"
            f":{get_time()}"
        )

    @classmethod
    def parse(cls, command: str):
        """
        Parse the representation of a response (see `__repr__`).
        """
        if not command.startswith("command:"):
            raise pydantic.ValidationError
        nickname, *content, timestamp = command.split(':')
        # In case there was some colon in the content,
        # let's construct it back
        content = ':'.join(content)
        return cls(
            nickname=nickname,
            content=content,
        )
