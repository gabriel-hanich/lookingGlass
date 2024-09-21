import click

# Handle Standin files

@click.command("new")
@click.argument("id")
def newStandIn(id):
    "Create a new Stand in File"
    click.echo("Making Stand In")


@click.command("view")
@click.argument("id")
def viewStandIn(id):
    "View the contents of a stand in file"
    click.echo("Viewing Stand In")


@click.command("modify")
@click.argument("id")
def modifyStandIn(id):
    "Modify Metadata associated with a stand in file"
    click.echo("Modifying Stand In")