# Elastic tabstops converter
# convert between using spaces to align columns and elastic tabstops
# (for use with versions of Gedit that support elastic tabstops)
# see: http://nickgravgaard.com/elastictabstops
#
# This version released: 2007-05-10 (first release)
#
# Copyright (C) 2007 Nick Gravgaard
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import gedit
import gtk
import os.path


def cell_exists(listoflists, x, y):
    """Check that an item exists in a list of lists."""
    try:
        test = listoflists[x][y]
        return True
    except IndexError:
        return False


def unique(s):
    """Return a list of the elements in s, but without duplicates."""

    if len(s) == 0:
        return []

    u = {}
    for x in s:
        u[x] = 1
    return u.keys()


class ElasticTabstopsConverterPlugin(gedit.Plugin):
    def __init__(self):
        gedit.Plugin.__init__(self)
        self.id_name = 'ElasticTabstopsConverterPluginID'
        self.convertOnLoadSaveEnabled = False # change to True to enable convertonloadsave by default
        self.tabsize = 0 # this is overwritten
        self.unusedchar = '\0' # misuse of null char, but avoids unicode conversion
        #self.unusedchar = u'\ufffc' # Unicode Object Replacement char
        #self.unusedchar = u'\ue000' # Unicode Private Use Area char
        return


    def calc_fixed_cell_size(self, textlen):
        try:
            # we add two to provide padding
            # only adding one would be too small since it could be confused for a non-aligning space when importing the file later
            return (int((textlen + 2) / self.tabsize) + 1) * self.tabsize
        except ZeroDivisionError:
            return self.tabsize


    def replace_multiple_spaces(self, text):
        # if it's just a single space replace it
        if text == " ":
            return self.unusedchar

        numspaces = 0
        newtext = []
        for i in range(len(text)):
            if text[i] == ' ':
                numspaces += 1
            else:
                if numspaces == 1:
                    newtext.append(' ')
                elif numspaces >= 2:
                    for j in range(numspaces):
                        newtext.append(self.unusedchar)
                numspaces = 0
                newtext.append(text[i])

        if numspaces == 1:
            newtext.append(' ')
        elif numspaces >= 2:
            for j in range(numspaces):
                newtext.append(self.unusedchar)

        return ''.join(newtext)


    def convert_to_elastic_tabstops(self, text):
        """Expand tabs to unusedchars instead of spaces, and replace runs of more than one space with the same number of unusedchars."""
        tokenised = []
        text = text.replace('\r\n', '\n')
        text = text.replace('\r', '\n')
        lines = text.split('\n')
        for linenum in range(len(lines)):
            cells = lines[linenum].split('\t')
            for cellnum in range(len(cells)):
                cell = self.replace_multiple_spaces(cells[cellnum])
                tokenised.append(cell)
                if cellnum < len(cells) - 1:
                    # assume that any tabs are indended to align text with fixed column tabstops
                    tokenised.append(self.unusedchar * (self.tabsize - len(cell) % self.tabsize))
            if linenum < len(lines) - 1:
                tokenised.append('\n')

        replacedtext = ''.join(tokenised)
        tokenised = replacedtext.split('\n')

        linestextposs = []
        linescells = []
        maxcells = 0
        finallines = []

        # get cell's contents and positions
        for linenum in range(len(tokenised)):
            finallines.append([])
            textposs = []
            linestextposs.append(textposs)
            cells = []
            linescells.append(cells)
            line = tokenised[linenum]
            incell = False
            startpos = 0
            endpos = 0
            cellcontents = ""
            numcells = 0
            charnum = 0
            for charnum in range(len(line)):
                if line[charnum] != self.unusedchar:
                    if incell == False:
                        textposs.append(charnum)
                        startpos = charnum
                        incell = True
                        numcells += 1
                    endpos = charnum
                else:
                    if incell == True:
                        endpos = charnum
                        cellcontents = line[startpos:endpos]
                        cells.append(cellcontents)
                        incell = False
            if incell == True:
                endpos = charnum
                cellcontents = line[startpos:endpos + 1]
                cells.append(cellcontents)

            if numcells > maxcells:
                maxcells = numcells

        numlines = len(linescells)

        # not a for cellnum in (range(maxcells)) loop because maxcells may increase 
        cellnum = 0
        while cellnum < maxcells:
            startingnewblock = True
            startrange = 0
            endrange = 0

            for linenum in range(numlines):
                if not cell_exists(linestextposs, linenum, cellnum):
                    # end column block
                    if startingnewblock == False:
                        slicedlist = []
                        for blockcellnum in range(startrange, endrange + 1):
                            slicedlist.append(linestextposs[blockcellnum][cellnum])

                        sortedlist = sorted(unique(slicedlist))
                        minindent = min(slicedlist)
                        for blockcellnum in range(len(slicedlist)):
                            key = slicedlist[blockcellnum]
                            if slicedlist[blockcellnum] > minindent:
                                # shift cells across
                                linescells[startrange + blockcellnum].insert(cellnum, "")
                                linestextposs[startrange + blockcellnum].insert(cellnum, 0)
                                cells_in_line = len(linescells[startrange + blockcellnum])
                                if maxcells < cells_in_line:
                                    maxcells = cells_in_line

                        startingnewblock = True
                        maxwidth = 0
                else:
                    if startingnewblock == True:
                        startrange = linenum
                        startingnewblock = False
                    endrange = linenum

            if startingnewblock == False:
                slicedlist = []
                for blockcellnum in range(startrange, endrange + 1):
                    slicedlist.append(linestextposs[blockcellnum][cellnum])

                sortedlist = sorted(unique(slicedlist))
                minindent = min(slicedlist)
                for blockcellnum in range(len(slicedlist)):
                    key = slicedlist[blockcellnum]
                    if slicedlist[blockcellnum] > minindent:
                        # shift cells across
                        linescells[startrange + blockcellnum].insert(cellnum, "")
                        linestextposs[startrange + blockcellnum].insert(cellnum, 0)
                        cells_in_line = len(linescells[startrange + blockcellnum])
                        if maxcells < cells_in_line:
                            maxcells = cells_in_line

            cellnum += 1

        for cellnum in range(maxcells):
            for linenum in range(numlines):
                if cell_exists(linescells, linenum, cellnum):
                    if cellnum > 0:
                        finallines[linenum].append('\t')
                    finallines[linenum].append(linescells[linenum][cellnum])

        newtext = ""

        for linenum in range(numlines):
            line = finallines[linenum]
            for cellnum in range(len(line)):
                newtext += line[cellnum]
            if linenum < numlines - 1:
                newtext += "\n"

        return newtext


    def convert_to_spaces(self, text):
        lines = []
        sizes = []
        maxcells = 0

        text = text.replace('\r\n', '\n')
        text = text.replace('\r', '\n')

        for line in text.split('\n'):
            cells = line.split('\t')
            numcells = len(cells)
            if numcells > maxcells:
                maxcells = len(cells)
            lines.append(cells)

            linesizes = []
            for cell in cells:
                celllength = self.calc_fixed_cell_size(len(cell))
                linesizes.append(celllength)
            sizes.append(linesizes)

        numlines = len(lines)

        for cellnum in range(maxcells):
            startingnewblock = True
            startrange = 0
            endrange = 0
            maxwidth = 0
            for linenum in range(numlines):
                 if cell_exists(sizes, linenum, cellnum + 1) and cell_exists(sizes, linenum, cellnum):
                     if startingnewblock == True:
                         startrange = linenum
                         startingnewblock = False
                     if maxwidth < sizes[linenum][cellnum]:
                         maxwidth = sizes[linenum][cellnum]
                     endrange = linenum
                 else:
                     # end column block
                     if startingnewblock == False:

                         for blockcellnum in range(startrange, endrange + 1):
                             sizes[blockcellnum][cellnum] = maxwidth

                         startingnewblock = True
                         maxwidth = 0

            if startingnewblock == False:
                for blockcellnum in range(startrange, endrange + 1):
                    sizes[blockcellnum][cellnum] = maxwidth

        # append text and spaces to newtext
        newtext = ""
        for linenum in range(numlines):
            for cellnum in range(maxcells):
                try:
                    if cellnum < len(lines[linenum]) - 1:
                        numspaces = sizes[linenum][cellnum] - len(lines[linenum][cellnum])
                        newtext += lines[linenum][cellnum] + (' ' * numspaces)
                    else:
                        newtext += lines[linenum][cellnum]
                except IndexError:
                    pass
            if linenum < numlines - 1:
                newtext += "\n"

        return newtext


    def convert_to_elastic_tabstops_action(self, widget, window):
        doc = window.get_active_document()
        self.tabsize = window.get_active_view().get_tabs_width()
        start, end = doc.get_bounds()
        text = doc.get_text(start, end)

        newtext = self.convert_to_elastic_tabstops(text)

        doc.begin_user_action() # begins single undo/redo action
        doc.delete(start, end)
        doc.insert(start, newtext)
        doc.end_user_action()
        return


    def convert_to_spaces_action(self, widget, window):
        doc = window.get_active_document()
        self.tabsize = window.get_active_view().get_tabs_width()
        start, end = doc.get_bounds()
        text = doc.get_text(start, end)

        newtext = self.convert_to_spaces(text)

        doc.begin_user_action() # begins single undo/redo action
        doc.delete(start, end)
        doc.insert(start, newtext)
        doc.end_user_action()
        return


    def convert_on_load_save_action(self, widget, window):
        self.convertOnLoadSaveEnabled = (self.convertOnLoadSaveEnabled == False)
        return


    def activate(self, window):
        """Activate plugin."""

        handler_id = window.connect('tab-added', self.on_window_tab_added)
        window.set_data(self.id_name, handler_id)
        self.window = window

        for doc in window.get_documents():
            self.connect_document(doc)

        actions = [
            ("converttoelastictabstops", gtk.STOCK_INDENT,
            "Reindent using tabs (elastic tabstops)", None,
            "Reindent using tabs (elastic tabstops)",
            self.convert_to_elastic_tabstops_action),
            ("converttospaces", gtk.STOCK_INDENT,
            "Reindent using spaces", None,
            "Reindent using spaces",
            self.convert_to_spaces_action)
        ]

        toggleactions = [
            ("convertonloadsave", None,
            "Convert to/from elastic tabstops on load/save", None,
            "Convert to/from elastic tabstops on load/save",
            self.convert_on_load_save_action, self.convertOnLoadSaveEnabled)
        ]

        # store as window data in the window object
        windowdata = dict()
        window.set_data("ElasticTabstopsConvertererPluginWindowDataKey", windowdata)

        windowdata["action_group"] = gtk.ActionGroup("GeditElasticTabstopsConvertererPluginActions")
        #windowdata["action_group"].set_translation_domain(GETTEXT_PACKAGE)
        windowdata["action_group"].add_actions(actions, window)
        windowdata["action_group"].add_toggle_actions(toggleactions, window)

        manager = window.get_ui_manager()
        manager.insert_action_group(windowdata["action_group"], -1)
        windowdata["ui_id"] = manager.new_merge_id ()

        submenu = '''<ui>
          <menubar name="MenuBar">
            <menu name="ToolsMenu" action="Tools">
              <placeholder name="ToolsOps_2">
                <menuitem action="converttoelastictabstops"/>
                <menuitem action="converttospaces"/>
                <menuitem action="convertonloadsave" />
              </placeholder>
            </menu>
          </menubar>
        </ui>'''

        manager.add_ui_from_string(submenu)
        return


    def connect_document(self, doc):
        """Connect to document's signals."""

        handler_id = doc.connect('loaded', self.on_document_loaded)
        doc.set_data(self.id_name, [handler_id])

        handler_id = doc.connect('saved', self.on_document_saved)
        doc.set_data(self.id_name, handler_id)
        return


    def deactivate(self, window):
        windowdata = window.get_data("ElasticTabstopsConvertererPluginWindowDataKey")
        manager = window.get_ui_manager()
        manager.remove_ui(windowdata["ui_id"])
        manager.remove_action_group(windowdata["action_group"])
        return


    def on_document_loaded(self, doc, *args):
        """Called on recieving Loaded signal"""

        if self.convertOnLoadSaveEnabled:
            self.tabsize = self.window.get_active_view().get_tabs_width()
            start, end = doc.get_bounds()
            text = doc.get_text(start, end)

            newtext = self.convert_to_elastic_tabstops(text)

            doc.delete(start, end)
            doc.insert(start, newtext)

        return


    def on_document_saved(self, doc, *args):
        """Called on recieving Saved signal"""

        if self.convertOnLoadSaveEnabled:
            self.tabsize = self.window.get_active_view().get_tabs_width()
            start, end = doc.get_bounds()
            text = doc.get_text(start, end)

            newtext = self.convert_to_spaces(text)

            filename = os.path.abspath(doc.get_uri_for_display())
            filehandle = open(filename, "w")
            filehandle.write(newtext)
            filehandle.close()

        return


    def on_window_tab_added(self, window, tab):
        """Connect the document in tab."""

        self.connect_document(tab.get_document())
        return


    def update_ui(self, window):
        view = window.get_active_view()
        windowdata = window.get_data("ElasticTabstopsConvertererPluginWindowDataKey")
        windowdata["action_group"].set_sensitive(bool(view and view.get_editable()))
        return
