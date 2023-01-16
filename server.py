import click
from colorama import Fore
from colorama import init as colorama_init
from art import text2art

from irc import OwnServer

colorama_init(autoreset=True)


@click.command()
@click.argument("server_name", type=int, nargs=1)
@click.argument("servers", type=list[str], nargs=-1)
def run_server(server_name: str, servers: list[str]):
    click.echo(f"Launching server on hostname:{server_name}...")
    server = OwnServer.from_name(server_name)
    server.sync(*servers)
    server.listen()
    click.clear()
    click.echo(f"{Fore.LIGHTBLUE_EX}{text2art('IRC server', font='random')}")
    while True:
        try:
            command = click.prompt("", type=str, prompt_suffix="").lower()
        except KeyboardInterrupt:
            command = "exit"
        if command in ["exit", "quit", "q"]:
            click.echo("Exiting!")
            break
    server.close()


if __name__ == "__main__":
    run_server()
