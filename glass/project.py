import click
from . import util
import os
from datetime import datetime
import sys
from importlib.metadata import version

revisionStages = ["planning", "working-document", "editing", "submission"]

class Project:
    def __init__(self, id:util.pathID, metaFilePath:str, childIDs, doValidation=True, **kwargs) -> None:
        self.id = id
        self.metaFilePath = metaFilePath
        self.childIDs = childIDs
        self.isValid = True
        self.descriptor = ""

        self.properties = kwargs.get("projectProperties", {})

        if doValidation:
            self.isValid, self.descriptor = self.validate()
        
        self.revisionStages = {"A": "planning", "B": "working paper", "C": "editing", "D": "submission"}
        self.revisionLetters = {"planning": "A", "working paper": "B", "editing": "C", "submission": "D"}

    def validate(self):
        # Validate that all the data is normal and stuff
        # TODO Double check childIDs list is valid
        # Ensure Meta path exists
        if not os.path.isfile(self.metaFilePath):
            if self.metaFilePath == "":
                return [False, f"There was no connected metafile in the markdown path"]
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
    
    def updateMetaFileRevisions(self):
        # Update the meta file to reflect new revision
        modified = False
        if self.properties["revision-stage"].replace("-", " ") != self.revisionStages[self.id.revisionStage]:
            self.modifyPair("revision-stage", self.revisionStages[self.id.revisionStage].replace(" ", "-"))
            modified = True
        if self.properties["revision-number"].replace('"', '') != str(self.id.revision) and self.id.revision != -1:
            self.modifyPair("revision-number", self.id.revision)
            modified = True
        return modified
    
    def modifyPair(self, propertyKey, newPropertyValue):
        # Change the value of a given property
        # Updates the metadata file AND the local dictionary 
        self.properties[propertyKey] = newPropertyValue
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
                    thisLine = f'{propertyKey}: {newPropertyValue}\n'
                elif type(newPropertyValue) == datetime:
                    thisLine = f'{propertyKey}: {newPropertyValue.strftime("%Y-%m-%d")}\n'
                else:
                    thisLine = f"{propertyKey}: {newPropertyValue}\n"
            
            newLines.append(thisLine)
        
        # Adjust the subheadings to track the new revisions
        if propertyKey == "revision-number":
            foundsubheading = False
            revStage = self.properties['revision-stage'].replace('-', ' ')
        
            # Get all the subheadings within the subheading for the revision
            for lineIndex, line in enumerate(newLines):
                if line.count("#") == 3: # If the line is a H3
                    foundsubheading = False 
                if f"### {revStage}" in line.strip().lower(): # If the line is the desired H3
                    foundsubheading = True
                
                # If a subheading for the current revision already exists in the meta file
                if foundsubheading and f"#### {self.revisionLetters[revStage]}{newPropertyValue}" in line:
                    break

                # If the loop reaches the end of the loop and discovers the next revision stage
                if foundsubheading and newLines[lineIndex+1].count("#") == 3:
                    newLines.insert(lineIndex+1, f"#### {self.revisionLetters[revStage]}{newPropertyValue} - {datetime.today().strftime('%Y-%m-%d')}\n")
                    break
                    


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

def generateProjectList(idList, metaFilePath):
    # Generates a list of Projects based on their IDs
    projectIDs = [thisId for thisId in idList if thisId.idType == "project"]
    
    # Get list of all the metafiles
    metaFiles = {}
    for (dirpath, dirNames, fileNames) in os.walk(metaFilePath):
        for fileName in fileNames:
            if(fileName[-3:] == ".md"):
                fileProperties = readFileProperties(dirpath + "/" + fileName)
                try:
                    if fileProperties["type"] == "project":
                        metaFiles[fileProperties["glassID"]] = dirpath + "/" + fileName
                except Exception:
                    pass
    
    projects = []
    for projectID in projectIDs:
        # Find Child IDs
        childIDs = []
        for child in idList:
            if child.idText[:8] == projectID.numericalID and child != projectID.numericalID:
                childIDs.append(child)
        
        try:
            projects.append(Project(projectID, metaFiles[projectID.numericalID.strip()], childIDs))
        except KeyError as E:
            # If there is no metafile
            projects.append(Project(projectID, "", childIDs))

    validIDs = [project for project in projects if project.isValid]
    invalidIDs = [project for project in projects if not project.isValid]

    return validIDs, invalidIDs

