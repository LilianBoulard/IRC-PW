"""
Client-specific code
"""
from __future__ import annotations

import inspect
import socket
import time
import queue

from .commands import Command
from .threads import BaseThread
from ._handler import CommandHandler
from .design import Singleton


sender_queue: queue.Queue[Command] = queue.Queue()


class SenderThread(BaseThread):
    def run(self):
        while self.running:
            try:
                command = sender_queue.get()
            except queue.Empty:
                time.sleep(2)
                continue
            except:
                continue


class ClientHandler(CommandHandler):
    """
    Class containing the code used to handle the commands
    received from the user.
    """

    def parse_command(self, command: str, context: dict) -> Command:
        """
        Gets a command as the user inputs it:
        `/command parameters...`, and returns a command object.
        """
        if command.startswith('/'):
            command_parts = command[1:].split()
            return Command(
                author=self.client.name,
                recipient=context["channel"],
                identifier=command_parts.pop(0),
                parameters=command_parts,
            )
        else:
            # If the message is not an explicit command,
            # we assume it's a message to be sent on the current
            # channel.
            return Command(
                author=self.client.name,
                recipient=context["channel"],
                identifier="msg",
                parameters=[command],
            )

    def __init__(self):
        super().__init__()
        self.client = Client()

    def away(self, command: Command):
        self.client.send_command(command)

    def help(self, command: Command):
        message = "Available commands:\n\n"
        for func_name, _ in inspect.getmembers(CommandHandler, predicate=inspect.isfunction):
            if func_name.startswith('_'):
                continue
            doc = inspect.getdoc(getattr(CommandHandler, func_name))
            message += f"/{func_name}\t{doc}\n"
        print(message)

    def invite(self, command: Command):
        pass

    def join(self, command: Command):
        self.client.send_command(command)

    def list(self, command: Command):
        pass

    def names(self, command: Command):
        if command.parameters:
            for channel in command.parameters:
                self.client.send_command(Command(
                    author=command.author,
                    recipient=command.recipient,
                    identifier="names",
                    parameters=[channel],
                ))
        else:
            self.client.send_command(Command(
                author=command.author,
                recipient=command.recipient,
                identifier="names",
                parameters=[],
            ))

    def _invalid(self, command: Command):
        print(f"Invalid command {command.identifier!r}.")


class Client(Singleton):

    """
    The unique client instance.
    Should not be instanced when running as a server.
    """

    def __init__(self, name: str):
        self.name = name
        self._server = None

    @property
    def connection(self):
        if self._server is None:
            raise RuntimeError(
                "No server connection has been registered by the client. "
                "Use `client.connection = ServerConnection(...) to fix. `"
            )
        return self._server

    @connection.setter
    def connection(self, value: ServerConnection):
        self._server = value

    def send_command(self, command: Command):
        """
        Send a Request to a specific Contact.
        Returns True if we managed to send the Request, False otherwise.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_sock:
            client_sock.settimeout(5)
            req = command.json().encode()
            try:
                client_sock.connect((self.connection.address, self.connection.port))
                total_sent = 0
                while total_sent < len(req):
                    sent = client_sock.send(req[total_sent:])
                    if sent == 0:
                        raise RuntimeError("Socket connection broken")
                    total_sent += sent
            except (
                socket.timeout,
                ConnectionRefusedError,
                ConnectionResetError,
                OSError,
            ):
                print(
                    f"Could not send command {command!r} to {self.connection!r}"
                )
            except Exception as e:
                print(f"Unhandled {type(e)} exception caught: {e!r}")
            else:
                print(f"Sent {command!r} to {self.connection!r}")


class ServerConnection:

    def __init__(self, address: str, port: int):
        self.address = address
        self.port = port

    def __repr__(self) -> str:
        return f"{self.address}:{self.port}"

    @classmethod
    def from_name(cls, name: str):
        return cls("localhost", int(name))
