from .__base import Command


class Help(Command):
    identifier = "help"
    arguments = []

    def action(self) -> str:
        pass
