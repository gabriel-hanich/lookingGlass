import click
from click_prompt import auto_complete_option

@click.group()
def cli():
    print("Hello world")

noteTypes = ["essay", "report", "video", "note"]


@click.command()
@auto_complete_option("--item", "-i", type=click.Choice(noteTypes))
def orderItem(item):
    click.echo(f"You registered a {item}")

cli.add_command(orderItem)

if __name__ == "__main__":
    cli()