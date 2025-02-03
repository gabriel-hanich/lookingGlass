# ID Format
This note specifies the format of every type of ID in Looking Glass. IDs are broken up into the following categories (from highest to lowest level). Files are only to be stored in IDs at or below the Subfolder level. 

1. Area
2. Category
3. Subfolder
4. Project 
5. Project Child

## Area
An Area is the highest level ID in Looking Glass. Each Looking Glass system can have up to 10 areas. It has the following syntax:

```
[driveLetter][1-9][0]
[A-Z][1-9][0]
```

Where:
- `[driveLetter]` is an optional letter designating the drive (if left blank, the system assumes letter `A`)
- `[0-9]` is the numbers 0 through 9

This means that a given area ID could look like any of the following

```
00
10
B20
```

With the folder itself having the following path:

```
[rootpath]/10 - Personal
```

## Categories
A category is a level below an area, and is designated by the second digit. Each area can have up to 9 categories. It has the following syntax:

```
[driveLetter][areaNumber][1-9]
[A-Z][0-9][1-9]
```

Where:
- `[areaNumber]` is the letter of the parent area

This means that a given category ID could look like any of the following:

```
01
11
B21
```

With the folder itself having the following path:

```
[rootpath]/10 - Personal/11 - Finances
```

### Subfolder
A subfolder is the folder that actually stores your files. Each category can have up to 99 subfolders, with a dot separating the two IDs. It has the following syntax:

```
[driveLetter][areaNumber][categoryNumber].[01-99]
[A-Z][0-9][1-9].[01-99]
```

Where:
- `[categoryNumber]` is the number of the parent category. 

This means that a given subfolder ID could look like any of the following

```
01.01
11.34
B21.27
```

With the folder itself having the following path:

```
[rootPath]/10 - Personal/11 - Finances/11.01 - 2025 Finances
```

## Project
A project is a specific, self-contained project within a given subfolder. A given subfolder can have up to 99 projects. It has the following syntax:

```
[driveLetter][areaNumber][categoryNumber].[subfolderNumber].[01-99]
[A-Z][0-9][1-9].[01-99].[01-99]
``` 

Where:
- `[subfolderNumber]` is the number of the parent subfolder

This means that a given project ID could look like any of the following:

```
01.01.01
11.34.45
B21.27.05
```

With the folder itself having the following path:

```
[rootPath]/10 - Personal/11 - Finances/11.01 - 2025 Finances/11.01.01 - Summer Roadtrip
```

## Project Child
A project child is used to track the different revisions of a project. It is the only type not to include the full ID in the folder path. Project Children have the following syntax

```
[driveLetter][areaNumber][categoryNumber].[subfolderNumber].[projectNumber][revisionLetter][revisionNumber]
[A-Z][0-9][1-9].[01-99].[01-99][A-D][1-9]
``` 

Where:
- `[revisionLetter]` is the letter of the revision stage (see below)
- `[revisionNumber]` is the number of the iteration in this stage

This means a given Project Child could have any of the following IDs 

```
01.01.01A1
11.34.45B3
B21.27.05C3
```

With the folder itself having the following path (Either works):

```
[rootPath]/10 - Personal/11 - Finances/11.01 - 2025 Finances/11.01.01 - Summer Roadtrip/A1 - Summer Roadtrip
[rootPath]/10 - Personal/11 - Finances/11.01 - 2025 Finances/11.01.01 - Summer Roadtrip/11.01.01A1 - Summer Roadtrip
```

### Revision Letter
The Revision letter refers to which stage of the drafting process a document is within. These are outlined below:

| Revision Letter | Label | Description| 
| -- | -- | -- |
| A  | Planning | Broad plan for the project with research notes, headings and an outline of each section |
| B  | Working Paper | The first copy to feature fully articulated paragraphs based off of the previously compiled notes |
| C  | Editing | First copy to contain all the text for all the sections, to be proof-read and gradually adjusted | 
| D  | Submission| The final copy that was submitted |

Note: Generally, there will only be D1 documents, (i.e D2, D3... is uncommon)
