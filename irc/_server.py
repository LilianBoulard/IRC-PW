from __future__ import annotations

import time
import socket
import threading as th
import queue

from tinydb.queries import where

from .config import network_buffer_size
from .commands import Command
from ._handler import CommandHandler
from .threads import BaseThread
from .database import Database
from .objects import AwayRegister, Message
from .design import Singleton


# Commands in this queue will be sent by an independent thread
send_queue: queue.Queue[str] = queue.Queue()

# Raw commands in this queue will be handled by an independent thread
handle_queue: queue.Queue[bytes] = queue.Queue()


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

            handler(raw_command, {})


class SenderThread(BaseThread):
    def run(self):
        pass


class ServerHandler(CommandHandler):

    def __init__(self):
        super().__init__()
        self.server = OwnServer()

    def parse_command(self, command: str, _: dict) -> Command:
        nickname, recipient, command, *parameters, timestamp = command.split(':')
        # In case there was some colon in the parameters section,
        # let's construct it back
        parameters = ':'.join(parameters)
        return Command(
            author=nickname,
            recipient=recipient,
            identifier=command,
            parameters=eval(parameters),  # FIXME: Extremely dangerous
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
                    message=" ".join(command.parameters) if command.parameters else "",
                ))

    def help(self, command: Command):
        """Not implemented by the server"""
        return

    def invite(self, command: Command):
        pass

    def _invalid(self, command: Command):
        pass


class Server:

    def __init__(self, address: str, port: int):
        self.address = address
        self.port = port

        self._handler_thread = HandlerThread()
        self._peers = []  # see method `sync`
        self._stop_event = th.Event()

    @classmethod
    def from_name(cls, name: str):
        return cls("localhost", int(name))


class OwnServer(Server, Singleton):

    def sync(self, *srv: tuple[Server]):
        """
        Takes one or more other servers, and registers them locally so that
        information can be replicated over those.
        """
        self._peers.extend(srv)

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
                        raise RuntimeError("Socket connection broken")
                    total_sent += sent
            except (
                    socket.timeout,
                    ConnectionRefusedError,
                    ConnectionResetError,
                    OSError,
            ):
                print(
                    f"Could not send {content!r} to {peer!r}"
                )
            except Exception as e:
                print(f"Unhandled {type(e)} exception caught: {e!r}")

    def _broadcast(self, content: bytes):
        """
        Send something to all peers (other servers).
        """
        for peer in self._peers:
            self._send(content, peer)

    def transmit(self, command: Command):
        """
        Transmits a command to every server we're synced with.
        """
        self._broadcast(command.json().encode())

    def send(self, message: Message):
        """
        Sends a message to a client. In practice, stores it locally if the user is stored on this server,
        otherwise, broadcast it.
        """
        pass

    def listen(self):
        self._handler_thread.start()

    def listen_for_commands(self) -> None:
        """
        Sets up a server and listens on a port.
        It requires a TCP connection to receive information.
        """
        with socket.socket() as server_socket:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((self.address, self.port))
            server_socket.listen()
            while not self._stop_event.is_set():
                connection, address = server_socket.accept()
                raw_command, _ = self._receive_all(connection, address)
                handle_queue.put(raw_command)
                connection.close()

    def _receive_all(
            self, sock: socket.socket, address_check: str | None = None
    ) -> tuple[bytes, tuple[str, int]]:
        """
        Receives all parts of a network-sent message.
        Takes a socket object and returns a tuple with
        (1) the complete message as bytes
        (2) a tuple with (1) the address and (2) distant port of the sender.
        """
        data = bytes()
        while True:
            part, addr = sock.recvfrom(network_buffer_size)
            if address_check:
                if addr == address_check:
                    data += part
            else:
                data += part
            if len(part) < network_buffer_size:
                # Either 0 or end of data
                break
        return data, addr
