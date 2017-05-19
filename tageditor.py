from mutagen.id3 import ID3, TIT2, TALB, TPE1, TPE2, COMM, USLT, TCOM, TCON, TDRC, TRCK, APIC, TYER, error, ID3NoHeaderError
from mutagen.mp4 import MP4, MP4Cover, AtomDataType
import os
import sys
import glob
import re
import argparse
import fnmatch
import logging
import time

class Song:
    
    def __init__(self, title, track_num, track_num_total, artist, album, year):
        self.title = title
        self.track_num = track_num
        self.track_num_total = track_num_total
        self.artist = artist
        self.album = album
        self.year = year

def music_title(text):
    """Converts a string into a "title"

    Handles uppercasing only the first leter of words.
    Keywords such as EP and LP as well as reoman numeralse are caps

    Args:
        text: The string to 'titlize'

    Returns:
        The transformed text
    """
    ROMAN_NUMS = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]
    ROMAN_NUMS.extend(["X" + n for n in ROMAN_NUMS])
    UPPER_KEYWORDS = ["EP", "LP"]

    words = text.split()
    for i, word in enumerate(words):
        if word.upper() in UPPER_KEYWORDS or word.upper() in ROMAN_NUMS:
            word = word.upper()
        elif word.find('.') != -1 or word.find('(') != -1: # parens or abreviations
            word = word.title()
        else:
            word = word.capitalize()
        words[i] = word
    
    # Replace underscores with colons because Windows doens't allow colon characters in name
    text = " ".join(words).replace("_", ":")

    # Search for text inside parens and recursively call music_title
    g = re.search('(.*)\((.*)\)(.*)', text, re.IGNORECASE)
    if g:
        text = "{0}({1}){2}".format(g.group(1), music_title(g.group(2)), g.group(3))
    return text

def find_files_by_extension(directory, extensions):
    """Walks through files in a directory and searches for files by extension ignoring case

    Args:
        directory: The root directory to start the search from
        extensions: A list of extensions to filter files by

    Returns:
        An array of filenames that match the extensions argument
    """
    files = []
    for filename in glob.glob(directory):
        base, ext = os.path.splitext(filename)
        if ext.lower() in extensions:
            files.append(filename)
    return files

def remove_wmp_files(directory):
    """Removes windows media player hidden files

    Args:
        directory: The root directory to start the search from
    """
    logger.info("Starting purge of WMP image files")
    count = 0
    for root, dirnames, filenames in os.walk(directory):
        for pattern in ('AlbumArt*.jpg', 'Folder.jpg', 'desktop.ini'):
            for filename in fnmatch.filter(filenames, pattern):
                count += 1
                logger.info("Removing hidden file {0}".format(filename))
                os.remove(os.path.join(root, filename))
    logger.info("Finished purge of WMP image files, {0} deleted".format(count))

def modify_m4a_tag(song, song_path, image_path, genreArg):

    # Essentially returns a map of m4a keys to values
    m4a = MP4(song_path)

    # create reference to M4A keys
    M4A_IDEN_TITLE = '\xa9nam'
    M4A_IDEN_TRACK_NUM = 'trkn'
    M4A_IDEN_ARTIST = '\xa9ART'
    M4A_IDEN_ALBUM_ARTIST = 'aART'
    M4A_IDEN_ALBUM = '\xa9alb'
    M4A_IDEN_YEAR = '\xa9day'
    M4A_IDEN_GENRE = '\xa9gen'
    M4A_IDEN_COMMENT = '\xa9cmt'
    M4A_IDEN_COVER = 'covr'

    # Set genre
    genre = None
    if genreArg is None or genreArg.strip() == "":
         # Try to extract genre from existing tag
        try:
            genre = m4a.tags[M4A_IDEN_GENRE][0]
        except KeyError:
            pass
    else:
        genre = genreArg
    
    # Set genre to default if genre could not be extracted
    genre = DEFAULT_GENRE if genre is None or genre.strip() == "" else genre

    # Assign all tags
    m4a.tags[M4A_IDEN_TITLE] = [unicode(song.title)]
    m4a.tags[M4A_IDEN_TRACK_NUM] = [(int(song.track_num), song.track_num_total)] # tuple of size 2
    m4a.tags[M4A_IDEN_ARTIST] = [unicode(song.artist)]
    m4a.tags[M4A_IDEN_ALBUM_ARTIST] = [unicode(song.artist)]
    m4a.tags[M4A_IDEN_ALBUM] = [unicode(song.album)]
    m4a.tags[M4A_IDEN_YEAR] = [unicode(song.year)]
    m4a.tags[M4A_IDEN_GENRE] = [unicode(genre)]
    m4a.tags[M4A_IDEN_COMMENT] = [unicode("")]

    if image_path:
        image_data = open(image_path, 'rb').read()
        image_type = AtomDataType.PNG if image_path.split('.')[-1].lower() == "png" else AtomDataType.JPEG
        cover = MP4Cover(image_data, image_type)
        m4a.tags[M4A_IDEN_COVER] = [cover]

    # Save the m4a tag
    m4a.save()

