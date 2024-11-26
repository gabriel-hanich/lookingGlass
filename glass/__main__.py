import re
import click
import os
import sys
from importlib.metadata import version
import json
import ctypes

from . import project
from . import standin
from . import util
from . import tools
from . import constants
from . import configmanager

# TODO
# - [X] Come up with better method for managing config stuff
# - [X] Integrate other file systems (A, B, C, D, etc)
# - [X] Ensure --help messages are present & succint (UPTO diagram)
# - [X] Either delete workspace stuff or write it


@click.group()
@click.pass_context
def cli(ctx):
    appConstants = constants.CONSTANTS

    try: 
        idDict = util.loadIDDict(appConstants["root_path"])
    except Exception as e:
        try:
            util.doBackgroundTasks(
                appConstants["root_path"],
                appConstants["markdown_path"],
                appConstants["excluded_folders"],
                " ".join(sys.argv), 
                version('glass'),
            )
        except KeyError:
            configmanager.buildConfig()
            return

    ctx.obj = {
        "root":  appConstants["root_path"], 
        "ids": util.loadIDDict(appConstants["root_path"]),
        "metafiles": appConstants["markdown_path"],
        "templatePath": appConstants["project_template_path"],
        "storageLocations": appConstants["storage_locations"],
        "revisionLabels": appConstants["revision_labels"],
        "excludeDirs": appConstants["excluded_folders"]
    }


@cli.command('open')
@click.argument("id")
@click.option("printPath", "--print", default=False, is_flag=True, help="Will display the path rather then opening it")
@click.option("noBackground", "--no-background", default=False, is_flag=True, help="Disables running the background tasks after the path has been opened")
@click.option("quiet", "--quiet", default=False, is_flag=True, help="Disables printing infromation to the terminal")
@click.option("jsonOutput", "--json", default=False, is_flag=True, help="Returns data in a JSON format")
@click.pass_context
def openID(ctx, id, printPath, noBackground, quiet, jsonOutput, doReccurance=True):
    """Open a specific id"""
    if 'glass://' in id:
        id = id[7:]
        id = id.replace("/", "")
        id = id.replace('"', "")
    
    searchID = util.pathID(id, "", True)
    if searchID.storageLocation == "A":
        try: # Find Path that corresponds to ID
            openPath = ctx.obj['ids'][searchID.numericalID].path
        except KeyError: # If ID Doesn't exist
            # Run the code a second time to allow the background check to find new IDs
            if doReccurance:
                if not jsonOutput and not quiet:
                    click.echo("ID is not present in the cached file, regenerating Cache")
                ctx.invoke(tools.manuallyDoBackgroundTasks)
                ctx.obj['ids'] = util.loadIDDict(ctx.obj['root']) # Load the JSON file into the context again
                
                # Re-run current command with the new context 
                ctx.invoke(openID, id=id, printPath=printPath, quiet=quiet, jsonOutput=jsonOutput, doReccurance=False) 
                return

            else:
                # This runs if the function has been called recursively
                if jsonOutput:
                    click.echo(json.dumps({
                    "status": "failure",
                    "data": "",
                    "reason ": f"{id} is not available within {ctx.obj['root']}"
                    }))
                else:
                    click.echo(f"{id} is not available within {ctx.obj['root']}")
                return
    else:
        try:
            alternateIDs = util.loadIDDict(ctx.obj["root"], searchID.storageLocation)
        except FileNotFoundError:
            if jsonOutput:
                click.echo(json.dumps({
                    "status": "failure",
                    "data": "",
                    "reason ": f"{searchID.storageLocation} is not a tracked storage location in the filesystem"
                    }))
                return
            else:
                raise click.ClickException(f"There is no alternate ID file for the Storage Location provided {searchID.storageLocation}")
        try:
            openPath = alternateIDs[id].path
        except KeyError:
            if jsonOutput:
                click.echo(json.dumps({
                    "status": "failure",
                    "data": "",
                    "reason ": f"{id} is not available within storage drive {searchID.storageLocation}"
                    }))
                return
            else:
                raise click.ClickException(f"The Storage Location {ctx.obj['storageLocations'][searchID.storageLocation]} ({searchID.storageLocation}) does not contain the provided ID")

    if printPath == False and jsonOutput == False:
        if openPath[0:5] == "msg:\\":
            ctypes.windll.user32.MessageBoxW(0, openPath[6:], f"Path for {id}", 0)
            click.echo(openPath[6:])
        else:
            launchSuccess = click.launch(openPath)
            if launchSuccess == 1: # If the folder cannot be launcged
                # If the original ID no longer exists, rerun the command after a new background scan
                ctx.invoke(tools.manuallyDoBackgroundTasks)
                ctx.obj['ids'] = util.loadIDDict(ctx.obj['root']) # Load the JSON file into the context again
            
                # Re-run current command with the new context 
                ctx.invoke(openID, id=id, printPath=printPath, quiet=quiet, jsonOutput=jsonOutput, doReccurance=False) 
            
    elif quiet == False and jsonOutput == False: # Print the path to terminal
        click.echo(openPath)
    elif quiet == False and jsonOutput == True: # Print data to terminal in JSON Format
        click.echo(json.dumps({
            "status": "success",
            "data": openPath,
            "reason ": ""
        }))

    if not noBackground:
        ctx.invoke(tools.manuallyDoBackgroundTasks)


