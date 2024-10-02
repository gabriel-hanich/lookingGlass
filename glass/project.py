import click
# from . import util UNCOMMENT THIS FOR THE CLI 
import util as util
import os
from datetime import datetime

class Project:
    def __init__(self, id:util.pathID, metaFilePath, doValidation=True, **kwargs) -> None:
        self.id = id
        self.metaFilePath = metaFilePath
        self.isValid = True
        self.descriptor = ""

        self.properties = kwargs.get("projectProperties", {})

        if doValidation:
            self.isValid, self.descriptor = self.validate()
        


    def validate(self):
        # Validate that all the data is normal and stuff
        # Ensure Meta path exists
        if not os.path.isfile(self.metaFilePath):
            return [False, f"The meta file located at {self.metaFilePath} does not exist"]
        
        # Ensure meta path points to .md file
        if not self.metaFilePath[-3:] == ".md":
            return [False, f"The meta file located at {self.metaFilePath} is not a Markdown file"]
        
        # Load data from the file
        try:
            self.properties = readFileProperties(self.metaFilePath)
            if self.properties["glassID"] != self.id.getHigherLevel("project"):
                return [False, f"The ID present in the file indicates "]

        except KeyError as exception:
            return [False, f"The metafile located at {self.metaFilePath} does not have the necessary information in the file properties. It is missing a value for {exception}"]
        return [True, ""]
    
    def updateFile(self, propertyKey, newPropertyValue):
        # Change the value of a given property
        # Updates the metadata file AND the local dictionary 
        
        self.properties[propertyKey] == newPropertyValue
        with open(self.metaFilePath, "r") as metaFile:
            oldLines = metaFile.readlines()

        newLines = []
        withinProperties = False
        for line in oldLines:
            thisLine = line
            if "---" in line:
                withinProperties = not withinProperties

            if f"{propertyKey}:" in line and withinProperties:
                if type(newPropertyValue) == bool:
                    if newPropertyValue == True:
                        thisLine = f'{propertyKey}: true\n'
                    else:
                        thisLine = f'{propertyKey}: false\n'

                elif type(newPropertyValue) == int:
                    thisLine = f'{propertyKey}: "{newPropertyValue}"\n'
                elif type(newPropertyValue) == datetime:
                    thisLine = f'{propertyKey}: {newPropertyValue.strftime("%Y-%m-%d")}\n'
                else:
                    thisLine = f"{propertyKey}: {newPropertyValue}\n"
            
            newLines.append(thisLine)
        
        with open(self.metaFilePath, "w") as metaFile:
            metaFile.writelines(newLines)

        return

def readFileProperties(metaFilePath):
    # Read the Properties of an Obsidian markdown file 
    with open(metaFilePath, "r") as metaFile:
        fileLines = metaFile.readlines()

    withinProperties = False
    data = {}
    for line in fileLines:
        line = line.strip()
        if line == "---":
            withinProperties = not withinProperties

        if withinProperties and ":" in line:
            keyPair = line.split(":")

            if len(keyPair) > 2:
                keyPair[1] = ":".join(keyPair[1:])

            key, value = keyPair[0], keyPair[1][1:]
            key.strip()
            value.strip()
            data[key] = value
    return data

# Manage the users projects
@click.command("new")
@click.argument("id")
def newProj(id):
    "Create a new Project"
    click.echo("Making Project")


@click.command("view")
@click.argument("id")
def viewProj(id):
    "View the metadata associated with a specific project"
    click.echo("Viewing Project")


@click.command("modify")
@click.argument("id")
def modifyProj(id):
    "Modify Metadata associated with a specific project"
    click.echo("Modifying project")


if __name__ == "__main__":
    projID = util.pathID(
        "21.01.02",
        "PATH",
        True
    )
    testProj =Project(
        projID,
        "PATH",
        True
    )

    testProj.updateFile("revision-number", 1)