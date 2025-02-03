import os
import re
import json
from datetime import datetime
import time

import click
from . import project

class pathID:
    def __init__(self, idString, path, doValidation, **kwargs):
        self.path = path.replace("/", "\\") # The path to the folder 
        self.idText = idString # The ID itself
        self.idType = kwargs.get("idType", "invalid") # The type of Id
        self.numericalID = kwargs.get("numericalID", "") # The type of Id

        self.descriptor = kwargs.get("desc", "")

        self.storageLocation = kwargs.get("storage", "A")

        self.revision = kwargs.get("revision", -1) # The current revision (only applicable if it's a project) 
        self.revisionStage = kwargs.get("revisionStage", "A")

        self.levelDict = {"area": 0, "category": 1, "subfolder": 2, "project": 3, "child-project": 4}

        if doValidation:
            self.detectIDContext()
            if self.idType != "invalid":
                correctPath = self.validatePath()
                if not correctPath['validPath']:
                    self.idType = 'invalid'
                    self.descriptor = correctPath['desc']

    def detectIDContext(self):
        # Determine the level of the ID (area, catergory, subfolder, project or invalid)
        numbers = re.compile("[0-9]")
        self.numericalID = self.idText
        
        if len(self.idText) < 2:
            self.idType = "invalid"
            self.descriptor = "ID is too short"
            return

        if not numbers.match(self.idText):
            # If the first letter of the ID points to a different storage location
            self.storageLocation = self.idText[0]
            self.numericalID = self.idText[1:]

        idDepth = self.numericalID.count(".")
        if idDepth == 0:
            # It's either an area or a subject
            if numbers.match(self.numericalID[0]) and self.numericalID[1] == "0":
                # Area IDs have a non-zero first digit and a zero second digit
                self.idType = "area"
            elif numbers.match(self.numericalID[1]):
                # Category Have A non-zero second digit and any first digit
                self.idType = "category"
            else:
                # Return an error if the first 2 digits of the ID are chars instead of digits (Except for storage letter)
                self.idType = "invalid"
                if not numbers.match(self.numericalID[0]):
                    self.descriptor = "This ID does not have a number for the Area"
                elif not numbers.match(self.numericalID[1]):
                    self.descriptor = "This ID does not have a number for the Category"
                return
        
        elif idDepth == 1:
            # It's a subfolder
            try:
                int(self.idText[-2:])
                self.idType = "subfolder"
            except ValueError:
                self.idType = "invalid"
                self.descriptor = "The Subfolder ID contains characters"
                return
        else:
            # It's a project
            self.idType = "project"

            # The project ID contains all characters after the 3rd period
            projectID = ""
            for index, item in enumerate(self.idText.split(".")):
                if index >= 2:
                    projectID += "." + item

            projectID = projectID[1:]
            
            
            try:
                # The ID has no characters, and hence no revisions
                int(projectID)
            except ValueError:
                # If the ID has revision 
                if (not numbers.match(projectID[-2])) and numbers.match(projectID[-1]):
                    self.revisionStage = self.idText[-2]
                    self.revision = int(self.idText[-1])
                    self.idType = "child-project"
                else:
                    self.idType = "invalid"
                    self.descriptor = "Invalid Project ID, Either you have a 2 digit version number or no Revision Letter"
        
    def validatePath(self):
        # Ensure the path (as read from the file name) matches the folder it is within
        splitPath = self.path.split("\\")
        rootIndex = -1 # The index in the list of the root folder
        levels = list(self.levelDict.keys())
        for pathIndex, pathSection in enumerate(splitPath):
            if " - " in pathSection:
                if rootIndex == -1:
                    rootIndex = pathIndex

                levelIndex = pathIndex - rootIndex
                if levelIndex <= 3:
                    if not pathSection.split(' - ')[0] == self.getHigherLevel(levels[levelIndex]):
                        return {
                            "validPath": False, 
                            "desc": (f"There is a mismatch in the path. "
                                     f"The object has {levels[levelIndex]} ID {self.getHigherLevel(levels[levelIndex])} "
                                     f"but the path indicates it has ID {pathSection.split(' - ')[0]}"),
                            "path": self.path
                        }
       
        return {"validPath": True, "desc": "Correct Path", "path": self.path}

    def getHigherLevel(self, level):
       # Get the ID of the level specified that this pathID falls within
        if self.idType == "invalid":
            raise Exception(f"Error, Cannot get the higher level ID of an invalid ID")
        if self.levelDict[self.idType] < self.levelDict[level]:
            raise Exception(f"Error, Cannot find the {level} of an ID at level {self.idType}")
        
        if level == "area":
            return f"{self.numericalID[0]}0"
        if level == "category":
            return f"{self.numericalID[0:2]}"
        if level == "subfolder":
            return f"{self.numericalID[0:5]}"
        if level == "project":
            return f"{self.numericalID[0:8]}"

    def display(self, storageLabels, revisionLabels):
        # Display the PathID in a human-readable format
        print(f"ID: {self.idText}")
        print(f"Desc: {self.descriptor}")
        print(f"Type: {self.idType}")
        if self.idType == "invalid":
            return
        
        print(f"Stored: {storageLabels[self.storageLocation]}")
        if self.idType == "project":
            print(f"Revision-Stage: {revisionLabels[self.revisionStage]}")
            print(f"Revision: {self.revision}")
   

