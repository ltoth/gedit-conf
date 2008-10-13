import gedit
import os
import time
import shutil

class NetSavePlugin(gedit.Plugin):
	def __init__(self):
		gedit.Plugin.__init__(self)
		
	def activate(self, window):
		#make sure we have the directories to store backups
		self.setup_directories()
		
		#clean any really old backups
		self.clean_backups()
		
		#register new handler for when a new document is opened
		handler_id = window.connect("tab-added", self.on_window_tab_added)
		window.set_data(self.__class__.__name__, handler_id)
		
		#now register handlers for all of the documents that are already open
		for doc in window.get_documents():
			self.connect_document(doc)
		
	def deactivate(self, window):
		name = self.__class__.__name__
		handler_id = window.get_data(name)
		window.disconnect(handler_id)
		window.set_data(name, None)
		for doc in window.get_documents():
			handler_id = doc.get_data(name)
			doc.disconnect(handler_id)
			doc.set_data(name, None)
		
	def update_ui(self, window):
		pass
		
	# Utilities #
	def is_on_remote_fs(self, uri):
		result = False
		
		statinfo = os.stat(uri)
		device = statinfo.st_dev
		
		#if the major and minor numbers are 0 then it is not a local device
		if os.major(device) == 0:
			result = True
		
		return result
		
	def setup_directories(self):
		path = os.path.expanduser("~")
		path = path + "/.gnome2/gedit/netsave_backups"
		
		if not os.path.isdir(path):
			os.makedirs(path)
			
	def clean_backups(self):
		path = os.path.expanduser("~")
		path = path + "/.gnome2/gedit/netsave_backups"
		
		seven_days_ago = time.time() - (7 * 24 * 3600)
		
		for root, dirs, files in os.walk(path):
			for curfile in files:
				statinfo = os.stat(os.path.join(root,curfile))
				mtime = statinfo.st_mtime
				
				if mtime < seven_days_ago:
					os.remove(os.path.join(root,curfile))
			
		
	############
	# Handlers #
	############
	def connect_document(self, doc):
		# set a handler for the documents 'saved' signal
		handler_id = doc.connect("saved", self.on_document_saved)
		doc.set_data(self.__class__.__name__, handler_id)
		
		#and one for the 'saving' signal
		handler_id = doc.connect("saving", self.on_document_saving)
		doc.set_data(self.__class__.__name__, handler_id)
	
	def on_window_tab_added(self, window, tab):
		#have to create the proper handlers for a new document that has been opened
		self.connect_document(tab.get_document())
		
	def on_document_saving(self, doc, *args):
		#handler for when a document is about to be saved
		#first we make sure the file is not stored on a local device and then we delete it
		uri = doc.get_uri_for_display()
		
		if self.is_on_remote_fs(uri):
			#we want to move the file. but since it is on a different filesystem we have to copy then remove
			filename = os.path.basename(uri)
			dest = os.path.expanduser("~")
			dest = dest + "/.gnome2/gedit/netsave_backups/" + filename
			shutil.copyfile(uri, dest)
			os.remove(uri)
		
	def on_document_saved(self, doc, tab):
		#handler for when a document gets saved
		
		uri = doc.get_uri_for_display()
		
		#first make sure it is actually on a remote filesystem
		if self.is_on_remote_fs(uri):		
			currentTime = time.time()
			currentTime = (currentTime - 500)
			os.utime(uri, (currentTime, currentTime))
