from mutagen.id3 import ID3, TIT2, TALB, TPE1, TPE2, COMM, USLT, TCOM, TCON, TDRC, TRCK, APIC, error, TYER
import os
import sys
import glob
import re
import argparse
import fnmatch

def log(open_file, msg, tag=False):
	if tag: msg = tag + " " + msg
	open_file.write(msg + "\n")
	print msg

# turns "01 example song.mp3" into "01 Example Song.mp3"
def capitalizeMP3(name):
	return name[:-4].title() + ".mp3"

# remove windows media player hidden files
def removeWMPFiles(dir, logger):
	log(logger, "## Started purge of WMP image files ##")
	count = 0
	for root, dirnames, filenames in os.walk(dir):
		for pattern in ('AlbumArt*.jpg', 'Folder.jpg', 'desktop.ini'):
			for filename in fnmatch.filter(filenames, pattern):
				count += 1
				log(logger, "Removing hidden file {0}".format(filename) )
				os.remove(os.path.join(root, filename))
	log(logger, "## Finished purge of WMP image files {0} deleted ##".format(count) )

# walks through dir_list and renames each directory as well as all mp3 files found in that directory
def renameFiles(dir_list, logger):
	log(logger, "## Started renaming process ##")
	for cd_path in sorted(dir_list):
		cd_name = cd_path.split('/')[-1]
		songs = glob.glob(cd_path + "/*.mp3")
		if len(songs) <= 0:
			log(logger, "No mp3 files found. Stopping renaming process for '{0}'".format(cd_name), WARNING_TAG)
			continue

		if cd_schema.match(cd_name):
			log(logger, "CD format matches. Skipping rename for '{0}'".format(cd_name), GOOD_TAG)
			os.rename(cd_path, os.path.join(os.path.dirname(cd_path), cd_name.title() ))
		else:
			try: # rename album directory
				audio = ID3(songs[0])
				artist, album, year = audio["TPE1"].text[0], audio["TALB"].text[0], audio["TDRC"].text[0]
				artist, album, year = unicode(artist), unicode(album), unicode(year)
				if year == None or year == "":
					print audio.pprint()
					year = unicode(audio["TYER"].text)  # check the IDv1 frame
				match = re.search(r'\d{4}', year)
				year = match.group() if match else None
				new_cd_name = "{0} - {1} ({2})".format(artist.trim(), album.trim(), year.trim()).title()
				new_cd_path =  os.path.join(os.path.dirname(cd_path), new_cd_name)

				log(logger, "Renaming album directory from '{0}' to '{1}'".format(cd_path.split("/")[-1], new_cd_name), RENAME_TAG)
				os.rename(cd_path, new_cd_path)
				cd_path = new_cd_path
			except:
				log(logger, "Exception thrown when parsing first mp3 file to rename album dir for '{0}'".format(cd_path), WARNING_TAG)

		songs = glob.glob(cd_path + "/*.mp3") # get a new song list since the file names have changed
		for song in songs: # rename songs
			# skip renaming if already in correct format
			song_name = song.split('/')[-1]
			if song_schema.match(song_name):
				log(logger, "Song format matches. Skipping rename for '{0}'".format(song_name), GOOD_TAG)
				new_song_name = os.path.join(os.path.dirname(song), capitalizeMP3(song_name))
				os.rename(song, new_song_name)
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
				new_song_name = "{0} {1}.mp3".format(track, title)
				new_song_path = os.path.join(os.path.dirname(song), new_song_name)

				log(logger, "Renaming song to '{0}' from '{1}'".format(new_song_name, song_name), RENAME_TAG)
				os.rename(song, new_song_path)
			except:
				log(logger, "Exception thrown when parsing '{0}'".format(song), WARNING_TAG)
				continue
	log(logger, "## Finished renaming process ##")

ERROR_TAG = "[ERROR]"
WARNING_TAG = "[WARNING]"
GOOD_TAG = "[GOOD]"
RENAME_TAG = "[RENAME]"

# define regex schemas for pattern matching cd/song names
cd_schema   = re.compile("^.+ - .+ \([0-9]{4}\)$", re.IGNORECASE)
song_schema = re.compile("^[0-9]{2} .+\.mp3$", re.IGNORECASE)

parser = argparse.ArgumentParser(description='PyD3 is a tool used to organize mp3 file metadata')
parser.add_argument('-p', metavar='pathname', help='Specify a path that contains album directories', required=True)
parser.add_argument('-s', help='Specifies path to be a single album directory', action='store_true')
parser.add_argument('-g', metavar='genre', help='The genre of music for all songs in batch')
parser.add_argument('-r', help='Renames album directory and files if possible', action='store_true')
args = vars(parser.parse_args())

pathname, singleAlbumFlag, genre, renameFlag = args['p'], args['s'], args['g'], args['r']
if genre is None: genre = 'Metal'

