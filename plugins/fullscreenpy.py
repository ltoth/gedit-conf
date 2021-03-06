import gedit, gtk
from gettext import gettext as _
# Menu item Fullscreen, insert a new item in the Tools menu
ui_str = """<ui>
  <menubar name="MenuBar">
    <menu name="ViewMenu" action="View">
      <placeholder name="ViewsOps_2">
        <menuitem name="FullscreenPy" action="FullscreenPy"/>
      </placeholder>
    </menu>
  </menubar>
</ui>
"""
class FullscreenPyWindowHelper:
        def __init__(self, plugin, window):
                self._window = window
                self._plugin = plugin
                
                # Insert menu items
                self._insert_menu()  
        
        def deactivate(self):
                # Remove any installed menu items
                self._remove_menu()
                
                # Set the window to not fullscreen
                self._window.unfullscreen()
                
                self._window = None
                self._plugin = None
                self._action_group = None

        def _insert_menu(self):
                # Get the GtkUIManager
                manager = self._window.get_ui_manager()                
                
                # Create a new action group
                self._action_group = gtk.ActionGroup("FullscreenPyPluginActions")
                self._action_group.add_toggle_actions([("FullscreenPy", None, _("Toggle Fullscreen"), "F11", _("Toggle Fullscreen"), lambda a: self.on_toggle_fullscreen_activate())])

                # Insert the action group
                manager.insert_action_group(self._action_group, -1)

                # Merge the UI
                self._ui_id = manager.add_ui_from_string(ui_str)
        def _remove_menu(self):
                # Get the GtkUIManager
                manager = self._window.get_ui_manager()

                # Remove the ui
                manager.remove_ui(self._ui_id)

                # Remove the action group
                manager.remove_action_group(self._action_group)

                # Make sure the manager updates
                manager.ensure_update()
        def update_ui(self):
                self._action_group.set_sensitive(self._window.get_active_document() != None)
        # Menu activate handlers
        def on_toggle_fullscreen_activate(self):
            # Test if already fullscreen, and toggle appropriately
            if (self._window.window.get_state() & gtk.gdk.WINDOW_STATE_FULLSCREEN):
                self._window.unfullscreen()
            else:
                self._window.fullscreen()

class FullscreenPyPlugin(gedit.Plugin):
        DATA_TAG = "FullscreenPyPluginInstance"

        def __init__(self):
                gedit.Plugin.__init__(self)
        def _get_instance(self, window):
                return window.get_data(self.DATA_TAG)

        def _set_instance(self, window, instance):
                window.set_data(self.DATA_TAG, instance)

        def activate(self, window):
                self._set_instance(window, FullscreenPyWindowHelper(self, window))
        def deactivate(self, window):
                self._get_instance(window).deactivate()
                self._set_instance(window, None)

        def update_ui(self, window):
                self._get_instance(window).update_ui()

