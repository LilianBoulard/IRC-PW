from __future__ import annotations

import time
import socket
import threading as th
import queue

from tinydb.queries import where
from json import JSONDecoder

from .config import network_buffer_size
from ._handler import CommandHandler
from .threads import BaseThread
from .database import Database
from .objects import AwayRegister, Command, ServerChannel, User
from .design import Singleton
from ._utils import Printer

handle_queue: queue.Queue[bytes] = queue.Queue()

printer = Printer(verbose=4)


class HandlerThread(BaseThread):
    def run(self):
        handler = ServerHandler()
        while self.running:
            # We don't block because we want to be able to stop the thread
            # with a condition.
            try:
                raw_command = handle_queue.get(
                    block=False
                ).decode()
            except queue.Empty:
                time.sleep(2)
                continue
            except:
                continue
            handler(raw_command)


class ServerHandler(CommandHandler):

    def __init__(self):
        super().__init__()
        self.server = OwnServer()

    def _parse_command(self, command: str) -> Command:
        printer.error(f"Got this command: {command!r}")
        _, nickname, recipient, command, *parameters, timestamp = command.split(':')
        # In case there was some colon in the parameters section,
        # let's construct it back
        parameters = ':'.join(parameters)
        printer.warning(parameters)
        return Command(
            author=nickname,
            recipient=recipient,
            identifier=command,
            parameters=JSONDecoder().decode(parameters),
        )

    def away(self, command: Command):
        with Database() as db:
            if dbo := db.search(where('nickname') == command.author):
                # User has used /away before, we remove the entry
                away_reg = AwayRegister(**dbo)
                db.remove(away_reg)
            else:
                # User has no registry already saved, creating one (they're now away)
                db.upsert(AwayRegister(
                    nickname=command.author,
                    message=command.parameters["message"],
                ))

    def help(self, command: Command):
        """Not implemented by the run_server"""
        return

    def invite(self, command: Command):
        chan = ServerChannel.from_name(command.parameters["channel"])
        if not chan:
            return
        if command.parameters["key"] != chan.key:
            self.server.send(Command(
                author=repr(self.server),
                recipient=command.author,
                identifier="message",
                parameters={
                    "content": (f"Could not invite user {command.recipient!r} "
                                f"to channel {command.parameters['channel']!r}: "
                                f"invalid key {command.parameters['key']!r}.")
                }
            ))

    def join(self, command: Command):
        chan = ServerChannel.from_name(command.parameters["channel"])
        if not chan:
            # We don't know this channel, so we'll create it.
            if command.recipient == repr(self.server):
                # This is the declaration of a channel that has been created
                # on another host.
                chan = ServerChannel(
                    name=command.parameters["channel"],
                    host=command.author,
                    key=command.parameters["key"],
                    members=[command.author],
                )
                chan.upsert()
            else:
                chan = ServerChannel(
                    name=command.parameters["channel"],
                    host=repr(self),
                    key=command.parameters["key"],
                    members=[command.author],
                )
                chan.upsert()
                # Propagate the channel info to other servers
                for peer in self.server.peers:
                    self.server.send(Command(
                        author=repr(self.server),
                        recipient=repr(peer),
                        identifier=command.identifier,
                        parameters={
                            "host": chan.host,
                            "channel": chan.name,
                            "key": chan.key,
                        },
                    ))
        else:
            # We know this channel
            if chan.host == repr(self.server):
                # We are the host of this channel
                if command.parameters["key"] != chan.key:
                    self.server.send(Command(
                        author=repr(self.server),
                        recipient=command.author,
                        identifier="msg",
                        parameters={
                            "content": (f"Cannot join channel "
                                        f"{command.parameters['channel']!r}: "
                                        f"invalid key {command.parameters['key']!r}."),
                        },
                    ))
            else:
                # We are not the channel host, just transmit the command.
                self.server.send(Command(
                    author=command.author,
                    recipient=chan.host,
                    identifier=command.identifier,
                    parameters={
                        "host": chan.host,
                        "channel": command.parameters["channel"],
                        "key": command.parameters["key"],
                    },
                ))

    def list(self, command: Command):
        self.server.send(Command(
            author=repr(self.server),
            recipient=command.author,
            identifier="msg",
            parameters={
                "content": "\n".join([chan.name for chan in ServerChannel.all()]),
            },
        ))

    def msg(self, command: Command):
        self.server.send(Command(
            author=command.author,
            recipient=command.recipient,
            identifier=command.identifier,
            parameters=command.parameters,
        ))

    def names(self, command: Command):
        if command.parameters["channel"]:
            chan = ServerChannel.from_name(command.parameters["channel"])
            if not chan:
                # This channel doesn't exist
                # Transmit the response.
                self.server.send(Command(
                    author=repr(self.server),
                    recipient=command.author,
                    identifier="msg",
                    parameters={
                        "content": f"The channel {command.parameters['channel']!r} "
                                   f"does not exist.",
                    },
                ))
                return
            if chan.host == repr(self.server):
                self.server.send(Command(
                    author=repr(self.server),
                    recipient=command.author,
                    identifier="msg",
                    parameters={
                        "content": f"{chan.name!r}: {' - '.join(chan.members)}",
                    },
                ))
            else:
                # We are not the host ; only they know the members
                self.server.send(Command(
                    author=command.author,
                    recipient=chan.host,
                    identifier=command.identifier,
                    parameters=command.parameters,
                ))
        else:
            for chan in ServerChannel.all():
                self.server.send(Command(
                    author=repr(self.server),
                    recipient=command.author,
                    identifier="msg",
                    parameters={
                        "content": f"{chan.name!r}: {' - '.join(chan.members)}",
                    },
                ))

    def _invalid(self, command: Command):
        pass