@cli.command("list")
@click.option("id", "--id", help="The parent ID of the IDs to be displayed")
@click.option("jsonOutput", "--json", default=False, is_flag=True, help="Returns the data in a JSON format")
@click.option("quiet", "--quiet", default=False, is_flag=True, help="Will not print anything")
@click.pass_context
def listIDs(ctx, id, jsonOutput, quiet):
    "List all the IDs in the file system"
    idLevels = ['area', 'category', 'subfolder', 'project', 'child-project']
    titles = []
    searchDepth = 0
    idDict = ctx.obj['ids']
    if id != None: 
        searchID = util.pathID(id, "", True)
        idDict = util.loadIDDict(ctx.obj["root"], searchID.storageLocation)
        if searchID.idType == "invalid":
            if len(id) == 1:
                try:
                    idDict = util.loadIDDict(ctx.obj["root"], id)
                    searchDepth = 0
                    id = None
                except FileNotFoundError:
                    raise click.ClickException("The ID you provided points to a storage location that does not exist")
            else:
                raise click.ClickException("The ID provided to the ID flag is invalid")
        else:
            searchDepth = idLevels.index(searchID.idType)
    outputText = ""
    for thisIDText in idDict.keys():
        thisID = idDict[thisIDText]
        idDepth = idLevels.index(thisID.idType)
        # Check if ID within parent ID
        try:
            if id == None and thisID.idType != "child-project":
                titles.append(f"{thisID.idText} - {thisID.descriptor}")
                outputText += f"{'| ' * (idDepth - searchDepth)}{thisID.idText} - {thisID.descriptor}\n"
            if thisID.getHigherLevel(idLevels[searchDepth]) == searchID.numericalID and thisID.idType != "child-project":    
                titles.append(f"{thisID.idText} - {thisID.descriptor}")
                outputText += f"{'| ' * (idDepth - searchDepth)}{thisID.idText} - {thisID.descriptor}\n"  
        except Exception as E:
            pass
    
    if not (jsonOutput or quiet):
        click.echo(outputText)
    if jsonOutput and not quiet:
        click.echo(json.dumps(titles))
    if quiet:
        return {"titles":  titles, "prettyText": outputText}

