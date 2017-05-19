PyD3
====

A command line tool for organizing the ID3 tags of MP3 files. The tool is designed for people who organize their music by folder/filename and would like to assign this data inside the tags of their files. Album data (Artist, Album, Year) is read from the folder name containing the song files while Song data (Track Number and Title) are read from the filename of the song. Any existing ID3 tags will be removed and a new ID3v2.3 tag will be created using the parsed data. Any auto generated files from Windows Media Player are detected and deleted (ie. Folder.jpg, AlbumArt.jpg, AlbumArt-Small.jpg).

## Install Instructions (Windows)

1. Install [Python](https://www.python.org/downloads/). (This install should come with python's package manager pip)
2. Add python and pip install locations to your Windows PATH environment variable. Assuming you installed python v2.7 to your C drive, you can append the following to your PATH ```;C:\Python27;C:\Python27\Scripts```
3. Open windows cmd prompt and run ```python --version``` and ```pip --version``` to make sure you have python and pip correctly installed on your machine.
4. Upgrade your pip version with ```python -m pip install -U pip```
5. Install **mutagen** dependency using pip with ```pip install mutagen```
6. Clone/Download this repository to your local machine

## How to use

1. Create a folder to hold all of your album folders. The full path of this directory will be given when you run the script. Place all album folders inside this directory.

2. Rename album folders if needed. The artist name, album name, and year are parsed from the album folder. The folder should be in the following format: ```<Artist Name> - <Album Name> (<Year>)```

3. Rename the individual mp3 files inside each album folder. The track number and song title are parsed from the mp3 filename. The track number must be 2 digits long and there must be a space separating the track number from the title. Format: ```<2 digit track number> <title>.mp3```

3. Add an image file in the album folder and name it "cover.jpg/jpeg/png". This image will be embedded in the tags of all mp3 files in the album folder.

4. Run the program with ```python tageditor.py -p <pathname> [-g genre] [-s]``` The pathname should be the directory from step 1 that contains all of your album folders. The -g flag is optional to specify a genre for the entire batch of album folders. The -s flag is optional which specifies that the -p path given is the path to a *single* album directory, not the surrounding folder. For help run ```python tageditor.py -h```

6. Done! PyD3 will crawl through this directory and fix the ID3 tag information for all of your mp3 files. An error log text file will be created in the directory from step 1.

## An example with file layout

```
music/
  The Beatles - Abbey Road (1969)/
	 01 Come Together.mp3
	 02 Something.mp3
	 cover.jpg
  Bayside - Killing Time (2011)/
     01 Already Gone.mp3
     02 Sick, Sick, Sick.mp3
     cover.png
```

Run on entire music folder 
```
python tageditor.py -p <path to music>/music -g Rock
```

Run on single album 
```
python tageditor.py -s -p "<path to music>/music/Bayside - Killing Time (2011)" -g Rock
```
