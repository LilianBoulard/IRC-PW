import pydantic

from .design import Singleton
from ._utils import get_time


class Command(pydantic.BaseModel):

    author: str  # Nickname
    recipient: str  # Channel or nickname
    identifier: str
    parameters: list[str]

    def __repr__(self) -> str:
        return (
            f"command"
            f":{self.author}"
            f":{self.recipient}"
            f":{self.identifier}"
            f":{self.parameters}"
            f":{get_time()}"
        )

    @classmethod
    def parse(cls, command: str):
        """
        Parse the representation of a command (see `__repr__`).
        """
        if not command.startswith("command:"):
            raise pydantic.ValidationError
        nickname, recipient, command, *parameters, timestamp = command.split(':')
        # In case there was some colon in the parameters section,
        # let's construct it back
        parameters = ':'.join(parameters)
        assert command == cls.identifier
        return cls(
            author=nickname,
            recipient=recipient,
            identifier=cls.identifier,
            parameters=eval(parameters),  # FIXME: Extremely dangerous
        )


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
