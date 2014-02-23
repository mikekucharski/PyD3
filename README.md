PyD3
====

A command line tool for editing ID3 tags of MP3 files.

## Why edit my ID3 tags?

Sometimes when you move your MP3 file to iTunes or your phone, you will notice that the meta data (album artwork, aritst, track title, etc) is incorrect. Sometimes a blogs website link will show up under the lyrics section. This is very annoying and because of the fact that the underlying ID3 tag contains unwanted data. Use this tool to cleanse your files.

## Install Instructions

1. Install Python its not already installed ```sudo apt-get install python```
2. Install TK python package dependency ```sudo apt-get install python-tk```
3. Finally, clone this repo. Thats it!

# How to use

1. Place all of the song files from a particular CD into separate folders. Each folder will represent a CD folder, and each CD folder should only contain songs from that CD (and the album cover of course).

2. Name your MP3 files. The song number and song name are parsed from the mp3 file. The song number must be 2 digits long and there must be a space delimiting the song number from the name. Example: ```<2 digit song number> <song name>.mp3```

2. Name your CD folder. The artist name, album name, and year are parsed from the folder name. The folder name should be in the following format: ```<Artist Name> - <Album Name> (<Year>)```

3. Add an image file named "cover" in the CD folder

4. Run the program with ```python tagEditor.py multiple```

5. A dialog box will pop up. Select the directory that contains all of your CD folders. The program will now crawl through this directory and fix the ID3 tag information for all of your MP3 files.

## Example file Layout?

In this example you would select the folder 'test' and add the "multiple param.
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

## I only want to edit one CD?

Specify "single" instead of "multiple" when you run the program: ```python tagEditor.py single``` When you are prompted to select the directory, make sure you select the name of the cd folder. "The Beatles - Abbey Road (1969)/" in the example above, not "test".