def generateIDList(fsPath, excludedList):
    # Checks to find all the IDs in the root directory and subfolders
    # Does not search within folders in the excluded list
    # TODO Maybe recursion?

    # Searches for the children of each ID, going down a level each time
    IDList, invalidIDList = getSubIDs(fsPath, excludedList)
    for IDType in ["area", "category", "subfolder", "project", "project-child"]:
        for itemID in IDList:
            if itemID.idType == IDType:
                validIDs, invalidIDs = getSubIDs(itemID.path, excludedList, itemID)
                IDList = IDList + validIDs

                # Paths with subfolders cannot be invalid
                if IDType != "subfolder":
                    invalidIDList = invalidIDList + invalidIDs

    IDList = assignRevisions(IDList)

    return IDList, invalidIDList

def getSubIDs(fsPath, excludedList, parentID=None):
    # Find all subIDs in a path
    dirStructure = os.scandir(fsPath)
    ids, invalidIDs = [], []
    for folder in dirStructure:
        try:
            endText = folder.path.split("\\")[-1]
            if endText.lower() not in excludedList:
                idText, desc = endText.split(" - ")

                # If the parentID is a project, then the folder may only contain the revision letter
                # Hence, append the ID of the parent to flesh it out
                if parentID != None:
                    if parentID.idType == "project" and len(idText) == 2:
                        idText = parentID.idText + idText

                thisID = pathID(idText, folder.path, doValidation=True, desc=desc)
                if thisID.idType != "invalid":
                    ids.append(thisID)
                else:
                    invalidIDs.append(thisID)
        except ValueError:
            if endText.lower() not in excludedList:
                thisID = pathID("", folder.path, doValidation=False, desc="Invalid Folder Name, no discernible ID")
                invalidIDs.append(thisID)
    
    return ids, invalidIDs

def exportIDlist(IDList, outputPath):
    # Exports all the IDs to a .json file
    # TODO Fix issue w/ the paths in the json containing a mix of / and \\
    # TODO Implement a better sorting method for projects (i.e aware of current revision)

    IDList.sort(key=lambda x: x.numericalID)
    outputDict = {"metaData": {"createdUTC": round(time.time())}, "IDs": {}}
    for exportID in IDList:
        outputDict["IDs"][exportID.idText] = {
            "numericalID": exportID.numericalID,
            "path": exportID.path,
            "type": exportID.idType,
            "descriptor": exportID.descriptor,
            "storageLocation": exportID.storageLocation,
            "revisionStage": exportID.revisionStage,
            "revisionCount": exportID.revision
        }
    
    with open(f"{outputPath}", "w", encoding="utf-8") as outputFile:
        json.dump(outputDict, outputFile, indent=4)

def loadIDDict(rootPath, storageLabel=""):
    IDDict = {}
    if storageLabel == "A":
        storageLabel = ""
    with open(os.path.join(rootPath, f".glass/data/IDPaths{storageLabel}.json"), "r", encoding="utf-8") as IDFile:
        rawData = json.load(IDFile)
        
        for key in rawData["IDs"].keys():
            thisID = rawData["IDs"][key]
            IDDict[key] = pathID(
                    key,
                    thisID["path"],
                    False,
                    idType=thisID["type"],
                    numericalID=thisID["numericalID"],
                    desc=thisID["descriptor"],
                    storage=thisID["storageLocation"],
                    revision=thisID["revisionCount"],
                    revisionStage=thisID["revisionStage"]
                )
    
    
    return IDDict

def assignRevisions(idList):
    # Determine the revision of every project based on it's child IDs
    for thisID in idList:
        if thisID.idType == "project" and thisID.revision == -1:
            childIDs = []
            for subID in idList:
                try:
                    if subID.getHigherLevel("project") == thisID.numericalID.strip() and subID.revision != -1:
                        childIDs.append(subID)
                except Exception:
                    pass
            
            childIDs.sort(key=lambda x: x.numericalID)

            try:
                thisID.revision = childIDs[-1].revision
                thisID.revisionStage = childIDs[-1].revisionStage
            except IndexError:
                # If there are no children for the ID
                pass
    
    return idList

