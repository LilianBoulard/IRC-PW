from irc import Server

from argparse import ArgumentParser


if __name__ == "__main__":
    _parser = ArgumentParser()

    _parser.add_argument(
        "server_name", help="Name of this server.",
        type=str, nargs=1, required=True,
    )
    _parser.add_argument(
        "servers", help="Other server to sync with.",
        type=str, nargs="+", required=True,
    )

    _args = _parser.parse_args()

    server = Server.from_name(_args.server_name)
    server.sync(*_args.servers)
    server.listen()
    app = Controller(has_ui=False)
    app.loop()
    server.close()