@cli.command("new")
@click.option("id", "--id", help="The Parent ID for the new ID", prompt=True, default="")
@click.option("title", "--title", prompt=True, type=str, help="The title for the new ID")
@click.option("force", "--force", is_flag=True, default=False, help="Forces the change without asking for confirmation")
@click.pass_context
def createNewID(ctx, id, title, force, doReccurance=True):
    "Generate a new ID and Associated Folder"

    numbers = re.compile("[0-9]")
    if id == "" or (not numbers.match(id[0]) and len(id) == 1):
        parentID = "" # If the user wishes to create a new area
        # Determine number of areas
        childrenCount = 0
        try:
            idDict = util.loadIDDict(ctx.obj["root"], id)
            for idText in idDict:
                if idDict[idText].idType == "area":
                    childrenCount += 1
        except FileNotFoundError:
            # If the storage area doesn't exist, create it new
            util.exportIDlist([], os.path.join(ctx.obj["root"], f".glass/data/IDPaths{id[0]}.json"))
            idDict = util.loadIDDict(ctx.obj["root"], id)



        if childrenCount >= 9:
            raise click.ClickException(f"There are too many Areas within this File system, Cannot create any more")

        newID = f"{id}{childrenCount+1}0"
        newPath = f"{ctx.obj['root']}\{newID} - {title}"
        if not(id == "" or id == "A"): # If the new Area is in the A filesystem
            newPath = click.prompt("Which path should this ID point to?")
            try:
                if title != ctx.obj["ids"][newID[1:]].descriptor:
                    click.echo(
                        click.style(
                            f"The proposed title ({title}) for this ID ({newID}) is not the same as the IDs title in the primary storage location ({ctx.obj['ids'][newID[1:]].descriptor})",
                            fg="yellow"))
                    if click.confirm("Do you want to edit the title?", default=False):
                        title = click.prompt("New Title", default=ctx.obj["ids"][newID[1:]].descriptor)
            except KeyError:
                pass
        if not force:
            click.echo(f"About to create the following")
            click.echo(f"{'ID':<20}| {newID}")
            click.echo(f"{'Title':<20}| {title}")
            click.echo(f"{'path':<20}| {newPath}")
            if not click.confirm("Do you want to continue?", default=True):
                click.echo("Canceled!")
                return
        
        if id == "" or id == "A": # If the new Area is in the primary filesystem
            os.mkdir(newPath)
            click.echo("Created new ID!")
        else:
            idDict[newID] = util.pathID(newID, newPath, True, desc=title)
            newIDList = [idDict[id] for id in idDict.keys()]
            util.exportIDlist(newIDList, os.path.join(ctx.obj["root"], f".glass/data/IDPaths{id}.json"))
            click.echo("Created new ID!")
                
    else:
        try: # Find Path that corresponds to ID
            # If the ID points to an alternative storageLocation
            isPrimaryStorage = True
            idDict = ctx.obj['ids']
            if not numbers.match(id[0]) and id[0] != "A":
                idDict = util.loadIDDict(ctx.obj["root"], id[0])
                isPrimaryStorage = False
            parentID = idDict[id]
        
        except KeyError: # If ID Doesn't exist
            # Run the code a second time to allow the background check to find new IDs
            if doReccurance and isPrimaryStorage:
                click.echo("ID is not present in the cached file, regenerating Cache")
                ctx.invoke(tools.manuallyDoBackgroundTasks)
                ctx.obj['ids'] = util.loadIDDict(ctx.obj['root']) # Load the JSON file into the context again
                
                # Re-run current command with the new context 
                ctx.invoke(createNewID, id=id, title=title, doReccurance=False) 

            else:
                click.echo(f"{id} is not available within storage {id[0]}")
                click.echo(click.style(f'glass new --id "" --title "{title}"', fg="blue"))
                return
            return

        # Find number of child IDs
        childrenCount = 0
        idTypes = ["area", "category", "subfolder", "project", "project-child"]
        for idText in idDict:
            thisID = idDict[idText]
            try:
                if id[1:] == thisID.getHigherLevel(parentID.idType):  # If the ID is a child of the parentID
                    if idTypes.index(thisID.idType) - idTypes.index(parentID.idType) == 1: # If the child ID is a DIRECT child of the parentID
                        childrenCount += 1
            except Exception:
                pass
        
        newID = ""
        if parentID.idType == "area":
            newID = f"{parentID.numericalID[0]}{childrenCount+1}"
            if childrenCount >= 9:
                raise click.ClickException(f"There are too many Categories within this Parent ID, Cannot create any more")
        if parentID.idType == "category":
            if childrenCount >= 99:
                raise click.ClickException(f"There are too many Subfolders within this Parent ID, Cannot create any more")
            newID = f"{parentID.numericalID[0:2]}.{'{:02d}'.format(childrenCount+1)}"

        newPath = f"{parentID.path}\{newID} - {title}"
        if not isPrimaryStorage:
            newPath = click.prompt("What should the path be?")
            newID = id[0] + newID
            try:
                if title != ctx.obj["ids"][newID[1:]].descriptor:
                    click.echo(
                        click.style(
                            f"The proposed title ({title}) for this ID ({newID}) is not the same as the IDs title in the primary storage location ({ctx.obj['ids'][newID[1:]].descriptor})",
                            fg="yellow"))
                    if click.confirm("Do you want to edit the title?", default=False):
                        title = click.prompt("New Title", default=ctx.obj["ids"][newID[1:]].descriptor)
            except KeyError:
                pass


        if not force:
            click.echo(f"About to create the following")
            click.echo(f"{'ID':<20}| {newID}")
            click.echo(f"{'Title':<20}| {title}")
            click.echo(f"{'path':<20}| {newPath}")
            if not click.confirm("Do you want to continue?", default=True):
                click.echo("Canceled!")
                return
        
        if isPrimaryStorage:
            os.mkdir(f"{parentID.path}\{newID} - {title}")
        else:
            idDict[newID] = util.pathID(newID, newPath, True, desc=title)
            newIDList = [idDict[idPath] for idPath in idDict]
            util.exportIDlist(newIDList, os.path.join(ctx.obj["root"], f".glass/data/IDPaths{id[0]}.json"))
        click.echo("Created new ID!")

    ctx.invoke(tools.manuallyDoBackgroundTasks)