def modify_mp3_tag(song, song_path, image_path, genreArg):
    
    # Set genre
    genre = None
    if genreArg is None or genreArg.strip() == "":
        # Try extracting genre from existing tag
        try:
            tag = ID3(song_path) # will call load() on the path
            genre = tag.get("TCON").genres[0] if tag.get("TCON") else None
        except ID3NoHeaderError:
            pass
    else:
        genre = genreArg
    
    # Set genre to default if genre could not be extracted
    genre = DEFAULT_GENRE if genre is None or genre.strip() == "" else genre

    # Create empty tag and add frames to it
    tag = ID3()
    tag.add(TIT2(encoding=3, text=unicode(song.title) ))          # TITLE
    tag.add(TRCK(encoding=3, text=unicode(int(song.track_num))))  # TRACK
    tag.add(TPE1(encoding=3, text=unicode(song.artist) ))         # ARTIST
    tag.add(TPE2(encoding=3, text=unicode(song.artist) ))         # ALBUMARTIST
    tag.add(TALB(encoding=3, text=unicode(song.album) ))          # ALBUM
    tag.add(TYER(encoding=3, text=unicode(song.year) ))           # YEAR
    tag.add(TDRC(encoding=3, text=unicode(song.year) ))           # YEAR
    tag.add(TCON(encoding=3, text=unicode(genre) ))               # GENRE

    if image_path:
        image_data = open(image_path, 'rb').read()
        image_type = image_path.split('.')[-1]  # get the file extension without dot
        tag.add(APIC(3, "image/"+image_type, 3, 'Album Cover', image_data))  # Album Artwork

    tag.save(song_path, v2_version=3) # write the tag as ID3v2.3

def save_metadata(dir_list, genreArg):

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
        all_images = find_files_by_extension(album_path + "/*", [".jpeg", ".jpg", ".png"])
        if all_images:
            image_path = all_images[0]    # grab the first image we found
        else:
            logger.warn("Did not find any cover image files in '{0}'".format(album_dir))

        # get all MP3/M4A files in album dir
        m4a_flag = False
        song_paths = find_files_by_extension(album_path + "/*", [".mp3"])
        if not song_paths:
            m4a_flag = True
            song_paths = find_files_by_extension(album_path + "/*", [".m4a"])

        if not song_paths:
            logger.warn("Skipping album directory with no mp3/m4a files '{0}'".format(album_dir))
            continue

        song_paths_len = len(song_paths)
        logger.info("Found {0} mp3/m4a files".format(song_paths_len))

        for song_path in sorted(song_paths):
            # verify song file name is correct
            filename = os.path.basename(song_path)
            logger.info("Processing >>> {0}".format(filename))
            if not REGEX_FILENAME.match(filename):
                logger.warn("Skipping mp3 invalid filename format '{0}/{1}'".format(album_dir, filename))
                continue

            # extract metadata from song name
            track_params = REGEX_FILENAME.search(filename)
            track_num, track_name = track_params.group(1).strip(), music_title(track_params.group(3).strip())

            song = Song(track_name, track_num, song_paths_len, artist, album, year)
            # Handle Apple Itunes m4a format.
            if m4a_flag:
                modify_m4a_tag(song, song_path, image_path, genreArg)
            else:
                modify_mp3_tag(song, song_path, image_path, genreArg)

def main():
    """Main method responsible for parasing cl aguments and passing them to 

    Args:
        None
    """
    # set up argument handling
    parser = argparse.ArgumentParser(description='PyD3 is a command line tool used to organize metadata of mp3 files')
    parser.add_argument('-p', metavar='path', help='Specify a path that contains one or more album directories', required=True)
    parser.add_argument('-s', help='Specifies path to be a single album directory', action='store_true')
    parser.add_argument('-g', metavar='genre', help='The genre of music for all songs in batch')
    args = vars(parser.parse_args())

    # grab arguments from command line
    path, singleAlbumFlag, genreArg = args['p'], args['s'], args['g']

    # for some reason windows grabs the path as unicode
    if isinstance(path, unicode):
        path = path.encode('ascii','ignore')
        
    if not isinstance(path, str) or not os.path.isdir(path):
        logger.error("Exiting script because '{0}' is not a directory".format(path))
        sys.exit()

    # removes all trailing slashes
    path = path.rstrip('/');

     # grab full paths of all album folders
    dir_list = [path] if singleAlbumFlag else [d for d in glob.glob(path + "/*") if os.path.isdir(d)]
    if len(dir_list) == 0:
        logger.error("Did not find any directories in {0}".format(path))
        sys.exit()

    logger.info("PyD3 Started")
    remove_wmp_files(path)
    save_metadata(dir_list, genreArg)
    logger.info("PyD3 Done")

if __name__ == '__main__':
    # constants (Global variables)
    LOG_DIR = 'log'
    LOG_FILE_NAME = 'pyd3_' + time.strftime('%Y-%m-%d_%H-%M-%S') + '.log'
    REGEX_ALBUM_DIR = re.compile("^(.+) - (.+) \(([0-9]{4})\)$", re.IGNORECASE)
    REGEX_FILENAME = re.compile("^([0-9]{2})\.? ([-_] )?(.+)\.(mp3|m4a)$", re.IGNORECASE)

    DEFAULT_GENRE = 'Metal'

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