# for some reason windows grabs the path as unicode
if isinstance(pathname, unicode): pathname = pathname.encode('ascii','ignore')
	
if not isinstance(pathname, str) or not os.path.isdir(pathname):
	print "[Error] Exiting script because '{0}' is not a directory".format(pathname)
	sys.exit()

pathname = pathname.rstrip('/'); # removes all trailing slashes
dir_list = [pathname] if singleAlbumFlag else [d for d in glob.glob(pathname + "/*") if os.path.isdir(d)] # grab paths of all folders
logPath = pathname + "/.." if singleAlbumFlag else pathname   # go back a directory if album directory given
logPath += "/pyd3_rename_log.txt" if renameFlag else "/pyd3_log.txt"

with open(logPath, "wb") as logger:
	logger.write("========== Log =========\r\n")

	removeWMPFiles(pathname, logger)
	if renameFlag: 
		renameFiles(dir_list, logger)
		sys.exit() # dir_list has changed and rename step should happen separately

	# Skip folders that do not match the cd schema
	for d in dir_list:
		cd_name = d.split('/')[-1]
		if not cd_schema.match(cd_name):
			log(logger, "Skipping '{0}' because it is not a valid album directory name".format(cd_name), WARNING_TAG)
			dir_list.remove(d)
	log(logger, "Found {0} album directories".format(len(dir_list)) )

	for cd_path in sorted(dir_list):
		# convert cd path to unix forward slashes
		cd_path = cd_path.replace('\\\\','/').replace('\\','/')
		cd_name = cd_path.split('/')[-1]
		log(logger, "Working in '{0}'".format(cd_name) )

		# capitalize first letter of each word only
		cd_name = cd_name.title()

		# extract metadata from directory name
		endOfArtist = cd_name.find(" - ")
		endOfAlbum = cd_name.rfind('(')
		artist = cd_name[:endOfArtist].strip()
		album = cd_name[endOfArtist + 3 : endOfAlbum].strip()
		year = cd_name[endOfAlbum+1:-1].strip()

		mp3_list = [s for s in glob.glob(cd_path + "/*.mp3")]
		log(logger, "Found " + str(len(mp3_list)) + " mp3 files")
		if len(mp3_list) == 0:
			log(logger, "No mp3 files found in '{0}'".format(cd_name), WARNING_TAG)

		for song_path in sorted(mp3_list):
			# convert cd path to unix forward slashes
			song_path = song_path.replace('\\\\','/').replace('\\','/')
			song_name = song_path.split('/')[-1]
			log(logger, "Processing >>> {0}".format(song_name) )

			if not song_schema.match(song_name):
				log(logger, "Skipping mp3, unable to parse filename '{0}/{1}'".format(cd_name, song_name), ERROR_TAG)
				continue

			# capitalize first letter of each word only
			song_name = capitalizeMP3(song_name)

			# extract metadata from song name
			track_number = song_name[:2].strip()
			track_name = song_name[2:-4].strip()

			# search for cover image in same directory
			image_found = False
			jpgs = glob.glob(cd_path + "/*.jpg") + glob.glob(cd_path + "/*.JPG")
			jpegs = glob.glob(cd_path + "/*.jpeg") + glob.glob(cd_path + "/*.JPEG")
			pngs = glob.glob(cd_path + "/*.png") + glob.glob(cd_path + "/*.PNG")
			all_images = jpgs+jpegs+pngs
			if len(all_images) > 0:
				image_found = True
				image_path = all_images[0]    # grab the first image we found
				image_type = image_path.split('.')[-1]  # get the file extension

			try:
				audio = ID3(song_path)
			except: 
				log(logger, "Adding ID3 header")
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
				log(logger, "Missing ID3 Tag")
				
			audio.add(TIT2(encoding=3, text=unicode(track_name) ))         # TITLE
			audio.add(TRCK(encoding=3, text=unicode(int(track_number)) ))  # TRACK
			audio.add(TPE1(encoding=3, text=unicode(artist) ))             # ARTIST
			audio.add(TPE2(encoding=3, text=unicode(artist) ))             # ALBUMARTIST
			audio.add(TALB(encoding=3, text=unicode(album) ))              # ALBUM
			audio.add(TYER(encoding=3, text=unicode(year) ))               # YEAR
			audio.add(TDRC(encoding=3, text=unicode(year) ))               # YEAR
			audio.add(TCON(encoding=3, text=unicode(genre) ))              # GENRE

			if image_found:
				image_data = open(image_path, 'rb').read()
				audio.add(APIC(3, "image/"+image_type, 3, 'Album Cover', image_data))  # Album Artwork
			else:
				log(logger, "Did not find an image named 'cover' in \"{0}\"".format(cd_name), WARNING_TAG)

			audio.save(song_path, v2_version=3)
			new_song_path = os.path.join(os.path.dirname(song_path), song_name)
			os.rename(song_path, new_song_path)

	log(logger, "Done")
