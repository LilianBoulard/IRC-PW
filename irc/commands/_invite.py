from argparse import ArgumentParser
from .__base import Command


class Invite(Command):
    identifier = "invite"
    _argument_parser = ArgumentParser()
    _argument_parser.add_argument(
        metavar="nickname", required=True, nargs=1, type=str,
        help="The nickname of the user to invite to this channel."
    )

    def client_action(self):
        pass

    def server_action(self) -> str:
        pass
