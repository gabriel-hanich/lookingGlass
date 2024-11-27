import json
import click

from . import tools
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
            if self.properties["meta-override"] not in ["true", "false"]:
                return [False, f"The meta-override value is not 'true' or 'false'. Value is '{self.properties['meta-override']}'"]
        except KeyError as exception:
            return [False, f"The metafile located at {self.metaFilePath} does not have the necessary information in the file properties. It is missing a value for {exception}"]
        return [True, ""]
    
    def updateMetaFileRevisions(self):
        # Update the meta file to reflect new revision
        try:
            modified = False
            if self.properties["meta-override"] != "true":
                if self.properties["revision-stage"].replace("-", " ") != self.revisionStages[self.id.revisionStage]:
                    self.modifyPair("revision-stage", self.revisionStages[self.id.revisionStage].replace(" ", "-"))
                    modified = True
                if self.properties["revision-number"].replace('"', '') != str(self.id.revision) and self.id.revision != -1:
                    self.modifyPair("revision-number", self.id.revision)
                    modified = True
                return modified
        except KeyError:
            return False
    
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

def generateMetaFile(metaRoot, templatePath, id, title, revisionStage, revisionNumber, dueDate, className, imageURL, command=""):
    metaPath = metaRoot + "/" + title + ".md"
    if os.path.isfile(metaPath):
        click.echo(click.style(command, fg="blue"))
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
                line = f"time: {datetime.now().strftime('%I:%m %p').lower()}\n" 
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

def readProjectsFileSystem(logFile, metaPath, IDList):
    # Read the File System to find the most recent revision of each project and update metadata file
    indent = " "*1
    logFile.write(f"{datetime.now().isoformat()}{indent}BEGIN Loading Projects\n")
    indent = " "*3
    
    validProjects, invalidProjects = generateProjectList(IDList, metaPath)
    logFile.write(f"{datetime.now().isoformat()}{indent}INFO found {len(validProjects)} valid Projects\n")
    
    # Write Invalid Projects
    if len(invalidProjects) != 0:
        logFile.write(f"{datetime.now().isoformat()}{indent}WARN found {len(invalidProjects)} invalid Projects\n")
        indent = " "*5
        for invalidProj in invalidProjects:
            logFile.write(f"{datetime.now().isoformat()}{indent}WARN {invalidProj.id.path} is invalid because {invalidProj.descriptor}\n")

    indent = " "*3
    logFile.write(f"{datetime.now().isoformat()}{indent}INFO Updating metafiles\n")
    modifiedMetaList = []
    for proj in validProjects:
        if proj.updateMetaFileRevisions(): # Returns true if the meta file is updated
            modifiedMetaList.append(proj.metaFilePath)
    
    # Write list of meta files that are updated
    logFile.write(f"{datetime.now().isoformat()}{indent}INFO Updated {len(modifiedMetaList)} metafiles\n")
    indent = " "*5
    for metaFile in modifiedMetaList:
        logFile.write(f"{datetime.now().isoformat()}{indent}INFO Modified {metaFile}\n")

    indent = " "*1
    logFile.write(f"{datetime.now().isoformat()}{indent}END Loading Projects\n")

