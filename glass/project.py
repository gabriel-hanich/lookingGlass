import click

# Manage the users projects

@click.command("new")
@click.argument("id")
def newProj(id):
    "Create a new Project"
    click.echo("Making Project")


@click.command("view")
@click.argument("id")
def viewProj(id):
    "View the metadata associated with a specific project"
    click.echo("Viewing Project")


@click.command("modify")
@click.argument("id")
def modifyProj(id):
    "Modify Metadata associated with a specific project"
    click.echo("Modifying project")