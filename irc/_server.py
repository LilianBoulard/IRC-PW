from __future__ import annotations

import time
import socket
import threading as th
import queue

import pydantic

from .config import network_buffer_size
from .commands import Commands
from .threads import BaseThread


# Commands in this queue will be sent by an independent thread
send_queue: queue.Queue[str] = queue.Queue()

# Raw commands in this queue will be handled by an independent thread
handle_queue: queue.Queue[bytes] = queue.Queue()


class HandlerThread(BaseThread):
    def run(self):
        commands = Commands()
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

            # Extract the identifier
            try:
                _, identifier, *_ = raw_command.split(':')
            except:
                continue

            # Instantiate the command
            if identifier not in commands:
                continue
            try:
                command = commands[identifier].parse(raw_command)
            except pydantic.ValidationError:
                continue

            # Now that we have the command, we'll run the server action.
            command.server_action()


class SenderThread(BaseThread):
    def run(self):
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

    def sync(self, *srv: tuple[Server]):
        """
        Takes one or more other servers, and registers them locally so that
        information can be replicated over those.
        """
        self._peers.extend(srv)

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
