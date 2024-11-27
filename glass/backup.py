from datetime import datetime
from importlib.metadata import version
import json
import os
import click
from . import drivemanager
import glass.__main__ as main
import hashlib
import time


@click.command("encode")
@click.option("drive", "--drive", type=str, help="The ID of the drive where this backup will be Stored", default="A")
@click.option("single", "--single", is_flag=True, help="Disables the creation of a local record of the backup in drive A")
@click.pass_context
def generateMetaData(ctx, drive, single):
    "Generates a file that can be used to track changes"
    titles = ctx.invoke(main.listIDs, quiet=True, jsonOutput=False)
    m = hashlib.sha256()
    m.update(str.encode(" ".join(titles["titles"])))
    titleHash = m.hexdigest()
    fileData = {
        "generated": time.time(),
        "version": version("glass"),
        "id_count": len(ctx.obj["ids"]),
        "fileHash": str(titleHash),
        "drive": drive,
        "filesystem": titles["titles"]
    }

    with open(f"{ctx.obj['root']}/identifier.json", "w") as outputFile:
        json.dump(fileData, outputFile, indent=2)

    if not single:
        try:
            open(f"{ctx.obj['root']}/.glass/backups/{drive}{datetime.now().strftime('%Y-%m-%d')}.json", "r")
            click.echo(click.style("WARNING, a backup file with todays date already exists for that drive, do you wish to continue? (This will override the existing backup file)", fg='red'))
            if not click.confirm("Continue?"):
                return
        except FileNotFoundError:
            pass
        with open(f"{ctx.obj['root']}/.glass/backups/{drive}{datetime.now().strftime('%Y-%m-%d')}.json", "w") as outputFile:
            json.dump(fileData, outputFile, indent=2)

    click.echo(f"Generated File Hash at {ctx.obj['root']}/identifier.json")
    click.echo(f"You can now export the file system to drive {drive}")

@click.command("view")
@click.pass_context
def viewBackups(ctx):
    "View a list of all the backups tracked locally"
    ctx.obj['drives'] = drivemanager.loadDrives(ctx.obj["root"])

    backupFiles = list(os.listdir(ctx.obj['root'] + "/.glass/backups"))
    click.echo(click.style(f"There are {len(backupFiles)} backups tracked in the filesystem", fg='blue'))
    click.echo(f"{'Drive':<20} | {'Drive Name':<20} | {'Date':<20} | {'Number of IDs':<20} | {'Path':<20}")
    click.echo(f"{'-'*21}|{'-'*22}|{'-'*22}|{'-'*22}|{'-'*21}")
    for backup in backupFiles:
        path = f"{ctx.obj['root']}/.glass/backups/{backup}"
        with open(path, 'r') as backupFile:
            data = json.load(backupFile)
        generatedDate = datetime.fromtimestamp(data['generated'])
        try:
            click.echo(f"{data['drive']:<20} | {ctx.obj['drives'][data['drive']]['label']:<20} | {generatedDate.strftime('%H:%M %d/%m/%Y'):<20} | {data['id_count']:<20} | {path:<20}")
        except KeyError:
            click.echo(f"{data['drive']:<20} | {'UNREGISTERED DRIVE':<20} | {generatedDate.strftime('%H:%M %d/%m/%Y'):<20} | {data['id_count']:<20} | {path:<20}")