# Manage the users projects
@click.command("new")
@click.argument("id")
@click.option("title", "--title", type=str, prompt=True, help="The title of the project")
@click.option("revisionStage", "--revision-stage", default="planning", type=click.Choice(revisionStages), prompt=True, help="The project's current Revision Stage")
@click.option("revisionNumber", "--revision-number", default=1, type=int, prompt=True, help="The current revision stage of the project")
@click.option("dueDate", "--due-date", type=click.DateTime(formats=["%d/%m/%Y"]), prompt=True, help="When the project is due to be submitted")
@click.option("className", "--class", type=str, prompt=True, default="", help="The class associated with the project")
@click.option("imageURL", "--image", type=str, prompt=True, default="", help="A link to the project's thumbnail")
@click.option("noSideCar", "--no-sidecar", default=False, is_flag=True, help="Disables the creation of a sidecar file")
@click.option("noInput", "--no-input", default=False, is_flag=True, help="Removes any input fields")
@click.pass_context
def newProj(ctx, id, title, revisionStage, revisionNumber, dueDate, className, imageURL, noSideCar, noInput):
    "Create a new Project"

    commandStr = f'glass project new {id} --title "{title}" --revision-stage "{revisionStage}" --revision-number "{revisionNumber}" '
    commandStr += f'--due-date "{dueDate.strftime("%d/%m/%Y")}" --class "{className}" --image "{imageURL}"'

    if noSideCar:
        commandStr += " --no-sidecar"
    if noInput:
        commandStr += " --no-input"

    # Get Metadata
    # Ensure the provided ID is a valid Project ID
    testID = util.pathID(id, "", True)
    if testID.idType != "project":
        if testID.idType != "subfolder":
            click.echo(click.style(commandStr, fg="blue"))
            raise click.ClickException(f"The provided ID is not a Project or Subfolder")
        
        # If the user has supplied a subfolder ID, create a new project within that subfolder
        projectsCount = 0
        for project in ctx.obj['projects']['valid'] + ctx.obj['projects']['invalid']:
            if project.id.getHigherLevel("subfolder") == id:
                projectsCount += 1
        
        id = f"{id}.{str(projectsCount+1).zfill(2)}"


    if not testID.getHigherLevel("subfolder") in ctx.obj['ids'].keys():
        click.echo(click.style(commandStr, fg="blue"))
        raise click.ClickException(f"The provided ID does not have a corresponding subfolder")

    # Ensure the project ID does not already exist
    for project in ctx.obj['projects']['valid']:
        if project.id.idText == id:
            ctx.invoke(tools.manuallyDoBackgroundTasks)
            click.echo(click.style(commandStr, fg="blue"))
            raise click.ClickException(f"This ID already exists at {project.id.path}")

    newProject = True
    # Check if Project exists but is invalid
    for project in ctx.obj['projects']['invalid']:
        if project.id.idText == id and project.metaFilePath == "":
            newProject = False
            break

    subfolderID = ctx.obj['ids'][testID.getHigherLevel("subfolder")]
    folderPath = f"{subfolderID.path}\\{id} - {title}"

    if not noInput:
        if newProject:
            click.echo("About to create a project with attributes")
        else:
            click.echo("An invalid Project already exists with that ID, creating a Metafile with the following properties")
        
        click.echo(f"{'ID':<20}| {id}")
        click.echo(f"{'title':<20}| {title}")
        click.echo(f"{'Revision Stage':<20}| {revisionStage}")
        click.echo(f"{'Revision Number':<20}| {revisionNumber}")
        click.echo(f"{'Due Date':<20}| {dueDate}")
        click.echo(f"{'Path':<20}| {folderPath}")
        
        
        if not click.confirm("Confirm", default=True):
            return

    # Only make a new directory if the project is new
    if newProject:
        try:
            os.mkdir(folderPath)
        except FileExistsError:
            click.echo(click.style(commandStr, fg="blue"))
            raise click.ClickException(f"There is already a folder at {folderPath}")

    generateMetaFile(
        ctx.obj["metafiles"], 
        ctx.obj["templatePath"], 
        util.pathID(id, "", True),
        title, 
        revisionStage, 
        revisionNumber, 
        dueDate, 
        className,
        imageURL,
        command=commandStr
    )

    # Do Background Tasks to add newly created project to the stack
    ctx.invoke(tools.manuallyDoBackgroundTasks)

    return

