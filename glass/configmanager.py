from importlib.metadata import version
import click
from . import constants
import json

@click.command("view")
@click.option("doJson", "--json", is_flag=True, default=False)
@click.pass_context
def viewConfig(ctx, doJson):
    "View the config"
    vals = constants.CONSTANTS
    if not doJson:
        click.echo("Glass Application Config")
        click.echo(f"{'App Version':<21} | {version('glass')}")
        click.echo(f"{'Root Path':<21} | {vals['root_path']}")
        click.echo(f"{'Project Metadata Path':<21} | {vals['markdown_path']}")
        click.echo(f"{'Project Template Path':<21} | {vals['project_template_path']}")
        click.echo(f"{'Excluded Folders':<21} | {', '.join(vals['excluded_folders'])}")
    if doJson:
        click.echo(json.dumps(vals))

# @click.command("modify")
#TODO 