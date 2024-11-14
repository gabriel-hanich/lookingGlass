from importlib.metadata import version
import json
import sys
import click
from . import util
import time
import os

class StandInFile:
    def __init__(self, filePath, existingFile, **kwargs):
        self.filePath = filePath
        self.title = kwargs.get("title", "")
        self.description = kwargs.get("description", "")
        self.url = kwargs.get("url", "")
        self.people = kwargs.get("people", [])
        self.created = time.time()
        self.fileVersion = kwargs.get("version", "")

        if existingFile:
            self.loadData()

    def loadData(self):
        with open(self.filePath, "r") as glassFile:
            fileData = json.load(glassFile)
            self.title = fileData['title'] 
            self.description = fileData['description'] 
            self.url = fileData['url'] 
            self.people = fileData['people'] 
            self.created = fileData['created'] 
            self.fileVersion = fileData['glass_version'] 

    def createFile(self):
        with open(self.filePath, "w") as glassFile:
            data = {
                "title": self.title,
                "description": self.description,
                "url": self.url,
                "people": self.people,
                "created": self.created,
                "glass_version": self.fileVersion
            }
            json.dump(data, glassFile, indent=2)

    def open(self):
        click.launch(self.url)

def getStandIns(path):
    # Gets a list of all the standins within a specific path
    standIns = []
    for filePath in os.listdir(path):
        abs_path = os.path.abspath(os.path.join(path, filePath))
        if filePath[-6:] == ".glass":
            standIns.append(StandInFile(abs_path, True))

    return standIns



# Handle Standin files
@click.command("new")
@click.argument("id")
@click.option("title", "--title", type=str, prompt=True)
@click.option("description", "--description", type=str, prompt=True)
@click.option("url", "--path", type=str, prompt=True)
@click.option("people", "--people", type=str, prompt=True, default="me")
@click.pass_context
def newStandIn(ctx, id, title, description, url, people, doReccurance=True):
    "Create a new Stand in File"
    # Ensure the ID exists in the filesystem
    try:
        parentID = ctx.obj["ids"][id]
    except KeyError:
        # If the ID does not exist in the cache, regenerate cache to double check
        if doReccurance:
            util.doBackgroundTasks(
                ctx.obj['root'],
                ctx.obj['metafiles'],
                ctx.obj['excludeDirs'],
                " ".join(sys.argv), 
                version('glass'),
            )
            ctx.obj['ids'] = util.loadIDDict(ctx.obj['root']) # Load the JSON file into the context again
            # Re-run current command with the new context 
            ctx.invoke(newStandIn, id=id, title=title, path=url, people=people, doReccurance=False) 
            return
        else:
            # Runs if the ID really doesn't exist
            click.echo(f"The ID {id} does not exist on the file directory, try the command again with a new id")
            click.echo(click.style(f'glass standin new [ID] --title "{title}" --description "{description}" --path "{url}" --people "{people}"', fg='blue'))
            return

    # Ensure another standin doesn't have the same title
    for otherFile in getStandIns(parentID.path):
        if otherFile.title == title:
            click.echo(f"ERROR, A standin File at this location has the same title")
            click.echo(f"File is located at {otherFile.filePath}")
            click.echo(click.style(f'glass standin new "{id}" --path "{url}" --description "{description}" --people "{people}" --title ""', fg="blue"))
            return
    
    # Actually make the file now
    newFile = StandInFile(
        f"{parentID.path}/{title}.glass", 
        False,
        title=title,
        description=description,
        url=url,
        people=people,
        version=version('glass')
        )
    newFile.createFile()


@click.command("view")
@click.argument("id")
def viewStandIn(id):
    "View the contents of a stand in file"
    click.echo("Viewing Stand In")


@click.command("modify")
@click.argument("id")
def modifyStandIn(id):
    "Modify Metadata associated with a stand in file"
    click.echo("Modifying Stand In")

@click.command("open")
@click.argument("path")
def openStandIn(path):
    thisFile = StandInFile(path, True)
    thisFile.open()