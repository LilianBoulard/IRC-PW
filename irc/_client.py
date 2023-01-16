"""
Client-specific code
"""
from __future__ import annotations

import inspect
import socket
import time
import queue

from json import JSONDecoder

from .objects import Command, ClientCommand, ClientChannel
from .threads import BaseThread
from ._handler import CommandHandler
from .design import Singleton
from ._utils import Printer
from .config import network_buffer_size


sender_queue: queue.Queue[str] = queue.Queue()


printer = Printer(verbose=4)


class SenderThread(BaseThread):

    def run(self):
        handler = ClientHandler()
        while self.running:
            try:
                command = sender_queue.get()
            except queue.Empty:
                time.sleep(2)
                continue
            handler(command)


class ClientHandler(CommandHandler):
    """
    Class containing the code used to handle the commands
    received from the user.
    """

    def _parse_command(self, command: str) -> ClientCommand | Command:
        """
        Gets a command as the user inputs it:
        `command parameters...`, and returns a client command object.
        """
        if command.startswith("command:"):
            nickname, recipient, command, *parameters, timestamp = command.split(':')
            # In case there was some colon in the parameters section,
            # let's construct it back
            parameters = ':'.join(parameters)
            return Command(
                author=nickname,
                recipient=recipient,
                identifier=command,
                parameters=JSONDecoder().decode(parameters),
            )
        # Remove the prefix
        if command.startswith("/"):
            command = command[1:]
        command_parts = command.split()
        return ClientCommand(
            author=self.client.name,
            identifier=command_parts.pop(0),
            parameters=command_parts,
        )

    def __init__(self):
        super().__init__()
        self.client = Client()

    def away(self, command: ClientCommand):
        if command.parameters:
            self.client.send_command(Command(
                author=command.author,
                recipient="*",
                identifier=command.identifier,
                parameters={"message": " ".join(command.parameters)},
            ))
        else:
            self.client.send_command(Command(
                author=command.author,
                recipient="*",
                identifier=command.identifier,
                parameters={},
            ))

    def help(self, command: ClientCommand):
        if command.parameters:
            printer.error("Invalid number of parameters.")
            return
        message = "Available commands:\n\n"
        for func_name, _ in inspect.getmembers(CommandHandler, predicate=inspect.isfunction):
            if func_name.startswith('_'):
                continue
            doc = inspect.getdoc(getattr(CommandHandler, func_name))
            message += f"/{func_name}\t{doc}\n"
        printer.info(message)

    def invite(self, command: ClientCommand | Command):
        if len(command.parameters) != 2:
            printer.error("Invalid number of parameters.")
            return
        chan = ClientChannel.from_name(command.parameters[1])
        if not chan:
            # This is not a channel, but a user
            printer.error(
                f"{command.parameters[1]!r} is not a channel we're part of"
            )
            return
        self.client.send_command(Command(
            author=command.author,
            recipient=command.parameters[0],
            identifier=command.identifier,
            parameters={
                "channel": chan.name,
                "key": chan.key,
            }
        ))

    def join(self, command: ClientCommand):
        if len(command.parameters) == 1:
            channel = command.parameters[0]
            key = ""
        elif len(command.parameters) == 2:
            channel = command.parameters[0]
            key = command.parameters[1]
        else:
            printer.error("Invalid number of parameters.")
            return

        self.client.send_command(Command(
            author=command.author,
            recipient="*",
            identifier=command.identifier,
            parameters={
                "channel": channel,
                "key": key,
                "host": "",
            }
        ))

    def list(self, command: ClientCommand):
        if command.parameters:
            printer.error("Invalid number of parameters.")
            return
        self.client.send_command(Command(
            author=command.author,
            recipient="*",
            identifier=command.identifier,
            parameters={},
        ))

    def msg(self, command: ClientCommand | Command):
        if isinstance(command, ClientCommand):
            if len(command.parameters) <= 2:
                printer.error("Invalid number of parameters.")
                return
            parameters = command.parameters.copy()
            self.client.send_command(Command(
                author=command.author,
                recipient=parameters.pop(0),
                identifier=command.identifier,
                parameters={"content": " ".join(parameters)},
            ))
        else:
            printer.info(f"{command.author} | {command.parameters['content']}")

    def names(self, command: ClientCommand):
        if len(command.parameters) == 0:
            channel = ""
        elif len(command.parameters) == 1:
            channel = command.parameters[0]
        else:
            printer.error("Invalid number of parameters.")
            return

        self.client.send_command(Command(
            author=command.author,
            recipient="*",
            identifier=command.identifier,
            parameters={"channel": channel},
        ))

    def _invalid(self, command: ClientCommand | Command):
        printer.error(f"Invalid command {command.identifier!r}.")


class Client(Singleton):

    """
    The unique client instance.
    Should not be instanced when running as a run_server.
    """

    def __init__(self, name: str):
        self.name = name
        self._server = None
        self.send_thread = SenderThread()

    @property
    def connection(self):
        if self._server is None:
            raise RuntimeError(
                "No run_server connection has been registered by the client. "
                "Use `client.connection = ServerConnection(...) to fix. `"
            )
        return self._server

    @connection.setter
    def connection(self, value: ServerConnection):
        self._server = value

    def run(self):
        self.send_thread.start()

    def input(self, command: str):
        sender_queue.put(command)

    def send_command(self, command: Command):
        """
        Send a command to the server we're connected to.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_sock:
            client_sock.settimeout(5)
            req = repr(command).encode()
            try:
                client_sock.connect((self.connection.address, self.connection.port))
                total_sent = 0
                while total_sent < len(req):
                    sent = client_sock.send(req[total_sent:])
                    printer.info(f"Send {req[total_sent:total_sent+sent].decode()}")
                    if sent == 0:
                        printer.error("Socket connection broken")
                        return
                    total_sent += sent
            except (
                socket.timeout,
                ConnectionRefusedError,
                ConnectionResetError,
                OSError,
            ):
                printer.error(
                    f"Could not send command to {self.connection!r}. "
                    f"Please ensure the server you've specified is running."
                )
            except Exception as e:
                printer.error(f"Unhandled {type(e)} exception caught: {e!r}")
            else:
                # Wait for the response
                response, _ = self._receive_all(client_sock)
                sender_queue.put(response.decode())

    def _receive_all(self, sock: socket.socket) -> tuple[bytes, tuple[str, int]]:
        """
        Receives all parts of a network-sent message.
        Takes a socket object and returns a tuple with
        (1) the complete message as bytes
        (2) a tuple with (1) the address and (2) distant port of the sender.
        """
        data = bytes()
        while True:
            part, addr = sock.recvfrom(network_buffer_size)
            data += part
            if len(part) < network_buffer_size:
                # Either 0 or end of data
                break
        return data, addr


class ServerConnection:

    def __init__(self, address: str, port: int):
        self.address = address
        self.port = port

    def __repr__(self) -> str:
        return f"{self.address}:{self.port}"

    @classmethod
    def from_name(cls, name: str):
        return cls("localhost", int(name))
