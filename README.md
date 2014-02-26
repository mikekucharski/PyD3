PyD3
====

A command line tool for editing ID3 tags of MP3 files. This tool will strip any existing tags on your MP3 files and construct new ones based off of the song names and parent folder names. Note, the new tags will be version ID3v2.3 only. Oh, and this program will also detect any files auto generated by windows media player and delete them (Folder.jpg, AlbumArt.jpg, AlbumArt-Small.jpg).

## Why edit my ID3 tags?

Sometimes when you move your MP3 file to iTunes or your phone, you will notice that the meta data (album artwork, aritst, track title, etc) is incorrect. Sometimes a blog's website link will show up under the lyrics section. This happens because the underlying ID3 tag contains unwanted data. Use this tool to cleanse your files!

## Install Instructions

1. Install Python its not already installed ```sudo apt-get install python```
2. Install TK python package dependency ```sudo apt-get install python-tk```
3. Finally, clone this repo. Thats it!

# How to use

1. Create a folder that will contain all of your CD folders.

2. Create any number of CD folders inside this directory. The artist name, album name, and year are parsed from the folder name. The folder name should be in the following format: ```<Artist Name> - <Album Name> (<Year>)```

3. Place the song files into their respective CD folder. The song number and song name are parsed from the mp3 files. The song number must be 2 digits long and there must be a space delimiting the song number from the name. Format: ```<2 digit song number> <song name>.mp3```

3. Add an image file in the root of the CD folder named "cover.jpg/jpeg/png". *Note, you do not need to specify an album cover for the script to work. There will simply be an error stating that you forgot the cover. You can ignore this if desired.

4. Run the program with ```python tagEditor.py multiple <pathname>``` The pathname should be the folder that contains all of your CD folders. If you leave out the path name, a dialog box will pop up. Select the directory that contains all of your CD folders. Note, the dialog box may not work cross platform so specifying the path is recommended.

6. Done! The program will now crawl through this directory and fix the ID3 tag information for all of your MP3 files. An error log text file will be created in the directory you choose so make sure you check it for any errors and delete it once done.

## Example with file layout?

```
test/
  The Beatles - Abbey Road (1969)/
	 01 Come Together.mp3
	 02 Something.mp3
	 cover.jpg
  Bayside - Killing Time (2011)/
     01 Already Gone.mp3
     02 Sick, Sick, Sick.mp3
     cover.png
```

In this example you would run ```python tagEditor.py multiple test``` to operate on both CD folders.

## I only want to edit one CD?

Lets use the previous example. If you only want to edit the Beatles folder, you would run it as  ```python tagEditor.py single test/The\ Beatles\ -\ Abbey\ Road\ \(1969\)```




