import os
import re
import time
import json

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

        self.levelDict = {"area": 0, "category": 1, "subfolder": 2, "project": 3}

        if doValidation:
            self.detectIDContext()
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
                else:
                    self.idType = "invalid"
                    self.descriptor = "Invalid Project ID, Either you have a 2 digit version number or no Revision Letter"
        
    def validatePath(self):
        # Determine if the path is valid given the folder
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
       # Get the ID of the object of it's higher level (i.e the area a given subfolder is within)
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
        print(f"ID: {self.idText}")
        print(f"Desc: {self.descriptor}")
        print(f"Type: {self.idType}")
        if self.idType == "invalid":
            return
        
        print(f"Stored: {storageLabels[self.storageLocation]}")
        if self.idType == "project":
            print(f"Revision-Stage: {revisionLabels[self.revisionStage]}")
            print(f"Revision: {self.revision}")
   

def getIDList(fsPath):
    # Checks to find all the IDs
    # TODO Maybe recursion?

    IDList, invalidIDList = getSubIDs(fsPath)

    for IDType in ["area", "category", "subfolder", "project"]:
        for itemID in IDList:
            if itemID.idType == IDType:
                validIDs, invalidIDs = getSubIDs(itemID.path)
                IDList = IDList + validIDs

                # Paths with subfolders cannot be invalid
                if IDType != "subfolder":
                    invalidIDList = invalidIDList + invalidIDs

    return IDList, invalidIDList


def getSubIDs(fsPath):
    # Find all subIDs in a path
    dirStructure = os.scandir(fsPath)

    ids, invalidIDs = [], []
    for folder in dirStructure:
        try:
            endText = folder.path.split("\\")[-1]
            areaID, desc = endText.split(" - ")
            thisID = pathID(areaID, folder.path, doValidation=True, desc=desc)
            if thisID.idType != "invalid":
                ids.append(thisID)
            else:
                invalidIDs.append(thisID)
        except ValueError:
            thisID = pathID("", folder.path, doValidation=False)
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

if __name__ == "__main__":
    # With the exception of the ID checking, this is just driver code
    action = "input"

    storageLabels = {"A": "C:/", "B": "Zotero", "C": "Google Drive"}
    revisionLabels = {"A": "Planning", "B": "Working Doc", "C": "Editing", "D": "Submission"}
    if action == "export":
        IDList, invalidIDList = getIDList("C:/Users/gabri/Documents/Sample Uni File Structure")

        # Detect if any IDs are the same
        pastIDs = []
        equalIDs = []
        for thisID in IDList:
            if thisID.idText in pastIDs:
                equalIDs.append([thisID, IDList[pastIDs.index(thisID.idText)]])
            pastIDs.append(thisID.idText)

        # Alert invalid IDs
        for invalidID in invalidIDList:
            if invalidID.idText != "":
                pass
                print(f"{invalidID.idText}\n{invalidID.descriptor}\n")

        exportIDlist(IDList, "./jd.json")
    
    elif action == "input":
        IDList = []
        with open("./jd.json", "r", encoding="utf-8") as IDFile:
            rawData = json.load(IDFile)
            for key in rawData["IDs"].keys():
                thisID = rawData["IDs"][key]
                IDList.append(
                    pathID(
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
                )