def readFileSystem(logFile, rootPath, excludedList):
    # Reads the files from the file system and save paths to each ID
    indent = " "
    logFile.write(f"{datetime.now().isoformat()}{indent}BEGIN Loading IDs\n")

    indent = " "*3
    IDList, invalidIDList = generateIDList(rootPath, excludedList)
    logFile.write(f"{datetime.now().isoformat()}{indent}INFO found {len(IDList)} valid IDs\n")

     # Detect if any IDs are the same
    scannedIDs = []
    equalIDs = []
    for thisID in IDList:
        if thisID.idText in scannedIDs:
            equalIDs.append([thisID, IDList[scannedIDs.index(thisID.idText)]])
        scannedIDs.append(thisID.idText)
    
    
    # Write Warning about Equivalent IDs
    if len(equalIDs) != 0:
        logFile.write(f"{datetime.now().isoformat()}{indent}WARN found {len(equalIDs)} equal IDs\n")
        indent = " "*5
        for copiedID in equalIDs:
            logFile.write(f"{datetime.now().isoformat()}{indent}WARN {copiedID[0].path} and {copiedID[1].path} have an equivalent ID\n")

    indent = " "*3
    # Write warning about invalid IDs
    if len(invalidIDList) != 0:
        logFile.write(f"{datetime.now().isoformat()}{indent}WARN found {len(invalidIDList)} invalid IDs\n")
        indent = " "*5
        for invalidID in invalidIDList:
            logFile.write(f"{datetime.now().isoformat()}{indent}WARN {invalidID.path} is invalid")
            if invalidID.descriptor == "":
                logFile.write(" with no descriptor\n")
            else:
                logFile.write(f" because {invalidID.descriptor}\n")
    
    indent = " "*3
    logFile.write(f"{datetime.now().isoformat()}{indent}INFO Writing data to {rootPath}/.glass/data/IDPaths.json\n")
    exportIDlist(IDList, os.path.join(rootPath, ".glass/data/IDPaths.json"))
    indent = " "*1
    logFile.write(f"{datetime.now().isoformat()}{indent}END Loading IDs\n")

    return IDList

def checkDrives(logFile, rootPath):
    # Checks that the drives listed in the data folder match up with those in the data.json file
    indent = " "*1
    logFile.write(f"{datetime.now().isoformat()}{indent}BEGIN Comparing Drives\n")
    driveData = {}
    with open(f"{rootPath}/.glass/data/drives.json", "r") as driveFile:
        fileData = json.load(driveFile)
        driveList = fileData["drives"]

    indent = " "*3
    logFile.write(f"{datetime.now().isoformat()}{indent}INFO Found {len(driveList)} Drives in the json File\n")
    indent = " "*5
    driveLetters = [item['letter'] for item in driveList]
    for path in os.listdir(f"{rootPath}/.glass/data/"):
        driveLetter = path.split(".")[0][-1]
        # Because the central IDList doesn't end in A
        if driveLetter == "s":
            driveLetter = "A"
        
        if driveLetter not in driveLetters:
            logFile.write(f"{datetime.now().isoformat()}{indent}WARN Drive Letter {driveLetter} has an IDList file but is NOT in drives.json file\n")


    indent = " "*1
    logFile.write(f"{datetime.now().isoformat()}{indent}END Comparing Drives\n")

def doBackgroundTasks(rootPath, metaPath, excludedList, command, version):
    indent = " "*1

    # Clear Log File
    logFile = open(os.path.join(rootPath, ".glass/logs/background.txt"), "w")
    logFile.write("w+")
    logFile.close()

    # Write Metadata to Log file
    logFile = open(os.path.join(rootPath, ".glass/logs/background.txt"), "w+")
    logFile.write(f"{datetime.now().isoformat()}{indent}BEGIN Background Tasks\n")
    logFile.write(f"{datetime.now().isoformat()}{indent}INFO version={version}\n")
    logFile.write(f"{datetime.now().isoformat()}{indent}INFO command={command}\n")
    logFile.write(f"{datetime.now().isoformat()}{indent}INFO Reading Data from {rootPath}\n")

    # Compare Drives
    try:
        checkDrives(logFile, rootPath)
    except Exception as e:
        logFile.write(f"{datetime.now().isoformat()}{indent} ERROR in Drive Comparator\n")
        indent = " "*5
        logFile.write(f"{datetime.now().isoformat()}{indent} ERROR {e}\n")
        return

    
    # Save IDs
    try:
        IDList = readFileSystem(logFile, rootPath, excludedList)
    except Exception as e:
        logFile.write(f"{datetime.now().isoformat()}{indent} ERROR in File System Reader\n")
        indent = " "*5
        logFile.write(f"{datetime.now().isoformat()}{indent} ERROR {e}\n")
        return

    # Save Projects
    try: 
        project.readProjectsFileSystem(logFile, metaPath, IDList)
    except Exception as e:
        logFile.write(f"{datetime.now().isoformat()}{indent} ERROR in Project Reader\n")
        indent = " "*5
        logFile.write(f"{datetime.now().isoformat()}{indent} ERROR {e}\n")
        return
    
    indent = " "*1
    logFile.write(f"{datetime.now().isoformat()}{indent}END Background Tasks\n")

def selectFromList(list):
    # Allow the user to select an item from a list
    while True:
        for index, item in enumerate(list):
            click.echo(f"{index+1}. {item}")
        selectedIndex = click.prompt("Which item do you want?", type=int)
        try:
            selectedItem = list[selectedIndex-1]
            return selectedItem 
        except IndexError:
            click.echo("This number is invalid")
