# -*- coding: utf-8 -*-
#
# Copyright (c) 2008 sharkbaitbobby <sharkbaitbobby+awn@gmail.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.


homepage = 'http://www.google.com/'#Google FTW

import gedit
import gtk

class WebBrowser:
    browsers = {}
    path = '/'.join(__file__.split('/')[:-1]) + '/'
    gtkmozembed = False
    
    def __init__(self, plugin, window):
        self._window = window
        self._plugin = plugin
        
        #Get an icon theme for the "favicon"
        self.icon_theme = gtk.icon_theme_get_default()
        
        #Back button (just the arrow)
        back_button = gtk.Button(stock=gtk.STOCK_GO_BACK)
        back_button.get_children()[0].get_children()[0]. \
            get_children()[1].destroy()
        back_button.set_relief(gtk.RELIEF_NONE)
        back_button.connect('clicked', self.go_back)
        
        #Forward button (just the arrow)
        forward_button = gtk.Button(stock=gtk.STOCK_GO_FORWARD)
        forward_button.get_children()[0].get_children()[0]. \
            get_children()[1].destroy()
        forward_button.set_relief(gtk.RELIEF_NONE)
        forward_button.connect('clicked', self.go_forward)
        
        #New tab button
        tab_button = gtk.Button()
        try:
            icon = self.icon_theme.load_icon('tab-new', 32, 0)
        except:
            icon = self.icon_theme.load_icon('list-add', 32, 0)
        tab_button.set_image(gtk.image_new_from_pixbuf(icon))
        tab_button.set_relief(gtk.RELIEF_NONE)
        tab_button.connect('clicked', self.new_tab)
        
        #Get a GtkEntry for the URL
        self.entry = gtk.Entry()
        self.entry.set_text(homepage)
        self.entry.connect('key-release-event', self.entry_key_release)
        self.entry.show()
        
        #Go button (just a -> arrow)
        go_button = gtk.Button(stock=gtk.STOCK_GO_FORWARD)
        go_button.get_children()[0].get_children()[0]. \
            get_children()[1].destroy()
        go_button.set_relief(gtk.RELIEF_NONE)
        go_button.connect('clicked', lambda b: self.goto_url())
        
        #HBox for the above widgets
        self.hbox = gtk.HBox()
        self.hbox.pack_start(back_button, False, False, 1)
        self.hbox.pack_start(forward_button, False, False, 1)
        self.hbox.pack_start(tab_button, False, False, 1)
        self.hbox.pack_start(self.entry, True, True, 1)
        self.hbox.pack_start(go_button, False, False, 1)
        self.hbox.show_all()
        
        #Put the HBox between the menu and main editor/pane
        vbox = window.get_children()[0]
        vbox.pack_start(self.hbox, False, False, 1)
        vbox.reorder_child(self.hbox, 2)

    def deactivate(self):
        self._window = None
        self._plugin = None
        del self.entry

    def update_ui(self):
        current_tab = self._window.get_active_tab()
        if current_tab in self.browsers.keys():
            self.entry.set_text(self.browsers[current_tab][0].get_location())
            self._window.set_title(self.browsers[current_tab][0]. \
              get_title() + ' - gedit')
    
    def goto_url(self, url=None, force=False):
        if url is None:
            url = self.entry.get_text()
        
        #Check if the current tab is a web browser tab
        current_tab = self._window.get_active_tab()
        if current_tab in self.browsers.keys() and not force:
            self.browsers[current_tab][0].load_url(self.entry.get_text())
            return False
        
        #Create a new Gedit tab
        self._window.create_tab(True)
        
        #Get some variables
        #The new Gedit tab
        tab = self._window.get_active_tab()
        
        #Web browser icon as a Pixbuf
        try:
            icon = self.icon_theme.load_icon('internet-web-browser', 16, 0)
        except:
            icon = gtk.gdk.pixbuf_new_from_file( \
                self.path + 'webbrowser/internet-web-browser.png')
        
        #The GeditNotebook (which inherits a GtkNotebook)
        notebook = self._window.get_children()[0].get_children()[3].\
            get_children()[1].get_children()[0]
        
        #Create the tab label
        label = gtk.Label('Loading')
        image = gtk.image_new_from_pixbuf(icon)
        button = notebook.get_tab_label(tab).get_children()[1]
        button.parent.remove(button)
        
        #Put the tab label together
        hbox = gtk.HBox()
        hbox.pack_start(image, False)
        hbox.pack_start(label, False, False, 3)
        hbox.pack_start(button, False)
        hbox.show_all()
        
        #Set the tab label to the tab
        notebook.set_tab_label(tab, hbox)
        
        #Import GtkMozEmbed if it hasn't been already
        #Importing it takes a little bit and can slow down the startup of
        #Gedit if it's done at startup
        if not self.gtkmozembed:
            self.gtkmozembed = __import__('gtkmozembed')
        
        #Create the GtkMozEmbed widget
        widget = self.gtkmozembed.MozEmbed()
        widget.load_url(url)
        widget.connect('title', self.title_changed, label)
        widget.connect('location', self.location_changed)
        widget.connect('open-uri', self.open_uri)
        widget.show()
        
        #Set the widget to be the widget for this tab
        #Otherwise, Gedit would load its GtkSourceView widget by default
        scrolled_window = tab.get_children()[0]
        scrolled_window.remove(scrolled_window.get_children()[0])
        scrolled_window.add_with_viewport(widget)
        
        #Keep a tab on this tab (Get it? Oh I'm so funny! I should do standup)
        self.browsers[tab] = [widget, label]
        #/sarcasm
    
    #When the title has changed - change the tab label text
    def title_changed(self, embed, label):
        label.set_text(embed.get_title())
        if self.get_active() == embed:
            self._window.set_title(embed.get_title() + ' - gedit')
    
    #When the location has changed - change the location entry text
    #(if this widget is in the current tab)
    def location_changed(self, embed):
        #There might be an easier way to do this...
        current_tab = self._window.get_active_tab()
        for tab, li in self.browsers.items():
            if tab == current_tab and li[0] == embed:
                self.entry.set_text(embed.get_location())
    
    #Not sure if this is necessary
    def open_uri(self, embed, uri):
        return False
    
    #Return the active embed, or None
    def get_active(self):
        current_tab = self._window.get_active_tab()
        for tab, li in self.browsers.items():
            if tab == current_tab:
                return li[0]
        #Python functions return None by default
    
    #Check if the user hit the enter key on the location entry widget
    def entry_key_release(self, entry, event):
        if event.keyval in (65293, 65421):
            self.goto_url()
    
    #The Go Back button was clicked
    def go_back(self, button):
        active_embed = self.get_active()
        if active_embed is not None and active_embed.can_go_back():
            active_embed.go_back()
    
    #The Go Forward button was clicked
    def go_forward(self, button):
        active_embed = self.get_active()
        if active_embed is not None and active_embed.can_go_forward():
            active_embed.go_forward()
    
    #Open a new tab (open blank page)
    def new_tab(self, button):
        self.goto_url('about:blank', True)

class WebBrowserPlugin(gedit.Plugin):
    def __init__(self):
        gedit.Plugin.__init__(self)
        self._instances = {}

    def activate(self, window):
        self._instances[window] = WebBrowser(self, window)

    def deactivate(self, window):
        self._instances[window].deactivate()
        del self._instances[window]

    def update_ui(self, window):
        self._instances[window].update_ui()
