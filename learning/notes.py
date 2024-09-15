import click
import fileManager
import os
from pathlib import Path
from config import load_config, save_config

@click.group()
@click.pass_context
def cli(ctx: click.Context)->None:
    print("Notes")
    config = load_config()
    notes_directory = config["path"]

    if not os.path.exists(notes_directory):
        os.mkdir(notes_directory)

    ctx.obj = {"notes_directory": notes_directory}


cli.add_command(fileManager.createNewNote)

@cli.group()
def config():
    pass

@config.command()
def create():
    config = load_config()
    save_config(config)
    click.echo("Configuration created")

@config.command()
def show():
    config = load_config()
    click.echo(config)

@config.command()
@click.option("--notes_directory", "-n", type=str)
def update(notes_directory):
    print(notes_directory)
    save_config({"path": notes_directory})