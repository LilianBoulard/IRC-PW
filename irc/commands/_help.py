from argparse import ArgumentParser

from .__base import Command


class Help(Command):

    identifier = "help"
    parameters = []
    _argument_parser = ArgumentParser()

    def client_action(self):
        pass

    def server_action(self) -> str:
        pass
