from irc import OwnServer, Controller

from argparse import ArgumentParser


if __name__ == "__main__":
    _parser = ArgumentParser()

    _parser.add_argument(
        "server_name", help="Name of this server.",
        type=str, nargs=1,
    )
    _parser.add_argument(
        "servers", help="Other server to sync with.",
        type=str, nargs="+",
    )

    _args = _parser.parse_args()

    server = OwnServer.from_name(_args.server_name[0])
    server.sync(*_args.servers)
    server.listen()
    app = Controller(has_ui=False)
    app.run()
    server.close()