@click.command("view")
@click.argument("id")
@click.option("jsonOutput", "--json", is_flag=True, default=False, help="Returns the data in a JSON format")
@click.pass_context
def viewProj(ctx, id, jsonOutput):
    "View the metadata associated with a specific project"
    selectedProj = ""
    for project in ctx.obj["projects"]["valid"] + ctx.obj["projects"]["invalid"]:
        if project.id.idText == id:
            selectedProj = project
            break

    if selectedProj == "":
        click.echo(f"ERROR, Could not find a project with id {id}\nUse glass list to generate a list of all valid IDs")
        return
    
    attributes = ['title', 'date', 'time', 'class', 'due-date', 'revision-stage', 'revision-number', 'submitted']

    if not jsonOutput:
        click.echo(f"{'ID':<20}| {selectedProj.id.idText}")
        for attr in attributes:
            try:
                click.echo(f"{attr:<20}| {selectedProj.properties[attr]}")
            except KeyError:
                click.echo(f"{attr:<20}| EMPTY")

        click.echo(f"{'Folder Path':<20}| {selectedProj.id.path}")
        click.echo(f"{'Meta File Path':<20}| {selectedProj.metaFilePath}")
        return
    
    data = {
        'id': selectedProj.id.idText,
        'path': selectedProj.id.path,
        'metapath': selectedProj.metaFilePath,
        'properties': selectedProj.properties
        }
    click.echo(json.dumps({
                "status": "success",
                "data": data,
                "reason ": ""
            }))


@click.command("repair")
@click.argument("id")
@click.option("noInput", "--no-input", default=False, is_flag=True, help="Forces the changes without asking for confirmation")
@click.pass_context
def repairProj(ctx, id, noInput):
    "Repair/Create the Metafile for a given project"
    thisProj = False
    for proj in ctx.obj["projects"]["valid"] + ctx.obj["projects"]["invalid"]:
        if proj.id.idText == id:
            thisProj = proj

    if thisProj == False:
        click.echo(f"The ID {id} does not exist in the filesystem")
        return
    
    if thisProj.metaFilePath == "":
        # If there isn't an existing metafile for the project
        click.echo("This project does not have an existing metafile")
        if not click.confirm("Do you want to generate a new one?", default=True):
            return

        generateMetaFile(
            ctx.obj["metafiles"], 
            ctx.obj["templatePath"], 
            util.pathID(id, "", True),
            thisProj.id.descriptor, 
            thisProj.revisionStages[thisProj.id.revisionStage].replace(" ", "-"), 
            thisProj.id.revision, 
            datetime.today(), 
            "",
            ""
        )

    if thisProj.metaFilePath != "":
        # If the project already has a metafile but is missing some properties

        # Get the ideal set of property keys
        vals = {
            'title': thisProj.id.descriptor,
            'date': datetime.today().strftime('%d/%M/%Y'),
            'type': 'project',
            'time': datetime.now().strftime('%H:%m %p').lower(),
            'class': '',
            'image': '',
            'due-date': '',
            'revision-stage': thisProj.revisionStages[thisProj.id.revisionStage].replace(" ", "-"),
            'revision-number': thisProj.id.revision,
            'submitted': False, 
            'grade': '',
            'glassID': id,
            'meta-override': False
        }
        templateProperties = readFileProperties(ctx.obj["templatePath"])
        projKeys = list(thisProj.properties.keys())
        keysToAdd = {}
        for key in templateProperties.keys():
            if key not in projKeys:
                keysToAdd[key] = vals[key]

        # Update Meta file to include the keys
        if len(keysToAdd.keys()) == 0:
            click.echo("There are no missing metafile properties in the project's metafile")
            return

        if not noInput:
            click.echo(f"The file {thisProj.metaFilePath} will be modified to include the following")
            for key in keysToAdd.keys():
                click.echo(f"{key:<20}| {keysToAdd[key]}")
                
            if not click.confirm("Do you wish to continue?", default=True):
                return

        with open(thisProj.metaFilePath, "r") as metaFile:
            lines = metaFile.readlines()
            fileLines = []
            foundPropertyStart = False
            addedData = False
            for lineIndex, line in enumerate(lines):
                if line.strip() == "---" and foundPropertyStart == True and addedData == False:
                    for key in keysToAdd.keys():
                        fileLines.append(f"{key}: {keysToAdd[key]}\n")
                    addedData = True


                if line.strip() == "---" and foundPropertyStart == False:
                    foundPropertyStart = True

                fileLines.append(line)
        
        with open(thisProj.metaFilePath, "w") as metaFile:
            metaFile.write("".join(fileLines))
