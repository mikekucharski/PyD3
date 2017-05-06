from mutagen.id3 import ID3, TIT2, TALB, TPE1, TPE2, COMM, USLT, TCOM, TCON, TDRC, TRCK, APIC, TYER, error, ID3NoHeaderError
import os
import sys
import glob
import re
import argparse
import fnmatch
import logging
import time

def music_title_mp3(filename):
    return music_title(filename[:-4]) + ".mp3"

# turns "01 example song" into "01 Example Song"
def music_title(text):
    words = text.split()
    for i, word in enumerate(words):
        romanNumList = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]
        romanNumList.extend(["X" + n for n in romanNumList])
        if word.upper() in ["EP", "LP"] or word.upper() in romanNumList:
            word = word.upper()
        elif word.find('.') != -1 or word.find('(') != -1: # parens or abreviations
            word = word.title()
        else:
            word = word.capitalize()
        words[i] = word
    
    text = " ".join(words)
    text.replace("_", ":")

    # Search for text inside parens and recursively call music_title
    g = re.search('(.*)\((.*)\)(.*)', text, re.IGNORECASE)
    if g:
        text = "{0}({1}){2}".format(g.group(1), music_title(g.group(2)), g.group(3))
    return text

def find_case_insensitve(dirname, extensions):
    files = []
    for filename in glob.glob(dirname):
        base, ext = os.path.splitext(filename)
        if ext.lower() in extensions:
            files.append(filename)
    return files

# remove windows media player hidden files
def remove_wmp_files(dir):
    logger.info("Starting purge of WMP image files")
    count = 0
    for root, dirnames, filenames in os.walk(dir):
        for pattern in ('AlbumArt*.jpg', 'Folder.jpg', 'desktop.ini'):
            for filename in fnmatch.filter(filenames, pattern):
                count += 1
                logger.info("Removing hidden file {0}".format(filename))
                os.remove(os.path.join(root, filename))
    logger.info("Finished purge of WMP image files, {0} deleted".format(count))

# walks through dir_list and renames each directory as well as all mp3 files found in that directory
def rename_files(dir_list):
    logger.info("Starting rename process")
    for album_path in sorted(dir_list):
        album_dir = os.path.basename(album_path)
        logger.info("Working in '{0}'".format(album_dir))
        print album_path + "/*.mp3"
        mp3_list = glob.glob(album_path + "/*.mp3")
        if len(mp3_list) <= 0:
            logger.warn("No mp3 files found. Skipping rename process for '{0}'".format(album_dir))
            continue

        if REGEX_ALBUM_DIR.match(album_dir):
            logger.info("GOOD - Album name format matches. Skipping rename for '{0}'".format(album_dir))
        else:  # rename album directory
            try:
                tag = ID3(mp3_list[0])
                # TYER checks the year from the IDv1 frame
                tag_list = tag.get("TPE1"), tag.get("TALB"), (tag.get('TYER') or tag.get('TDRC'))
                if not all(tag_list):
                    logger.warn("Could not find artist, album, and year when parsing first song")
                    continue

                artist = music_title(tag_list[0].text[0])
                album = music_title(tag_list[1].text[0])
                year = tag_list[2].text[0]

                if year.__class__.__name__ == "ID3TimeStamp":
                    year = year.text[:4] # format YYYY-MM-DD

                new_album_dir = "{0} - {1} ({2})".format(artist, album, year)
                new_album_path = os.path.join(os.path.dirname(album_path), new_album_dir)

                logger.info("Renaming album directory from '{0}' to '{1}'".format(album_dir, new_album_dir))
                os.rename(album_path, new_album_path)
                album_path = new_album_path
            except ID3NoHeaderError:
                logger.warn("Exception thrown when parsing first mp3 file to rename album dir for '{0}'".format(album_dir))

        # Rename mp3 files
        mp3_list = glob.glob(album_path + "/*.mp3") # get a new song list since the file names have changed
        for song_path in sorted(mp3_list):
            filename = os.path.basename(song_path)
            # skip renaming if already in correct format
            if REGEX_FILENAME.match(filename):
                logger.info("GOOD - Song format matches. Skipping rename for '{0}'".format(filename))
                continue

            try:
                tag = ID3(song)
                tag_list = tag.get("TRCK"), tag.get("TIT2")
                if not all(tag_list):
                    logger.warn("Could not find track number and name when parsing '{0}'".format(filename))
                    continue
                track, title = tag_list[0].text[0], music_title(tag_list[1].text[0])
                # covers when track format is 1/1. Also left pads with 0's up to 2 characters
                track = track.split('/')[0].zfill(2)

                new_filename = "{0} {1}.mp3".format(track, title)
                new_song_path = os.path.join(os.path.dirname(song_path), new_filename)

                logger.info("Renaming song from '{0}' to '{1}'".format(filename, new_filename))
                os.rename(song, new_song_path)
            except:
                logger.warn("Exception thrown when parsing '{0}'".format(filename))
                continue
    logger.info("Finished renaming process")

