# Legislatr

Legislatr is a web-app that predicts the passage of US legislative bills.
It also connects lobbyist contributions to bill sponsors and presents possible influence
contributors have over the creation of a given bill. 
The web-app can be found at: (http://www.legislatr.xyz)
This was produced as a consulting project at Insight Data Science for Fast Forward Labs.
Bill data comes from govtrack.us, contribution data comes from senate.gov.

## Usage

First you have to download all the data (~13 GB),

```
$ ./getdata.sh
```

This could take a while...

Once completed, start setting up the legislatr app databases.
The first file on this path is legislatr\_setup.ipynb.
_Note that the directories in the files may need to be adjusted for your setup.
This is especially true for the .py files._
At the end of each .ipynb file you will be directed to the next step.
There are 9 steps to setting up the databases for legislatr.

Once all databases are set up, the next step is to set up the legsilatr app.
The app is located in the web\_app folder.
In the steps for creating the database, a model was stored in a pickle file (.pkl).
Move that file into the following directory: /web\_app/legislatr/static/.
Running the run.py script should start the legislatr app up.