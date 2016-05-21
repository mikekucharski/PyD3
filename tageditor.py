from mutagen.id3 import ID3, TIT2, TALB, TPE1, TPE2, COMM, USLT, TCOM, TCON, TDRC, TRCK, APIC, error, TYER
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
    
    text = " ".join(words);

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
        album_dir = album_path.split('/')[-1]
        songs = glob.glob(album_path + "/*.mp3")
        if len(songs) <= 0:
            logger.warn("No mp3 files found. Skipping rename process for '{0}'".format(album_dir))
            continue

        if REGEX_ALBUM_DIR.match(album_dir):
            logger.info("GOOD - Album name format matches. Skipping rename for '{0}'".format(album_dir))
            os.rename(album_path, os.path.join(os.path.dirname(album_path), album_dir.title()))
        else:
            try: # rename album directory
                audio = ID3(songs[0])
                artist, album, year = unicode(audio["TPE1"].text[0]), unicode(audio["TALB"].text[0]), unicode(audio["TDRC"].text[0])
                artist = music_title(artist.strip())
                album = music_title(album.strip())
                year = year.strip()

                if year == None or year == "":
                    year = unicode(audio["TYER"].text).strip()  # check the IDv1 frame
                match = re.search(r'\d{4}', year)
                year = match.group() if match else None
                new_album_dir = "{0} - {1} ({2})".format(artist, album, year)
                new_album_path = os.path.join(os.path.dirname(album_path), new_album_dir)

                logger.info("RENAME - Renaming album directory from '{0}' to '{1}'".format(album_path.split("/")[-1], new_album_dir))
                os.rename(album_path, new_album_path)
                album_path = new_album_path
            except:
                logger.warn("Exception thrown when parsing first mp3 file to rename album dir for '{0}'".format(album_path))

        songs = glob.glob(album_path + "/*.mp3") # get a new song list since the file names have changed
        for song in songs: # rename songs
            # skip renaming if already in correct format
            filename = song.split('/')[-1]
            if REGEX_FILENAME.match(filename):
                logger.info("GOOD - Song format matches. Skipping rename for '{0}'".format(filename))
                new_song_path = os.path.join(os.path.dirname(song), music_title_mp3(filename))
                os.rename(song, new_song_path)
                continue

            try:
                audio = ID3(song)
                track, title = unicode(audio["TRCK"].text[0]), unicode(audio["TIT2"].text[0])

                title = title.title()
                index = track.find('/') # cover cases where track is "1/1"
                if index != -1:
                    track = track[:index] # take everything up to the index found

                track_num = int(track)
                track = "0" + str(track_num) if track_num < 10 else track_num
                new_filename = "{0} {1}.mp3".format(track, title)
                new_song_path = os.path.join(os.path.dirname(song), new_filename)

                logger.info("RENAME - Renaming song to '{0}' from '{1}'".format(new_filename, filename))
                os.rename(song, new_song_path)
            except:
                logger.warn("Exception thrown when parsing '{0}'".format(song))
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
                logger.error("Skipping mp3 invalid filename format '{0}/{1}'".format(album_dir, filename))
                continue

            # extract metadata from song name
            filename = music_title_mp3(filename)
            track_params = REGEX_FILENAME.search(filename)
            track_num, track_name = track_params.group(1).strip(), music_title(track_params.group(3).strip())

            try:
                audio = ID3(song_path)
            except: 
                logger.info("Adding ID3 header")
                audio = ID3()
                audio.add(TPE1(encoding=3, text=u'Artist'))
                audio.save(song_path, v2_version=3)
            audio.load(song_path)
            
            # USED FOR DEBUGGING
            # print audio.pprint()
            # audio.clear()
            
            # if an ID3 tag still can't be found, skip trying to delete it
            try:
                audio.delete()
                audio.save(song_path, v2_version=3)
            except:
                logger.info("Missing ID3 Tag")
                
            audio.add(TIT2(encoding=3, text=unicode(track_name) ))         # TITLE
            audio.add(TRCK(encoding=3, text=unicode(int(track_num)) ))  # TRACK
            audio.add(TPE1(encoding=3, text=unicode(artist) ))             # ARTIST
            audio.add(TPE2(encoding=3, text=unicode(artist) ))             # ALBUMARTIST
            audio.add(TALB(encoding=3, text=unicode(album) ))              # ALBUM
            audio.add(TYER(encoding=3, text=unicode(year) ))               # YEAR
            audio.add(TDRC(encoding=3, text=unicode(year) ))               # YEAR
            audio.add(TCON(encoding=3, text=unicode(genre) ))              # GENRE

            if all_images:
                image_data = open(image_path, 'rb').read()
                audio.add(APIC(3, "image/"+image_type, 3, 'Album Cover', image_data))  # Album Artwork

            audio.save(song_path, v2_version=3)
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

    genre = genre if genre is not None else 'Metal'
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
    LOG_FILE_NAME = 'pyd3_' + time.strftime('%Y_%m_%d') + '.log'
    REGEX_ALBUM_DIR = re.compile("^(.+) - (.+) \(([0-9]{4})\)$", re.IGNORECASE)
    REGEX_FILENAME = re.compile("^([0-9]{2}) ([-_] )?(.+)\.mp3$", re.IGNORECASE)

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