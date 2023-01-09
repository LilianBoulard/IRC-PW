from argparse import ArgumentParser
from .__base import Command


class Invite(Command):
    identifier = "invite"
    argument_parser = ArgumentParser()
    argument_parser.add_argument(
        metavar="nickname", required=True, nargs=1, type=str,
        help="The nickname of the user to invite to this channel."
    )

    def action(self) -> str:
        pass