@cli.command("modify")
@click.argument("id")
@click.option("parameter", "--parameter", type=click.Choice(['title', 'path'], case_sensitive=False), prompt=True, help="The parameter to be modified")
@click.option("newValue", "--value", type=str, prompt=True, help="The new value for this given parameter")
@click.option("force", "--force", is_flag=True, default=False, help="Force the change without asking for confirmation")
@click.pass_context
def modifyID(ctx, id, parameter, newValue, force):
    "Modify the path or metadata of a specific ID"
    selectedID = util.pathID(id, "", True)
    if selectedID.storageLocation == "A":
        click.echo(click.style("WARNING, the ID you input is within the Primary file system, changes will be overwritten by the background tasks", fg="yellow"))
        idDict = ctx.obj["ids"]
    else:
        try:
            idDict = util.loadIDDict(ctx.obj["root"], selectedID.storageLocation)
        except FileNotFoundError:
            raise click.ClickException(f"The storage location you provided ({selectedID.storageLocation}) does not exist")
    
    try:
        selectedID = idDict[selectedID.idText]
    except KeyError:
        raise click.ClickException(f"The provided ID could not be found in storage {selectedID.storageLocation}")

    if parameter == "title":
        selectedID.descriptor = newValue
    elif parameter == "path":
        selectedID.path = newValue

    if not force:
        click.echo("The new values will be")
        click.echo(f"{'ID':<20}| {selectedID.idText}")
        click.echo(click.style(f"{'Title':<20}| {selectedID.descriptor}", fg=('green' if parameter == 'title' else 'white')))
        click.echo(click.style(f"{'path':<20}| {selectedID.path}", fg=('green' if parameter == 'path' else 'white')))
        if not click.confirm("Do you want to continue?", default=True):
            click.echo("Canceled")
            return
    idDict[id] = selectedID
    newIDList = [idDict[id] for id in idDict.keys()]
    util.exportIDlist(newIDList, os.path.join(ctx.obj["root"], f".glass/data/IDPaths{selectedID.storageLocation}.json"))
    click.echo("Completed!")

# Projects Commands
@cli.group("project")
@click.pass_context
def projectCLI(ctx):
    """Manage Projects tracked by Looking Glass"""
    # Generate list of projects 
    projList = [pair[1] for pair in ctx.obj['ids'].items()]
    validProjectsList, invalidProjectsList = project.generateProjectList(projList, ctx.obj['metafiles'])
    ctx.obj['projects'] = {"valid": validProjectsList, "invalid": invalidProjectsList}


cli.add_command(tools.generateMermaidDiagram)
cli.add_command(tools.manuallyDoBackgroundTasks)
cli.add_command(tools.generateMetaData)
cli.add_command(tools.duplicateStorage)
cli.add_command(tools.printAbout)

projectCLI.add_command(project.viewProj)
projectCLI.add_command(project.newProj)
projectCLI.add_command(project.repairProj)

@cli.group("standin")
def standInCLI():
    """Manage Stand In Files in the file system"""
    

standInCLI.add_command(standin.newStandIn)
standInCLI.add_command(standin.modifyStandIn)
standInCLI.add_command(standin.viewStandIn)
standInCLI.add_command(standin.openStandIn)

@cli.group()
def config():
    """Manage App Config"""

config.add_command(configmanager.viewConfig)
config.add_command(configmanager.modifyConfig)
config.add_command(configmanager.buildConfig)

if __name__ == '__main__':
    cli()