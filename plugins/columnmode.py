# -*- coding: utf-8 -*-

#  columnmode.py - Column-mode editing for gedit.
#  
#  Copyright (C) 2007 - Stefan Schweizer
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#   
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#   
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330,
#  Boston, MA 02111-1307, USA.

import string

import gtk
import gedit
from gettext import gettext as _

ui_str = """
<ui>
  <menubar name="MenuBar">
    <menu name="EditMenu" action="Edit">
      <placeholder name="EditOps_4">
        <menuitem name="ColumnMode" action="ColumnMode" />
      </placeholder>
    </menu>
  </menubar>
</ui>
"""

class ColumnModeWindowHelper(object):

    VIEW_DATA_KEY = "ColumnModePluginViewData"    
    
    def __init__(self, plugin, window):
        self._window = window
        self._plugin = plugin
        self._checkbox = None
        self.insert_menu()
        
        for view in window.get_views():
            self.add_helper(view)
        
        self._handler_tab_added = window.connect("tab-added",
                                  lambda w, t: self.add_helper(t.get_view()))
        self._handler_tab_changed = window.connect("active-tab-changed",
                                    self.update_menu_checkbox)

    def __del__(self):
        self._window = None
        self._plugin = None
        self._checkbox = None
    
    def deactivate(self):
        self._window.disconnect(self._handler_tab_changed)
        self._window.disconnect(self._handler_tab_added)
        
        for view in self._window.get_views():
            self.remove_helper(view)
        
        self.remove_menu()

    def insert_menu(self):
        manager = self._window.get_ui_manager()

        self._action_group = gtk.ActionGroup("ColumnModePluginActions")
        self._action_group.add_toggle_actions([
                            ("ColumnMode", None, _("Column Mode"), "<alt>C",
                            _("Toggle column mode"), self.toggle_column_mode)
                ])

        manager.insert_action_group(self._action_group, -1)
        self._ui_id = manager.add_ui_from_string(ui_str)

    def remove_menu(self):
        manager = self._window.get_ui_manager()
        manager.remove_ui(self._ui_id)
        manager.remove_action_group(self._action_group)
        manager.ensure_update()
    
    def add_helper(self, view):
        helper = ColumnModeViewHelper(view)
        view.set_data(self.VIEW_DATA_KEY, helper)
    
    def remove_helper(self, view):
        view.get_data(self.VIEW_DATA_KEY).deactivate()
        view.set_data(self.VIEW_DATA_KEY, None)
    
    def update_menu_checkbox(self, window, tab):
        """Update menu checkbox with current state from view."""
        helper = tab.get_view().get_data(self.VIEW_DATA_KEY)
        if self._checkbox:
            self._checkbox.set_active(helper._column_mode)
        
    def toggle_column_mode(self, checkbox):
        """Activate/deactivate column mode for active view."""
        self._checkbox = checkbox
        helper = self._window.get_active_view().get_data(self.VIEW_DATA_KEY)
        state = helper.toggle_column_mode(checkbox.get_active())
        checkbox.set_active(state)