def save_metadata(dir_list, genre):

    for album_path in sorted(dir_list):

        # verfiy album directory name is correct
        album_dir = os.path.basename(album_path)
        logger.info("Working in '{0}'".format(album_dir))
        if not REGEX_ALBUM_DIR.match(album_dir):
            logger.warn("Skipping invalid album directory format '{0}'".format(album_dir))
            continue

        # extract metadata from directory name
        params = REGEX_ALBUM_DIR.search(album_dir)
        artist, album, year = music_title(params.group(1).strip()), music_title(params.group(2).strip()), params.group(3).strip()

        # search for cover image in same directory
        all_images = find_case_insensitve(album_path + "/*", [".jpeg", ".jpg", ".png"])
        if all_images:
            image_path = all_images[0]    # grab the first image we found
            image_type = image_path.split('.')[-1]  # get the file extension without dot
        else:
            logger.warn("Did not find any cover image files in '{0}'".format(album_dir))

        # get all MP3 files in album dir
        mp3_list = find_case_insensitve(album_path + "/*", [".mp3"])
        logger.info("Found {0} mp3 files".format(len(mp3_list)))
        if not mp3_list:
            logger.warn("Skipping album directory with no mp3 files '{0}'".format(album_dir))
            continue

        for song_path in sorted(mp3_list):

            # verify song file name is correct
            filename = os.path.basename(song_path)
            logger.info("Processing >>> {0}".format(filename))
            if not REGEX_FILENAME.match(filename):
                logger.warn("Skipping mp3 invalid filename format '{0}/{1}'".format(album_dir, filename))
                continue

            # extract metadata from song name
            filename = music_title_mp3(filename)
            track_params = REGEX_FILENAME.search(filename)
            track_num, track_name = track_params.group(1).strip(), music_title(track_params.group(3).strip())

            try:
                # If  genre not provided, take from existing tag
                if genre is None:
                    tag = ID3(song_path) # will call load() on the path
                    genre = tag.get("TCON").genres[0] if tag.get("TCON") else ""
                    genre = "Metal" if genre is None or genre.strip() == "" else genre
            except ID3NoHeaderError:
                logger.warn("File does not start with an ID3 tag")
            
            # Create empty tag and add frames to it
            tag = ID3()
            tag.add(TIT2(encoding=3, text=unicode(track_name) ))         # TITLE
            tag.add(TRCK(encoding=3, text=unicode(int(track_num))))      # TRACK
            tag.add(TPE1(encoding=3, text=unicode(artist) ))             # ARTIST
            tag.add(TPE2(encoding=3, text=unicode(artist) ))             # ALBUMARTIST
            tag.add(TALB(encoding=3, text=unicode(album) ))              # ALBUM
            tag.add(TYER(encoding=3, text=unicode(year) ))               # YEAR
            tag.add(TDRC(encoding=3, text=unicode(year) ))               # YEAR
            tag.add(TCON(encoding=3, text=unicode(genre) ))              # GENRE

            if all_images:
                image_data = open(image_path, 'rb').read()
                tag.add(APIC(3, "image/"+image_type, 3, 'Album Cover', image_data))  # Album Artwork

            tag.save(song_path, v2_version=3) # write the tag as ID3v2.3
            
            # Rename file
            new_song_path = os.path.join(os.path.dirname(song_path), filename)
            os.rename(song_path, new_song_path)

def main():
    # set up argument handling
    parser = argparse.ArgumentParser(description='PyD3 is a command line tool used to organize metadata of mp3 files')
    parser.add_argument('-p', metavar='path', help='Specify a path that contains one or more album directories', required=True)
    parser.add_argument('-s', help='Specifies path to be a single album directory', action='store_true')
    parser.add_argument('-g', metavar='genre', help='The genre of music for all songs in batch')
    parser.add_argument('-r', help='Renames album directory and files if possible', action='store_true')
    args = vars(parser.parse_args())

    # grab arguments from command line
    path, singleAlbumFlag, genre, renameFlag = args['p'], args['s'], args['g'], args['r']

    # for some reason windows grabs the path as unicode
    if isinstance(path, unicode):
        path = path.encode('ascii','ignore')
        
    if not isinstance(path, str) or not os.path.isdir(path):
        logger.error("Exiting script because '{0}' is not a directory".format(path))
        sys.exit()

    path = path.rstrip('/'); # removes all trailing slashes
    dir_list = [path] if singleAlbumFlag else [d for d in glob.glob(path + "/*") if os.path.isdir(d)] # grab paths of all folders

    logger.info("PyD3 Started")
    remove_wmp_files(path)
    if renameFlag: 
        rename_files(dir_list)  # dir_list will be modified in this func and is no longer valid
    else:
        save_metadata(dir_list, genre)
    logger.info("PyD3 Done")

if __name__ == '__main__':
    # GLOBAL VARIABLES
    # constants
    LOG_DIR = 'log'
    LOG_FILE_NAME = 'pyd3_' + time.strftime('%Y-%m-%d_%H-%M-%S') + '.log'
    REGEX_ALBUM_DIR = re.compile("^(.+) - (.+) \(([0-9]{4})\)$", re.IGNORECASE)
    REGEX_FILENAME = re.compile("^([0-9]{2})\.? ([-_] )?(.+)\.mp3$", re.IGNORECASE)

    # set up Logger
    logFormatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s] %(message)s", datefmt='%Y-%m-%d %H:%M:%S')
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # log to the console
    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    logger.addHandler(consoleHandler)

    # also log to a file
    if not os.path.exists(LOG_DIR):
        logger.info("Creating log directory")
        os.makedirs(LOG_DIR)
    fileHandler = logging.FileHandler('{0}/{1}'.format(LOG_DIR, LOG_FILE_NAME))
    fileHandler.setFormatter(logFormatter)
    logger.addHandler(fileHandler)

    main()