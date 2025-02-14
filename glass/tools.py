import os
import glass.__main__ as main
from . import drivemanager
from importlib.metadata import version
import sys
import click
import glass.util as util

@click.command("diagram")
@click.option("storageLocation", "--storage", type=str, default="A", help="The filestorage location that will be scanned (default=A)")
@click.option("includeProjects", "--projects", is_flag=True, default=False, help="Includes projects within the diagram")
@click.pass_context
def generateMermaidDiagram(ctx, includeProjects, storageLocation):
    "Generates a diagram in the syntax of Mermaid.JS of your file tree"
    idDict = ctx.obj["ids"]
    if storageLocation != "A":
        try:
            idDict = util.loadIDDict(ctx.obj["root"], storageLocation)
        except FileNotFoundError:
            raise click.ClickException(f"The provided Storage Location ({storageLocation}) does not exist")

    mermaidStr = "graph TD;\n"
    levels = ["area","category", "subfolder"]
    if includeProjects:
        levels.append("project")
    mermaidIds = {}
    a = 0
    for level in levels:
        for pathID in idDict:
            if idDict[pathID].idType == level:
                mermaidIds[idDict[pathID].numericalID] = f"id{a}" 
                mermaidStr += f"id{a}({idDict[pathID].descriptor})\n" 
                a += 1

    for pathID in idDict:
        thisID = idDict[pathID]
        if thisID.idType not in ["area", "child-project"]:
            if (thisID.idType == "project") and includeProjects:
                parentID = thisID.getHigherLevel(levels[levels.index(thisID.idType)-1])
                mermaidStr += f"{mermaidIds[parentID]}-->{mermaidIds[thisID.numericalID]}\n"
            elif thisID.idType != "project":
                parentID = thisID.getHigherLevel(levels[levels.index(thisID.idType)-1])
                mermaidStr += f"{mermaidIds[parentID]}-->{mermaidIds[thisID.numericalID]}\n"

    click.echo(mermaidStr)

@click.command("bg")
@click.pass_context
def manuallyDoBackgroundTasks(ctx):
    "Manually perform the background tasks"
    util.doBackgroundTasks(
            ctx.obj['root'],
            ctx.obj['metafiles'],
            ctx.obj['excludeDirs'],
            " ".join(sys.argv), 
            version('glass'),
        )
    

@click.command("duplicate")
@click.argument("parentstorage")
@click.argument("childstorage")
@click.option("preserve", "--preserve", is_flag=True, help="Preserves the paths from the parent", default=False)
@click.pass_context
def duplicateStorage(ctx, parentstorage, childstorage, preserve):
    """Duplicate the ID structure from the parent storage to child"""
    
    # Ensure both the parent and the child storage have been registered already
    ctx.obj["drives"] = drivemanager.loadDrives(ctx.obj["root"])
    missingStorage = ""
    if parentstorage not in ctx.obj["drives"].keys():
        missingStorage = "Parent"
    if childstorage not in ctx.obj["drives"].keys():
        missingStorage = "Child"

    if missingStorage != "":
        click.echo(click.style(f"WARNING, The {missingStorage} Storage ({parentstorage if missingStorage == 'Parent' else childstorage}) isn't registered in the app", fg="red"))
        click.echo("You can register it using " + click.style(f"glass drive new {parentstorage if missingStorage == 'Parent' else childstorage} [LABEL] [PATH]", fg="blue"))
        if not click.confirm("Do you want to continue?"):
            click.echo("Canceled")
            return


    if parentstorage == "A":
        parentDict = ctx.obj["ids"]
    else:
        try:
            parentDict = util.loadIDDict(ctx.obj["root"], parentstorage)
        except FileNotFoundError:
            raise click.ClickException(f"The Parent Storage ({parentstorage}) does not exist")

    if childstorage == "A":
        childDict = ctx.obj["ids"]
    else:
        try:
            childDict = util.loadIDDict(ctx.obj["root"], childstorage)
        except FileNotFoundError:
            # If the child  ID file does not exist, create it
            util.exportIDlist([], os.path.join(ctx.obj["root"], f".glass/data/IDPaths{childstorage}.json"))
            childDict = util.loadIDDict(ctx.obj["root"], childstorage)

    modifiedIDs = 0
    for parentText in parentDict.keys():
        parentID = parentDict[parentText]
        try:
            childID = childDict[f"{childstorage}{parentID.numericalID}"]
        except KeyError:
            # If the ID is in the parent storage but not the child
            childID = util.pathID(f"{childstorage}{parentID.numericalID}", parentID.path, True)
            childID.descriptor = parentID.descriptor
            if preserve:
                click.echo(f"Transferring ID {parentID.numericalID}")
                childID.path = parentID.path
                childDict[childID.idText] = childID
            else:
                click.echo(f"\n{'Attr':<20} | {'Parent':<20} | {'Child':<20}")
                click.echo(f"{'-'*21}|{'-'*22}|{'-'*21}")
                click.echo(f"{'ID':<20} | {parentID.idText:<20} | {childID.idText:<20}")
                click.echo(f"{'Descriptor':<20} | {parentID.descriptor:<20} | {childID.descriptor:<20}")
                click.echo(f"Given that the parent ID has a path that points to\n{parentID.path}")
                childID.path = click.prompt("What should the child ID point to?", type=str)
                if childID.path.lower() != "pass":
                    childDict[childID.idText] = childID
                    childIDList = [childDict[idPath] for idPath in childDict]
                    util.exportIDlist(childIDList, os.path.join(ctx.obj["root"], f".glass/data/IDPaths{childstorage}.json"))
            modifiedIDs += 1
    
    if preserve:
        if click.confirm(f"Do you want to bring {modifiedIDs} to the Storage Location {childstorage}", default=False):
            childIDList = [childDict[idPath] for idPath in childDict]
            util.exportIDlist(childIDList, os.path.join(ctx.obj["root"], f".glass/data/IDPaths{childstorage}.json"))
            click.echo("Completed!")
        else:
            click.echo("Canceled")

@click.command("about")
def printAbout():
    "Print Information about Looking Glass"
    logoStr = """
888                       888      d8b                         .d8888b.  888                            
888                       888      Y8P                        d88P  Y88b 888                            
888                       888                                 888    888 888                            
888      .d88b.   .d88b.  888  888 888 88888b.   .d88b.       888        888  8888b.  .d8888b  .d8888b  
888     d88""88b d88""88b 888 .88P 888 888 "88b d88P"88b      888  88888 888     "88b 88K      88K      
888     888  888 888  888 888888K  888 888  888 888  888      888    888 888 .d888888 "Y8888b. "Y8888b. 
888     Y88..88P Y88..88P 888 "88b 888 888  888 Y88b 888      Y88b  d88P 888 888  888      X88      X88 
88888888 "Y88P"   "Y88P"  888  888 888 888  888  "Y88888       "Y8888P88 888 "Y888888  88888P'  88888P' 
                                                     888                                                
                                                Y8b d88P                                                
                                                 "Y88P"                                                 
    """
    click.echo(click.style(logoStr, fg="bright_blue", bg="black"))
    click.echo(click.style(f"Looking Glass Version {version('glass')}", fg="blue"))
    click.echo("Developed by Gabriel Hanich, 2024")
    click.echo("Source Code Available at https://github.com/gabriel-hanich/lookingGlass/")
    click.echo(f"Files located at {__file__}")
    click.echo("run " + click.style("glass config build", fg='blue') + " to Initialise the application")

