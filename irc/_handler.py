from abc import ABC, abstractmethod
from typing import TypeVar


_T = TypeVar("_T")


class CommandHandler(ABC):

    """
    Base class defining the commands.

    Both the client and the run_server must subclass this,
    and implement their logic for each command.
    """

    def __call__(self, to_handle: str):
        command = self._parse_command(to_handle)
        if hasattr(command, "is_known"):
            if command.is_known():
                return

        if not hasattr(self, command.identifier):
            self._invalid(command)
            return

        func = getattr(self, command.identifier)
        func(command)

    @abstractmethod
    def _parse_command(self, command: str) -> _T:
        pass

    @abstractmethod
    def away(self, command: _T):
        """Indicate to others that this user is unreachable. A message can be optionally passed."""
        pass

    @abstractmethod
    def help(self, command: _T):
        """Display the list of available commands."""
        pass

    @abstractmethod
    def invite(self, command: _T):
        """Invite someone in this channel (if applicable)."""
        pass

    @abstractmethod
    def join(self, command: _T):
        """Join a channel by name. A key can optionally be passed."""
        pass

    @abstractmethod
    def list(self, command: _T):
        """Displays the list of channels on this network."""
        pass

    @abstractmethod
    def msg(self, command: _T):
        """Sends a message to someone or to a channel."""
        pass

    @abstractmethod
    def names(self, command: _T):
        """Displays the list of users of the specified channel, otherwise, all channels and their users."""
        pass

    @abstractmethod
    def _invalid(self, command: _T):
        """
        Special method called when the command doesn't have a handling function.
        """
        pass
