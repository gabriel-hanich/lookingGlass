import click
import os
import sys
from importlib.metadata import version
import json

from . import project
from . import workspace
from . import standin
from . import util
from . import tools


@click.group()
@click.pass_context
def cli(ctx):
    
    excludeDirs = [".glass", "vault"] # List of folders which will be Excluded from the indexation process

    storageLocations = {
        "A": "Main Drive",
        "B": "Google Drive",
        "C": "Supernote"
    }
    revisionLabels = {
        "A": "planning",
        "B": "working-document",
        "C": "editing",
        "D": "submission"
    }


    try: 
        idDict = util.loadIDDict(rootFolder)
    except Exception:
        ctx.invoke(tools.manuallyDoBackgroundTasks)

    ctx.obj = {
        "root": rootFolder, 
        "ids": util.loadIDDict(rootFolder),
        "metafiles": markdownPath,
        "templatePath": templatePath,
        "storageLocations": storageLocations,
        "revisionLabels": revisionLabels,
        "excludeDirs": excludeDirs
    }


@cli.command('open')
@click.argument("id")
@click.option("printPath", "--print", default=False, is_flag=True)
@click.option("noBackground", "--no-background", default=False, is_flag=True)
@click.option("quiet", "--quiet", default=False, is_flag=True)
@click.option("jsonOutput", "--json", default=False, is_flag=True)
@click.pass_context
def openID(ctx, id, printPath, noBackground, quiet, jsonOutput, doReccurance=True):
    """Open a specific id"""
    if 'glass://' in id:
        id = id[7:]
        id = id.replace("/", "")
        id = id.replace('"', "")

    try: # Find Path that corresponds to ID
        openPath = ctx.obj['ids'][id].path
    
    except KeyError: # If ID Doesn't exist
        # Run the code a second time to allow the background check to find new IDs
        if doReccurance:
            if not jsonOutput and not quiet:
                click.echo("ID is not present in the cached file, regenerating Cache")
            ctx.invoke(tools.manuallyDoBackgroundTasks)
            ctx.obj['ids'] = util.loadIDDict(ctx.obj['root']) # Load the JSON file into the context again
            
            # Re-run current command with the new context 
            ctx.invoke(openID, id=id, printPath=printPath, quiet=quiet, jsonOutput=jsonOutput, doReccurance=False) 

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


    if printPath == False and jsonOutput == False:
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
            "data": ctx.obj['root'],
            "reason ": ""
        }))

    if not noBackground:
        ctx.invoke(tools.manuallyDoBackgroundTasks)


@cli.command("list")
@click.option("id", "--id")
@click.option("jsonOutput", "--json", default=False, is_flag=True)
@click.option("quiet", "--quiet", default=False, is_flag=True)
@click.pass_context
def listIDs(ctx, id, jsonOutput, quiet):
    idLevels = ['area', 'category', 'subfolder', 'project', 'child-project']
    titles = []
    searchDepth = 0
    if id != None: 
        searchID = util.pathID(id, "", True)
        if searchID.idType == "invalid":
            raise Exception("The ID provided to the ID flag is invalid")
        searchDepth = idLevels.index(searchID.idType)
        

    idsList = ctx.obj['ids'].keys()
    for thisIDText in idsList:
        thisID = ctx.obj['ids'][thisIDText]
        idDepth = idLevels.index(thisID.idType)
        # Check if ID within parent ID
        try:
            if id == None and thisID.idType != "child-project":
                if jsonOutput or quiet:
                    titles.append(f"{thisID.idText} - {thisID.descriptor}")
                else:
                    click.echo(f"{'| ' * (idDepth - searchDepth)}{thisID.idText} - {thisID.descriptor}")  
            if thisID.getHigherLevel(idLevels[searchDepth]) == searchID.idText and thisID.idType != "child-project":    
                if jsonOutput or quiet:
                    titles.append(f"{thisID.idText} - {thisID.descriptor}")
                else:
                    click.echo(f"{'| ' * (idDepth - searchDepth)}{thisID.idText} - {thisID.descriptor}")  
        except Exception:
            pass 
    
    if jsonOutput:
        click.echo(json.dumps(titles))

    if quiet:
        return titles

