"""
Client-specific code
"""
from __future__ import annotations

import socket
import threading as th


class Client:

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

    def send_request(self, request: Request, contact: Contact) -> bool:
        """
        Send a Request to a specific Contact.
        Returns True if we managed to send the Request, False otherwise.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_sock:
            client_sock.settimeout(settings.contact_connect_timeout)
            req = request.to_bytes()
            try:
                client_sock.connect((contact.address, contact.port))
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
                logger.info(
                    f"Could not send request {request.id!r} to {contact!r}"
                )
            except Exception as e:
                logger.error(f"Unhandled {type(e)} exception caught: {e!r}")
            else:
                logger.info(
                    f"Sent {request.status!r} request {request.id!r} "
                    f"to {contact!r}"
                )
                return True
        return False

    def close(self):
        pass


class ServerConnection:

    def __init__(self, address: str, port: int):
        self.address = address
        self.port = port

    @classmethod
    def from_name(cls, name: str):
        return cls("localhost", int(name))
