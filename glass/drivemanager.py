from importlib.metadata import version
import json
import time
import click

# Load the drives and their labels from the JSON file
def loadDrives(rootPath):
    driveData = {}
    with open(f"{rootPath}/.glass/data/drives.json", "r") as driveFile:
        fileData = json.load(driveFile)
        for drive in fileData['drives']:
            driveData[drive['letter']] = drive
    return driveData

def writeDrives(rootPath, driveList):
    driveData = {
        "generated": time.time(),
        "version": version('glass'),
        "drives": driveList
    }
    with open(f"{rootPath}/.glass/data/drives.json", "w") as driveFile:
        json.dump(driveData, driveFile, indent=2)

@click.command("new")
@click.argument("letter")
@click.argument("label")
@click.argument("path")
@click.option("force", "--force", is_flag=True, help="Forces the change without confirming anything", default=False)
@click.pass_context
def newDrive(ctx, letter, label, path, force):
    """Registers a new drive into the system"""
    letter = letter.upper()

    commandStr = f'glass drive new {letter} "{label}"'
    if force:
        commandStr += " --force"
    
    # Ensure the provided letter is valid
    if len(letter) != 1:
        click.echo(click.style(commandStr, fg='blue'))
        raise click.ClickException("The letter you provided does not have a length of 1")

    # Ensure the drive letter does not already exist
    ctx.obj['drives'] = loadDrives(ctx.obj['root'])
    try:
        existingDrive = ctx.obj['drives'][letter]
        click.echo("Run " + click.style(f"glass modify {letter} name {label}", fg='blue') + " to Modify the drive's name to the provided value")
        raise click.ClickException(f"Drive '{existingDrive['label']}' already has letter {letter}")
    except KeyError:
        pass # This means there isn't a drive with the given letter

    if not force:
        click.echo("About to create the following drive")
        click.echo(f"{'Letter':<10} | {letter}")
        click.echo(f"{'Label':<10} | {label}")
        click.echo(f"{'Path':<10} | {path}")
        if not click.confirm("Do you want to continue?"):
            return

    ctx.obj['drives'][letter] = {
            "letter": letter,
            "label": label,
            "path": path
        }
    
    dList = [ctx.obj['drives'][thisLetter] for thisLetter in ctx.obj['drives'].keys()]
    writeDrives(ctx.obj["root"], dList)
    click.echo("Registered the Drive!")
    
@click.command("modify")
@click.argument("letter")
@click.argument("key", type=click.Choice(["label", "path"]))
@click.argument("newval", type=str)
@click.option("force", "--force", is_flag=True, help="Forces the change without requesting confirmation", default=False)
@click.pass_context
def modifyDriveData(ctx, letter, key, newval, force):
    """Modify a Value associated with a specific key"""
    letter = letter.upper()

    commandStr = f'glass drive modify {letter} {key} "{newval}"'
    if force:
        commandStr += " --force"
    
    # Ensure the provided letter is valid
    if len(letter) != 1:
        click.echo(click.style(commandStr, fg='blue'))
        raise click.ClickException("The letter you provided does not have a length of 1")

    # Ensure the drive letter already exists
    ctx.obj['drives'] = loadDrives(ctx.obj['root'])
    if letter not in ctx.obj["drives"].keys():
        raise click.ClickException(f"The provided letter ({letter}) does not exist\nRun " + click.style(f"glass drive new {letter}", fg='blue') + " to make a new Drive")

    ctx.obj['drives'][letter][key] = newval

    if not force:
        click.echo(f"Modifying Drive {letter}")
        click.echo(f"{'Letter':<10} | {letter}")
        click.echo(click.style(f"{'Label':<10} | {ctx.obj['drives'][letter]['label']}", fg=('green' if key == 'label' else 'white')))
        click.echo(click.style(f"{'Path':<10} | {ctx.obj['drives'][letter]['path']}", fg=('green' if key == 'path' else 'white')))
        if not click.confirm("Do you want to continue?"):
            return
        
    dList = [ctx.obj['drives'][thisLetter] for thisLetter in ctx.obj['drives'].keys()]
    writeDrives(ctx.obj["root"], dList)
    click.echo("Successfully Modified the Drive!")

@click.command("view")
@click.pass_context
def viewDrives(ctx):
    "View the tracked storage drives"
    ctx.obj["drives"] = loadDrives(ctx.obj["root"])
    click.echo(f"{'Letter':<10} | {'Label':<20} | {'Path':<20}")
    click.echo(f"{'-'*11}|{'-'*22}|{'-'*21}")
    for driveLetter in ctx.obj["drives"].keys():
        thisDrive = ctx.obj["drives"][driveLetter]
        click.echo(f"{thisDrive['letter']:<10} | {thisDrive['label']:<20} | {thisDrive['path']:<20}")

