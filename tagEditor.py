from Tkinter import Tk
from tkFileDialog import askopenfilename
import tkFileDialog
from mutagen.id3 import ID3, TIT2, TALB, TPE1, TPE2, COMM, USLT, TCOM, TCON, TDRC, TRCK, APIC, error
import os
import sys
import glob
import re
from sys import argv

def log_error(open_file, msg):
	msg += "\r\n"
	open_file.write(msg)
	print(msg)

# define regex schemas for pattern matching cd/song names
cd_schema = re.compile("^[\w ',()]{1,} - [\w ',()]{1,} \([0-9]{4}\)", re.IGNORECASE)
song_schema = re.compile("^[0-9]{2} [\w ',()+.]{1,}.mp3", re.IGNORECASE)

if len(sys.argv) == 3:
	filename, file_type, pathname = sys.argv
elif len(sys.argv) == 2:
	filename, file_type = sys.argv
	# we don't want a full GUI, so keep the root window from appearing
	Tk().withdraw()
	# show an "Open" dialog box and return the path to the selected dir
	pathname = tkFileDialog.askdirectory()
else:
	print "Error - Invalid number of parameters. Exiting script."
	sys.exit()

if not isinstance(pathname, str) or not os.path.isdir(pathname):
	print "Error - file path not valid. Exiting Script."
	sys.exit()

file_type = file_type.lower()
if file_type == 'single':
	dir_list = [pathname]
elif file_type == 'multiple':
	dir_list = [d for d in glob.glob(pathname + "/*") if os.path.isdir(d)]
else:
	print "Error - Invalid type. Type can be \'single\' or \'multiple\'"
	sys.exit()
print "Found {0} directories.".format(len(dir_list))

with open(pathname+"/error_log.txt", "wb") as error_log:
	log_error(error_log, "========== Error Log =========")
	for cd_path in sorted(dir_list):
		cd_name = cd_path.split('/')[-1]
		print "Working in " + cd_name
		if(not cd_schema.match(cd_name) ):
			log_error(error_log, "Error - Invalid cd name - '{0}' is not a valid folder name. Skipping this folder.".format(cd_name))
			continue

		#capitalize first letter of each word only
		cd_name = " ".join(w.capitalize() for w in cd_name.split())
		# extract metadata from directory name
		artist = cd_name.split('-')[0].strip()
		album = cd_name.split('-')[1][:-6].strip()
		year = cd_name.split('(')[1][:-1].strip()

		# remove windows media player hidden files
		windowsMediaHiddenFiles = glob.glob(cd_path + "/AlbumArt*.jpg") + glob.glob(cd_path + "/Folder.jpg") + glob.glob(cd_path + "/desktop.ini")
		for hiddenFile in windowsMediaHiddenFiles:
			print "Removing hidden file {0}".format(hiddenFile.split('/')[-1])
			os.remove(hiddenFile)

		mp3_list = [s for s in glob.glob(cd_path + "/*.mp3")]
		print "Found " + str(len(mp3_list)) + " mp3 files."
		if(len(mp3_list) == 0):
			log_error(error_log, "Error - No mp3 files found in {0}".format(cd_path))

		for song_path in sorted(mp3_list):
			song_name = song_path.split('/')[-1]
			print "Processing >>> {0}".format(song_name)

			if(not song_schema.match(song_name) ):
				log_error(error_log, "Error - Invalid song name - {0}/{1}. Skipping this song file.".format(cd_name, song_name))
				continue

			#capitalize first letter of each word only
			song_name = " ".join(w.capitalize() for w in song_name.split())

			# extract metadata from song name
			track_number = song_name[:2].strip()
			track_name = song_name[2:-4].strip()

			# search for cover image in same directory
			image_found = False
			jpgs = glob.glob(cd_path + "/*.jpg") + glob.glob(cd_path + "/*.JPG")
			jpegs = glob.glob(cd_path + "/*.jpeg") + glob.glob(cd_path + "/*.JPEG")
			pngs = glob.glob(cd_path + "/*.png") + glob.glob(cd_path + "/*.PNG")
			all_images = jpgs+jpegs+pngs
			if(len(all_images) > 0):
				image_found = True
				image_path = all_images[0]    # grab the first image we found
				image_type = image_path.split('.')[-1]  # get the file extension

			# all good,
			try:
				audio = ID3(song_path)
			except: 
				print "Adding ID3 header",
				audio = ID3()
			audio.load(song_path)
			
			#print audio.pprint()  # debugging purposes
			#audio.clear()
			audio.delete()
			audio.add(TIT2(encoding=3, text=unicode(track_name) ))         # TITLE
			audio.add(TRCK(encoding=3, text=unicode(int(track_number)) ))  # TRACK
			audio.add(TPE1(encoding=3, text=unicode(artist) ))             # ARTIST
			audio.add(TPE2(encoding=3, text=unicode(artist) ))             # ALBUMARTIST
			audio.add(TALB(encoding=3, text=unicode(album) ))              # ALBUM
			audio.add(TDRC(encoding=3, text=unicode(int(year)) ))          # YEAR
			audio.add(TCON(encoding=3, text=unicode("Deathcore") ))        # GENRE

			if(image_found):
				image_data = open(image_path, 'rb').read()
				audio.add(APIC(3, "image/"+image_type, 3, 'Album Cover', image_data))  # Album Artwork
			else:
				log_error(error_log, "Error - Cover not found - Did not find an image named cover in {0}".format(cd_path))
			audio.save(song_path, v2_version=3)

			# USED FOR DEBUGGING
			# print "\r\n"  # print newline
			# print audio.pprint()
			# sys.exit()
		print " " # newline
print "Done."