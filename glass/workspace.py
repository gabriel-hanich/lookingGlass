import click

# Manage the users workspaces
@click.command("open")
@click.argument("id")
def openWorkspace(id):
    "Open a Workspace"
    click.echo("Opening Workspace")


@click.command("new")
@click.argument("id")
def newWorkspace(id):
    "Create a new Workspace"
    click.echo("Making Workspace")


@click.command("view")
@click.argument("id")
def viewWorkSpace(id):
    "View the metadata associated with a specific Workspace"
    click.echo("Viewing Workspace")


@click.command("modify")
@click.argument("id")
def modifyWorkSpace(id):
    "Modify Metadata associated with a specific Workspace"
    click.echo("Modifying Workspace")