class Server:

    def __init__(self, address: str, port: int):
        self.address = address
        self.port = port

    def __repr__(self):
        return f"{self.address}:{self.port}"

    @classmethod
    def from_name(cls, name: str):
        return cls("localhost", int(name))


class OwnServer(Server, Singleton):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._listen_thread = th.Thread(target=self.listen_for_commands)
        self._handler_thread = HandlerThread()
        self.peers = []  # see method `sync`
        self._stop_event = th.Event()

    def sync(self, *srv: tuple[Server]):
        """
        Takes one or more other servers, and registers them locally so that
        information can be replicated over those.
        """
        self.peers.extend(srv)

    def _send(self, content: bytes, peer: Server):
        """
        Send something to someone specific.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_sock:
            client_sock.settimeout(5)
            try:
                client_sock.connect((peer.address, peer.port))
                total_sent = 0
                while total_sent < len(content):
                    sent = client_sock.send(content[total_sent:])
                    if sent == 0:
                        printer.error("Socket connection broken")
                    total_sent += sent
            except (
                    socket.timeout,
                    ConnectionRefusedError,
                    ConnectionResetError,
                    OSError,
            ):
                printer.error(f"Could not send {content!r} to {peer!r}")
            except Exception as e:
                printer.error(f"Unhandled {type(e)} exception caught: {e!r}")

    def send(self, command: Command):
        """
        Sends a command to someone.
        The contact information is inside the command.
        """
        if command.recipient == "*":
            cmd = repr(command).encode()
            for peer in self.peers:
                self._send(cmd, peer)
            return

        contact = User.from_name(command.recipient)
        if not contact:
            # This is not a user we know
            pass

        contact = ServerChannel.from_name(command.recipient)
        if not contact:
            # This is not a contact
            # That was the last possibility, exit
            return

        printer.info(f"Sending {command!r}")

    def listen(self):
        self._handler_thread.start()
        self._listen_thread.start()

    def listen_for_commands(self) -> None:
        """
        Sets up a run_server and listens on a port.
        It requires a TCP connection to receive information.
        """
        with socket.socket() as server_socket:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((self.address, self.port))
            server_socket.listen()
            while not self._stop_event.is_set():
                connection, address = server_socket.accept()
                raw_command, _ = self._receive_all(connection)
                printer.info(f"Received raw command {raw_command.decode()}")
                handle_queue.put(raw_command)
                connection.close()

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

    def close(self):
        self._stop_event.set()
