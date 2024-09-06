# How to Manage setup and use Custom .Glass Files 
Looking Glass relies upon a custom filetype (.glass) to manage links to files hosted in other locations. This is denoted by file IDs that start with a letter other than `A`. These files are located within the `A` file silo, where you would expect based on their ID. However, they point towards the location of the file in the other silo. 

.glass files are human-readable markdown files, meaning that they can easily be read by the user, or any 3rd party software. The files are automatically created whenever the user inputs a new file into their Johnny-Decimal system.

## How to Set it up
### Create the .bat File
This process relies on a .bat file that runs the `fileOpener.py` file. The bat file can be called any title, and should follow the following structure.

```bat
{Python Path} "{Path to fileOpener.py}" %*
```

Where:
- `{Python Path}` is the path to the python executable. The same one used in the command section of the registry value
- `{Path to fileOpener.py}` is the full path to the `fileOpener.py` file. This file is responsible for actually opening the link stored within the `.glass` file. 

> In the above excerpt, replace the { and } characters. However the " is necessary

### Tell Windows to Run .bat file
Next, Windows needs to be told to open all `.glass` files using the bat file. This sounds difficult, but isn't really that bad. First, go into file explorer and navigate to the root directory of Looking Glass. Then right click on `test.glass` (or any other .glass file). 

After the file has been right-clicked, select the `Open With` option. This should open a menu with the title "Select an app to open this .glass file". Scroll to the bottom of the list of apps, and click on "Select an app on your PC". This will open another file-explorer window. Within this window, navigate to and select the `.bat` file previously created. 

Now whenever a `.glass` file is opened, Windows will call the `.bat` file, which will then open the python file. This python file will then open the file. 