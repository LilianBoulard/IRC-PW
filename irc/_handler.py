import inspect

from typing import Optional
from abc import ABC, abstractmethod

from .commands import Command


class CommandHandler(ABC):

    """
    Base class defining the commands.

    Both the client and the server must subclass this,
    and implement their logic for each command.
    """

    @abstractmethod
    def __call__(self, to_handle: str, context: dict):
        """
        Should take the command to handle
        (the format depends on whether this is the client or the
        server receiving it), and call `route` with the appropriate command.
        """
        command = self.parse_command(to_handle, context)

        if not hasattr(self, command.identifier):
            self._invalid(command)
            return

        func = getattr(self, command.identifier)
        func(command)

    @abstractmethod
    def parse_command(self, command: str, context: dict) -> Command:
        pass

    @abstractmethod
    def away(self, command: Command) -> None:
        """Indicate to others that this user is unreachable. A message can be optionally passed."""
        pass

    @abstractmethod
    def help(self, command: Command) -> None:
        """Display the list of available commands."""
        pass

    @abstractmethod
    def invite(self, command: Command) -> None:
        """Invite someone in this channel (if applicable)."""
        pass

    @abstractmethod
    def join(self, command: Command) -> None:
        """Join a channel by name. A key can optionally be passed."""
        pass

    @abstractmethod
    def list(self, command: Command) -> None:
        """Displays the list of channels on this network."""
        pass

    @abstractmethod
    def msg(self, command: Command) -> None:
        """Sends a message to someone or to a channel."""
        pass

    @abstractmethod
    def names(self, command: Command):
        """Displays the list of users of the specified channel, otherwise, all channels and their users."""
        pass

    @abstractmethod
    def _invalid(self, command: Command):
        """
        Special method called when the command doesn't have a handling function.
        """
        pass
