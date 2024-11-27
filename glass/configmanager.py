from importlib.metadata import version
import os
import time
import click
from . import constants
import json

configKeys = ["root", "meta", "template", "excluded"]
keyLabels = {"root": "root_path", "meta":"markdown_path", "template": "project_template_path", "excluded": "excluded_folders"}

@click.command("view")
@click.option("doJson", "--json", is_flag=True, default=False, help="Returns the data in a JSON format rather then human-readable")
@click.pass_context
def viewConfig(ctx, doJson):
    "View the config values"
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

@click.command("modify")
@click.argument("key", type=click.Choice(configKeys))
@click.argument("newval", type=str)
@click.option("force", "--force", is_flag=True, default=False, help="Will force the change without asking for confirmation")
@click.option("doJson", "--json", is_flag=True, default=False, help="Backend flag (don't use)")
@click.pass_context
def modifyConfig(ctx, key, newval, force, doJson):
    "Modify key-value pair of app config"
    newval = newval.replace("\\", "/")
    actualKey = keyLabels[key]

    if not force:
        click.echo(f"About to update value {key}")
        click.echo(f"From {click.style(constants.CONSTANTS[actualKey], fg='blue')} to {click.style(newval, fg='blue')}")
        if not click.confirm("Are you sure?"):
            click.echo("Canceled")
            return
    

    if not doJson:
        with open(f"{__file__.replace('configmanager.py', '')}constants.py", "w") as configFile:
            constantsDict = constants.CONSTANTS
            constantsDict[actualKey] = newval

            if key == "excluded":
                constantsDict["excluded_folders"] = constantsDict["excluded_folders"].split(",")

                newExcludedFolders = []
                for val in constantsDict["excluded_folders"]:
                    newExcludedFolders.append(val.strip().lower())
                constantsDict["excluded_folders"] = newExcludedFolders

            configFile.write("CONSTANTS = {\n")
            for subKey in constantsDict:
                if subKey == "excluded_folders":
                    configFile.write(f'    "{subKey}": {constantsDict[subKey]},\n')
                elif subKey == "storage_locations" or subKey == "revision_labels":
                    configFile.write(f'    "{subKey}": {constantsDict[subKey]},\n')
                else:
                    configFile.write(f'    "{subKey}": "{constantsDict[subKey]}",\n')
            configFile.write("}")
        click.echo("Completed")
    else:
        return {"key": actualKey, "value": newval}

@click.command("build")
@click.pass_context
def buildConfig(ctx):
    "Generate a new Config File from Scratch"
    descriptions = {
        "root": "The path to the root directory of the filesystem", 
        "meta": "The path to the Obsidian Projects Folder, All metafiles will be created at this path", 
        "template": "The path to the template file for an Obsidian Project", 
        "excluded": "A list of folder names that are to be excluded"

    }
    click.echo("Welcome to Looking Glass, Please setup a few configuration variables")
    dataDict = {}
    for key in configKeys:
        click.echo(f"{click.style(key, fg='blue')} - {descriptions[key]}")
        newValue = click.prompt("What should this value be?", type=str)
        newValue = newValue.replace("\\", "/")
        dataDict[keyLabels[key]] = newValue

    click.echo("\n")
    click.echo(f"{'Attribute':<20} | {'Value':<20}")
    click.echo(f"{'-'*21}+{'-'*21}")
    for key in configKeys:
        click.echo(f"{key:<20} | {dataDict[keyLabels[key]]}")
    
    dataDict["storage_locations"] = {'A': 'Main Drive', 'B': 'Google Drive', 'C': 'Supernote'}
    dataDict["revision_labels"] = {'A': 'planning', 'B': 'working-document', 'C': 'editing', 'D': 'submission'}
    dataDict["excluded_folders"] = dataDict["excluded_folders"].split(",")

    newExcludedFolders = []
    for val in dataDict["excluded_folders"]:
        newExcludedFolders.append(val.strip().lower())
    dataDict["excluded_folders"] = newExcludedFolders

    if not click.confirm("Are you happy with these values"):
        click.echo("Canceled")
        return
    
    # Write the config settings to configManager
    with open(f"{__file__.replace('configmanager.py', '')}constants.py", "w") as configFile:
        configFile.write("CONSTANTS = {\n")
        for subKey in dataDict.keys():
            if subKey == "excluded_folders":
                configFile.write(f'    "{subKey}": {dataDict[subKey]},\n')
            elif subKey == "storage_locations" or subKey == "revision_labels":
                configFile.write(f'    "{subKey}": {dataDict[subKey]},\n')
            else:
                configFile.write(f'    "{subKey}": "{dataDict[subKey]}",\n')
        configFile.write("}")

    # Create the necessary files into the .glass folder
    os.mkdir(f"{dataDict['root_path']}/.glass")
    os.mkdir(f"{dataDict['root_path']}/.glass/data")
    os.mkdir(f"{dataDict['root_path']}/.glass/backups")
    os.mkdir(f"{dataDict['root_path']}/.glass/logs")


    driveData = {
        "generated": time.time(),
        "version": version('glass'),
        "drives": [
            {
                "letter": "A",
                "label": "Local Storage",
                "path": dataDict['root_path']
            }
        ]
    }
    with open(f"{dataDict['root_path']}/.glass/data/drives.json", "w") as driveFile:
        json.dump(driveData, driveFile)

    click.echo("Completed")