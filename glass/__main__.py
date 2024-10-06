import click
import os
from dotenv_vault import load_dotenv
import sys
from importlib.metadata import version
import json

from . import project
from . import workspace
from . import standin
from . import util


@click.group()
@click.pass_context
def cli(ctx):
    # Load Config file
    load_dotenv()
    rootFolder = os.getenv("root_path")
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

    ctx.obj = {
        "root": rootFolder, 
        "ids": util.loadIDDict(rootFolder),
        "metafiles": os.getenv("markdown_path"),
        "templatePath": os.getenv("template_path"),
        "storageLocations": storageLocations,
        "revisionLabels": revisionLabels
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
    try: # Find Path that corresponds to ID
        openPath = ctx.obj['ids'][id].path
    
    except KeyError: # If ID Doesn't exist
        # Run the code a second time to allow the background check to find new IDs
        if doReccurance:
            if not jsonOutput and not quiet:
                click.echo("ID is not present in the cached file, regenerating Cache")
            
            util.doBackgroundTasks(ctx.obj['root'], " ".join(sys.argv), version('glass')) # Make the JSON file again
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


    if printPath == False:
        launchSuccess = click.launch(openPath)
        if launchSuccess == 1: # If the folder cannot be launcged
            # If the original ID no longer exists, rerun the command after a new background scan
            util.doBackgroundTasks(ctx.obj['root'], " ".join(sys.argv), version('glass')) # Make the JSON file again
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
        util.doBackgroundTasks(ctx.obj['root'], " ".join(sys.argv), version('glass'))


@cli.command("list")
@click.option("id", "--id")
@click.option("jsonOutput", "--json", default=False, is_flag=True)
@click.pass_context
def listIDs(ctx, id, jsonOutput):
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
                if jsonOutput:
                    titles.append(f"{thisID.idText} - {thisID.descriptor}")
                else:
                    click.echo(f"{'| ' * (idDepth - searchDepth)}{thisID.idText} - {thisID.descriptor}")  
            if thisID.getHigherLevel(idLevels[searchDepth]) == searchID.idText and thisID.idType != "child-project":    
                if jsonOutput:
                    titles.append(f"{thisID.idText} - {thisID.descriptor}")
                else:
                    click.echo(f"{'| ' * (idDepth - searchDepth)}{thisID.idText} - {thisID.descriptor}")  
        except Exception:
            pass 
    
    if jsonOutput:
        click.echo(json.dumps(titles))

# Projects Commands
@cli.group("project")
@click.pass_context
def projectCLI(ctx):
    """Manage Projects tracked by Looking Glass"""
    validProjectsList, invalidProjectsList = project.generateProjectList(ctx.obj['ids'], ctx.obj['metafiles'])
    ctx.obj['projects'] = {"valid": validProjectsList, "invalid": invalidProjectsList}


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