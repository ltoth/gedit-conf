# textilepreview.py - HTML preview of Textile formatted text in gedit
#
# Copyright (C) 2005 - Michele Campeotto
# Brutally hacked for Textile - Tom MacWright
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

import gedit

import sys
import gtk
import gtkhtml2
import textile

HTML_TEMPLATE = """<html><head><style type="text/css">
body { background-color: #fff; padding: 8px; }
p, div { margin: 0em; }
p + p, p + div, div + p, div + div { margin-top: 0.8em; }
blockquote { padding-left: 12px; padding-right: 12px; }
pre { padding: 12px; }
</style></head><body>%s</body></html>"""

class TextilePreviewPlugin(gedit.Plugin):

	def __init__(self):
		gedit.Plugin.__init__(self)
			
	def activate(self, window):
		action = ("Textile Preview",
			  None,
			  "Textile Preview",
			  "<Control><Shift>T",
			  "Update the HTML preview",
			  lambda x, y: self.update_preview(y))
		
		# Store data in the window object
		windowdata = dict()
		window.set_data("TextilePreviewData", windowdata)
	
		scrolled_window = gtk.ScrolledWindow()
		scrolled_window.set_property("hscrollbar-policy",gtk.POLICY_AUTOMATIC)
		scrolled_window.set_property("vscrollbar-policy",gtk.POLICY_AUTOMATIC)
		scrolled_window.set_property("shadow-type",gtk.SHADOW_IN)

		html_view = gtkhtml2.View()
		html_doc = gtkhtml2.Document()
		html_view.set_document(html_doc)
		
		html_doc.clear()
		html_doc.open_stream("text/html")
		html_doc.write_stream(HTML_TEMPLATE % ("",))
		html_doc.close_stream()

		scrolled_window.set_hadjustment(html_view.get_hadjustment())
		scrolled_window.set_vadjustment(html_view.get_vadjustment())
		scrolled_window.add(html_view)
		scrolled_window.show_all()
		
		bottom = window.get_bottom_panel()
		image = gtk.Image()
		image.set_from_icon_name("gnome-mime-text-html", gtk.ICON_SIZE_MENU)
		self.scrolled_window = scrolled_window
		bottom.add_item(scrolled_window, "Textile Preview", image) # so this image is null
		windowdata["bottom_panel"] = scrolled_window
		windowdata["html_doc"] = html_doc
		
		windowdata["action_group"] = gtk.ActionGroup("TextilePreviewActions")
		windowdata["action_group"].add_actions ([action], window)

		manager = window.get_ui_manager()
		manager.insert_action_group(windowdata["action_group"], -1)

		windowdata["ui_id"] = manager.new_merge_id ()

		manager.add_ui (windowdata["ui_id"],
				"/MenuBar/ToolsMenu/ToolsOps_5",
				"Textile Preview",
				"Textile Preview",
				gtk.UI_MANAGER_MENUITEM, 
				True)
	
	def deactivate(self, window):
		# Retreive the data of the window object
		windowdata = window.get_data("TextilePreviewData")
		
		# Remove the menu action
		manager = window.get_ui_manager()
		manager.remove_action_ui(windowdata["ui_id"])
		manager.remove_action_group(windowdata["action_group"])
		
		# Remove the bottom panel
		bottom = window.get_bottom_panel()
		bottom.remove_item(windowdata["bottom_panel"])
	def update_live(self, event, window):
		bottom_panel = window.get_bottom_panel()
		if not bottom_panel.item_is_active(self.scrolled_window):
			return
		windowdata = window.get_data("TextilePreviewData")
		view = window.get_active_view()
		if not view:
			 return
		
		doc = view.get_buffer()
		
		start = doc.get_start_iter()
		end = doc.get_end_iter()
		
		if doc.get_selection_bounds():
			start = doc.get_iter_at_mark(doc.get_insert())
			end = doc.get_iter_at_mark(doc.get_selection_bound())
		
		text = doc.get_text(start, end)
		html = HTML_TEMPLATE % (textile.textile(text),)
		html_doc = windowdata["html_doc"]
		html_doc.clear()
		html_doc.open_stream("text/html")
		html_doc.write_stream(html)
		html_doc.close_stream()

	def update_preview(self, window):
		# Retreive the data of the window object
		windowdata = window.get_data("TextilePreviewData")
		bottom_panel = window.get_bottom_panel()
		bottom_panel.show()
		bottom_panel.activate_item(self.scrolled_window)
		view = window.get_active_view()
		if not view:
			 return
		
		doc = view.get_buffer()
		doc.connect("changed", self.update_live, window)
		
		start = doc.get_start_iter()
		end = doc.get_end_iter()
		
		if doc.get_selection_bounds():
			start = doc.get_iter_at_mark(doc.get_insert())
			end = doc.get_iter_at_mark(doc.get_selection_bound())
		
		text = doc.get_text(start, end)
		html = HTML_TEMPLATE % (textile.textile(text),)	
		p = windowdata["bottom_panel"].get_placement()
		
		html_doc = windowdata["html_doc"]
		html_doc.clear()
		html_doc.open_stream("text/html")
		html_doc.write_stream(html)
		html_doc.close_stream()
		
		windowdata["bottom_panel"].set_placement(p)