def generateMetaFile(metaRoot, templatePath, id, title, revisionStage, revisionNumber, dueDate, className, imageURL):
    metaPath = metaRoot + "/" + title + ".md"
    if os.path.isfile(metaPath):
        raise click.ClickException(f"A metafile with this title already exists at {metaPath}")

    # Read template
    with open(templatePath, "r") as templateFile:
        templateLines = templateFile.readlines()

    with open(metaPath, "w") as metaFile:
        for line in templateLines:
            # TODO Make this less god awful
            if "title:" in line:
                line = f"title: {title}\n"
            elif "date:" in line and "due-date:" not in line:
                line = f"date: {datetime.now().strftime('%Y-%m-%d')}\n" 
            elif "time:" in line:
                line = f"time: {datetime.now().strftime('%H:%m %p').lower()}\n" 
            elif "class:" in line:
                line = f"class: {className}\n"
            elif "image:" in line:
                line = f"image: {imageURL}\n"
            elif "due-date:" in line:
                line = f"due-date: {dueDate.strftime('%Y-%m-%d')}\n"
            elif "revision-stage:" in line:
                line = f"revision-stage: {revisionStage.replace(' ', '-')}\n"
            elif "revision-number:" in line:
                line = f'revision-number: {revisionNumber}\n'
            elif "glassID:" in line:
                line = f'glassID: {id.idText}\n'
            elif line == "[Glass URI](glass://)\n":
                line = f"[Glass URI](glass://{id.idText})\n"
            elif "# {{Title}}" in line:
                line = f"# {title}\n"

            metaFile.write(line)

    return

# Manage the users projects
@click.command("new")
@click.argument("id")
@click.option("title", "--title", type=str, prompt=True)
@click.option("revisionStage", "--revision-stage", default="planning", type=click.Choice(revisionStages), prompt=True)
@click.option("revisionNumber", "--revision-number", default=1, type=int, prompt=True)
@click.option("dueDate", "--due-date", type=click.DateTime(formats=["%d/%m/%Y"]), prompt=True)
@click.option("className", "--class", type=str, prompt=True, default="")
@click.option("imageURL", "--image", type=str, prompt=True, default="")
@click.option("noSideCar", "--no-sidecar", default=False, is_flag=True)
@click.option("noInput", "--no-input", default=False, is_flag=True)
@click.pass_context
def newProj(ctx, id, title, revisionStage, revisionNumber, dueDate, className, imageURL, noSideCar, noInput):
    "Create a new Project"
    # Ensure the provided ID is a valid Project ID
    testID = util.pathID(id, "", True)
    if testID.idType != "project":
        raise click.ClickException(f"The provided ID is not a project")

    if not testID.getHigherLevel("subfolder") in ctx.obj['ids'].keys():
        raise click.ClickException(f"The provided ID does not have a corresponding subfolder")
    
    # Ensure the project ID does not already exist
    for project in ctx.obj['projects']['valid'] + ctx.obj['projects']['invalid']:
        if project.id.idText == id:
            util.doBackgroundTasks(ctx.obj['root'], " ".join(sys.argv), version('glass'))
            raise click.ClickException(f"This ID already exists at {project.id.path}")

    subfolderID = ctx.obj['ids'][testID.getHigherLevel("subfolder")]
    folderPath = f"{subfolderID.path}\\{id} - {title}"

    if not noInput:
        click.echo("About to create a project with attributes")
        
        click.echo(f"{'title':<20}| {title}")
        click.echo(f"{'Revision Stage':<20}| {revisionStage}")
        click.echo(f"{'Revision Number':<20}| {revisionNumber}")
        click.echo(f"{'Due Date':<20}| {dueDate}")
        click.echo(f"{'Path':<20}| {folderPath}")
        
        
        if not click.confirm("Confirm", default=True):
            return

    os.mkdir(folderPath)
    generateMetaFile(
        ctx.obj["metafiles"], 
        ctx.obj["templatePath"], 
        testID,
        title, 
        revisionStage, 
        revisionNumber, 
        dueDate, 
        className,
        imageURL
    )

    # Do Background Tasks to add newly created project to the stack
    util.doBackgroundTasks(ctx.obj['root'], " ".join(sys.argv), version('glass'))

    return

@click.command("view")
@click.argument("id")
@click.pass_context
def viewProj(ctx, id):

    "View the metadata associated with a specific project"
    click.echo("Viewing Project")


@click.command("modify")
@click.argument("id")
def modifyProj(id):
    "Modify Metadata associated with a specific project"
    click.echo("Modifying project")