class ColumnModeViewHelper(object):
    
    def __init__(self, view):
        self._view = view
        self._column_mode = False
        self._column_marks = []
        
        self._handlers = [
            None,
            view.connect("notify::editable", self.on_notify)
        ]
        self.update_active()
    
    def __del__(self):
        self._view = None
    
    def deactivate(self):
        for handler in self._handlers:
            if handler is not None:
                self._view.disconnect(handler)

    def update_active(self):
        active = self._column_mode and self._view.get_editable()

        if active and self._handlers[0] is None:
            self._handlers[0] = self._view.connect("key-press-event",
                                                   self.on_key_press_event)
        elif not active and self._handlers[0] is not None:
            self.clear_column_marks()
            self._view.disconnect(self._handlers[0])
            self._handlers[0] = None
        
        return active
    
    def on_notify(self, view, pspec):
        self.update_active()
    
    def toggle_column_mode(self, enabled):
        self._column_mode = enabled
        return self.update_active()
    
    def clear_column_marks(self):
        while len(self._column_marks) > 0:
            mark = self._column_marks.pop()
            mark.set_visible(False)
            self._view.get_buffer().delete_mark(mark)
    
    def on_key_press_event(self, view, event):
        doc = view.get_buffer()
        insert_iter = doc.get_iter_at_mark(doc.get_insert())
        line_offset = insert_iter.get_line_offset()
        ret_val = False
        
        # Clear column marks for events with non-SHIFT modifiers (copy, ...)
        if (event.state != 0 and event.state != gtk.gdk.SHIFT_MASK
            and event.state != gtk.gdk.MOD2_MASK
            and event.state != gtk.gdk.MOD3_MASK
            and event.state != gtk.gdk.MOD4_MASK
            and event.state != gtk.gdk.MOD5_MASK):
            self.clear_column_marks()
        
        # Select column marks when SHIFT is held down
        elif event.state == gtk.gdk.SHIFT_MASK and \
             event.keyval in (gtk.keysyms.Up, gtk.keysyms.Down):
            
            old_position = insert_iter.copy()
            
            # Move cursor to new position if not in first or last line
            new_line = False
            if event.keyval == gtk.keysyms.Up and insert_iter.get_line() != 0:
                new_line = insert_iter.backward_line()
            elif event.keyval == gtk.keysyms.Down and \
                 insert_iter.get_line() != doc.get_line_count() - 1:
                new_line = insert_iter.forward_line()
            
            if new_line:    
                current_line = insert_iter.get_line()
                insert_iter.forward_chars(line_offset)
                
                # The new line must be long enough
                if current_line == insert_iter.get_line():
                    doc.place_cursor(insert_iter)
                    # Create mark at old position
                    name = "ColumnMode" + str(len(self._column_marks))
                    mark = doc.create_mark(name, old_position, left_gravity=False)
                    mark.set_visible(True)
                    self._column_marks.append(mark)           
            
            ret_val = True
        
        # Clear column marks when moving around with arrow keys
        elif event.keyval in (gtk.keysyms.Up, gtk.keysyms.Down,
                              gtk.keysyms.Left, gtk.keysyms.Right,
                              gtk.keysyms.Return):
            self.clear_column_marks()
        
        # Nothing to do
        elif not self._column_marks:
            pass
        
        # BACKSPACE 
        elif event.keyval == gtk.keysyms.BackSpace:
            if line_offset == 0:
                # Don't delete from start of line backwards
                ret_val = True
            else:
                for mark in self._column_marks:
                    start = doc.get_iter_at_mark(mark)
                    end = start.copy()
                    end.backward_char()
                    doc.delete(start, end)
        
        # DEL
        elif event.keyval == gtk.keysyms.Delete:
            if insert_iter.get_char() in ("\r", "\n"):
                # Don't delete CR or LF at cursor position
                ret_val = True
            for mark in self._column_marks:
                start = doc.get_iter_at_mark(mark)
                end = start.copy()
                end.forward_char()
                # Never delete CR or LF
                if start.get_char() not in ("\r", "\n"):
                    doc.delete(start, end)
        
        # TAB
        elif event.keyval == gtk.keysyms.Tab:
            if self._view.get_insert_spaces_instead_of_tabs():
                tab = " " * self._view.get_tabs_width()
            else:
                tab = "\t"
            for mark in self._column_marks:
                doc.insert(doc.get_iter_at_mark(mark), tab)
        
        # Insert printable string at all marked positions
        elif event.string in string.printable:
            for mark in self._column_marks:
                doc.insert(doc.get_iter_at_mark(mark), event.string)
        
        return ret_val

class ColumnModePlugin(gedit.Plugin):
    
    WINDOW_DATA_KEY = "ColumnModePluginWindowData"
    
    def __init__(self):
        gedit.Plugin.__init__(self)

    def activate(self, window):
        helper = ColumnModeWindowHelper(self, window)
        window.set_data(self.WINDOW_DATA_KEY, helper)
    
    def deactivate(self, window):
        window.get_data(self.WINDOW_DATA_KEY).deactivate()        
        window.set_data(self.WINDOW_DATA_KEY, None)
        
    def update_ui(self, window):
        pass

# ex:ts=4:et:
