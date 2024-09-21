import click
from . import project
from . import workspace
from . import standin

@click.group()
def cli():
    click.echo("LOAD IDs")
    pass

@cli.command('open')
def openID():
    """Open a specific id"""
    click.echo("OPENING ID")


# Projects Commands
@cli.group("project")
def projectCLI():
    """Manage Projects tracked by Looking Glass"""
    click.echo("LOAD Projs")


projectCLI.add_command(project.viewProj)
projectCLI.add_command(project.modifyProj)
projectCLI.add_command(project.newProj)


@cli.group("workspace")
def workspaceCLI():
    """Open/Manage Workspaces tracked by Looking Glass"""
    click.echo("LOAD Workspace")

workspaceCLI.add_command(workspace.openWorkspace)
workspaceCLI.add_command(workspace.newWorkspace)
workspaceCLI.add_command(workspace.modifyWorkSpace)
workspaceCLI.add_command(workspace.viewWorkSpace)

@cli.group("standin")
def standInCLI():
    """Manage Stand In Files in the file system"""
    click.echo("LOAD Workspace")

standInCLI.add_command(standin.newStandIn)
standInCLI.add_command(standin.modifyStandIn)
standInCLI.add_command(standin.viewStandIn)

@cli.group()
def config():
    """Modify App Config"""
    click.echo("LOAD Workspace")



if __name__ == '__main__':
    cli()