@click.command("new")
@click.option("id", "--id", help="The Parent ID for the new ID", prompt=True, default="")
@click.option("title", "--title", prompt=True, type=str)
@click.option("force", "--force", is_flag=True, default=False)
@click.pass_context
def createNewID(ctx, id, title, force, doReccurance=True):
    "Generate a new ID and associated folder based on a provided PARENT ID"

    if id == "":
        parentID = "" # If the user wishes to create a new area

        # Determine number of areas
        childrenCount = 0
        for idText in ctx.obj['ids']:
            if ctx.obj['ids'][idText].idType == "area":
                childrenCount += 1

        if childrenCount >= 9:
            raise click.ClickException(f"There are too many Areas within this File system, Cannot create any more")

        newID = f"{childrenCount}0"
        if not force:
            click.echo(f"About to create ID {newID}")
            click.echo(f"Path {ctx.obj['root']}\{newID} - {title}")
            if not click.confirm("Do you want to continue?", default=True):
                click.echo("Canceled!")
                return
        
        os.mkdir(f"{ctx.obj['root']}\{newID} - {title}")
        click.echo("Created new ID!")

    else:
        try: # Find Path that corresponds to ID
            parentID = ctx.obj['ids'][id]
        
        except KeyError: # If ID Doesn't exist
            # Run the code a second time to allow the background check to find new IDs
            if doReccurance:
                click.echo("ID is not present in the cached file, regenerating Cache")
                ctx.invoke(tools.manuallyDoBackgroundTasks)
                ctx.obj['ids'] = util.loadIDDict(ctx.obj['root']) # Load the JSON file into the context again
                
                # Re-run current command with the new context 
                ctx.invoke(createNewID, id=id, title=title, doReccurance=False) 

            else:
                click.echo(f"{id} is not available within {ctx.obj['root']}")
                click.echo(click.style(f'glass new --id "" --title "{title}"', fg="blue"))
            return

        # Find number of child IDs
        childrenCount = 0
        idTypes = ["area", "category", "subfolder", "project", "project-child"]
        for idText in ctx.obj['ids']:
            thisID = ctx.obj['ids'][idText]
            try:
                if id == thisID.getHigherLevel(parentID.idType):  # If the ID is a child of the parentID
                    if idTypes.index(thisID.idType) - idTypes.index(parentID.idType) == 1: # If the child ID is a DIRECT child of the parentID
                        childrenCount += 1
            except Exception:
                pass
        
        newID = ""
        click.echo(childrenCount)
        if parentID.idType == "area":
            newID = f"{parentID.idText[0]}{childrenCount+1}"
            if childrenCount >= 9:
                raise click.ClickException(f"There are too many Categories within this Parent ID, Cannot create any more")
        if parentID.idType == "category":
            if childrenCount >= 99:
                raise click.ClickException(f"There are too many Subfolders within this Parent ID, Cannot create any more")
            newID = f"{parentID.idText[0:2]}.{'{:02d}'.format(childrenCount+1)}"

        if not force:
            click.echo(f"About to create ID {newID}")
            click.echo(f"Path {parentID.path}\{newID} - {title}")
            if not click.confirm("Do you want to continue?", default=True):
                click.echo("Canceled!")
                return
        
        os.mkdir(f"{parentID.path}\{newID} - {title}")
        click.echo("Created new ID!")

    ctx.invoke(tools.manuallyDoBackgroundTasks)

    



cli.add_command(createNewID)

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

projectCLI.add_command(project.viewProj)
projectCLI.add_command(project.newProj)
projectCLI.add_command(project.repairProj)


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
    

standInCLI.add_command(standin.newStandIn)
standInCLI.add_command(standin.modifyStandIn)
standInCLI.add_command(standin.viewStandIn)
standInCLI.add_command(standin.openStandIn)

@cli.group()
def config():
    """Modify App Config"""
    click.echo("LOAD Workspace")



if __name__ == '__main__':
    cli()