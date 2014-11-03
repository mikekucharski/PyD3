from mutagen.id3 import ID3, TIT2, TALB, TPE1, TPE2, COMM, USLT, TCOM, TCON, TDRC, TRCK, APIC, error, TYER
import os
import sys
import glob
import re
import argparse

def log(open_file, msg, tag=False):
	if tag:
		msg = tag + msg
	msg += "\r\n"
	open_file.write(msg)
	print(msg)

ERROR_TAG = "[Error] "
WARNING_TAG = "[Warning] "

# define regex schemas for pattern matching cd/song names
cd_schema = re.compile("^[\w ',()]{1,} - [\w ;',()+.-]{1,} \([0-9]{4}\)", re.IGNORECASE)
song_schema = re.compile("^[0-9]{2} [\w ;',()+.-]{1,}.mp3", re.IGNORECASE)

parser = argparse.ArgumentParser(description='PyD3 is a tool used to organize mp3 file metadata')
parser.add_argument('-p', metavar='pathname', help='Specify a path that contains album directories.', required=True)
parser.add_argument('-g', metavar='genre', help='The genre of music for this batch')
args = vars(parser.parse_args())

parent_dir = args['p']
genre = args['g'] if args['g'] is not None else 'Metal'

# for some reason windows grabs the path as unicode
if isinstance(parent_dir, unicode):
	parent_dir = parent_dir.encode('ascii','ignore')
	
if not isinstance(parent_dir, str) or not os.path.isdir(parent_dir):
	print "[Error] Exiting script because folder {0} could not be found.".format(parent_dir)
	sys.exit()

parent_dir = parent_dir.rstrip('/');

#grab paths of all folders
dir_list = [d for d in glob.glob(parent_dir + "/*") if os.path.isdir(d)]

with open(parent_dir+"/error_log.txt", "wb") as error_log:
	log(error_log, "========== Error Log =========")

	# Skip folders that do not match the cd schema
	for d in dir_list:
		cd_name = d.split('/')[-1]
		if not cd_schema.match(cd_name):
			log(error_log, "Skipping '{0}' because it is not a valid album directory name.".format(cd_name), WARNING_TAG)
			dir_list.remove(d)
	print "Found {0} album directories.".format(len(dir_list))

	for cd_path in sorted(dir_list):
	
		# convert cd path to unix forward slashes
		cd_path = cd_path.replace('\\','/')
		cd_path = cd_path.replace('\\\\','/')
		cd_name = cd_path.split('/')[-1]
		print "Working in " + cd_name

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
			log(error_log, "No mp3 files found in '{0}'".format(cd_name), WARNING_TAG)

		for song_path in sorted(mp3_list):
			# convert cd path to unix forward slashes
			song_path = song_path.replace('\\','/')
			song_path = song_path.replace('\\\\','/')
			
			song_name = song_path.split('/')[-1]
			print "Processing >>> {0}".format(song_name)

			if(not song_schema.match(song_name) ):
				log(error_log, "Skipping mp3, unable to parse filename '{0}/{1}'".format(cd_name, song_name), ERROR_TAG)
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


			#song_path = song_path.replace('/', '\\')

			try:
				audio = ID3(song_path)
			except: 
				print "Adding ID3 header",
				audio = ID3()
				audio.add(TPE1(encoding=3, text=u'Artist'))
				audio.save(song_path, v2_version=3)
			audio.load(song_path)
			
			#print audio.pprint()  # debugging purposes
			#audio.clear()
			
			# if an ID3 tag still can't be found, skip trying to delete it
			try:
				audio.delete()
				audio.save(song_path, v2_version=3)
			except:
				print "Missing ID3 Tag"
				
			audio.add(TIT2(encoding=3, text=unicode(track_name) ))         # TITLE
			audio.add(TRCK(encoding=3, text=unicode(int(track_number)) ))  # TRACK
			audio.add(TPE1(encoding=3, text=unicode(artist) ))             # ARTIST
			audio.add(TPE2(encoding=3, text=unicode(artist) ))             # ALBUMARTIST
			audio.add(TALB(encoding=3, text=unicode(album) ))              # ALBUM
			audio.add(TYER(encoding=3, text=unicode(year) ))               # YEAR
			audio.add(TDRC(encoding=3, text=unicode(year) ))               # YEAR
			audio.add(TCON(encoding=3, text=unicode(genre) ))              # GENRE

			if(image_found):
				image_data = open(image_path, 'rb').read()
				audio.add(APIC(3, "image/"+image_type, 3, 'Album Cover', image_data))  # Album Artwork
			else:
				log(error_log, "Did not find an image named 'cover' in \"{0}\"".format(cd_name), ERROR_TAG)
			audio.save(song_path, v2_version=3)

			# USED FOR DEBUGGING
			# print "\r\n"  # print newline
			# print audio.pprint()
			# sys.exit()
		print " " # newline
print "Done."
