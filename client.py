from irc import Client, ServerConnection, Controller

from argparse import ArgumentParser


if __name__ == "__main__":
    _parser = ArgumentParser()

    _parser.add_argument(
        "nickname", help="Username we want to use on the network.",
        type=str, nargs=1,
    )
    _parser.add_argument(
        "server_name", help="Server we want to connect to.",
        type=str, nargs=1,
    )

    _args = _parser.parse_args()

    client = Client(_args.nickname[0])
    client.connection = ServerConnection.from_name(_args.server_name[0])
    app = Controller()
    app.run()
