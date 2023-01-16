import click
from colorama import Fore
from colorama import init as colorama_init
from art import text2art

from irc import Client, ServerConnection

colorama_init(autoreset=True)


@click.command()
@click.argument("nickname", type=str, nargs=1)
@click.argument("server_name", type=str, nargs=1)
def run_client(nickname: str, server_name: str):
    click.echo("Launching client...")
    client = Client(nickname)
    client.connection = ServerConnection.from_name(server_name)
    client.run()
    click.clear()
    click.echo(f"{Fore.LIGHTBLUE_EX}{text2art('IRC client', font='random')}")
    click.echo(f"Hello {nickname}!")
    while True:
        try:
            command = click.prompt("", type=str, prompt_suffix="").lower()
            client.input(command)
        except KeyboardInterrupt:
            command = "exit"
        if command in ["exit", "quit", "q"]:
            click.echo("Exiting!")
            break


if __name__ == "__main__":
    run_client()
