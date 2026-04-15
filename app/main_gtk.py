import gi
import os
import subprocess
import threading
import urllib.parse
import keyring  # 🚀 NEW: Secure credential storage

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("GLib", "2.0")

from gi.repository import Gtk, Adw, GLib

from core.router import get_filters
# 🚀 NEW: Replaced search_files with our DB and Indexer modules
from storage.db import init_db, search_db
from core.indexer import build_index


APP_NAME = "Seekr"
APP_VERSION = "v1.0"


class SeekrWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)

        self.set_title(APP_NAME)
        self.set_default_size(720, 520)

        # 🔥 Toolbar view (modern Adwaita layout)
        toolbar_view = Adw.ToolbarView()

        # 🔹 Header bar
        header = Adw.HeaderBar()

        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        title = Gtk.Label(label=APP_NAME)
        title.set_xalign(0.5)
        title.add_css_class("title")

        subtitle = Gtk.Label(label=APP_VERSION)
        subtitle.set_xalign(0.5)
        subtitle.add_css_class("dim-label")

        title_box.append(title)
        title_box.append(subtitle)
        header.set_title_widget(title_box)

        toolbar_view.add_top_bar(header)

        # 🍞 Toast Overlay (For showing slick error messages)
        self.toast_overlay = Adw.ToastOverlay()

        # 🔹 Main content box
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_top(16)
        box.set_margin_bottom(16)
        box.set_margin_start(16)
        box.set_margin_end(16)

        # 🔹 Search Entry
        self.entry = Gtk.Entry()
        self.entry.set_placeholder_text("Search files...")
        self.entry.connect("activate", self.on_search)

        # 📚 Gtk.Stack (To swap between UI states)
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self.stack.set_vexpand(True)

        # 🔐 State 0: The Setup/Onboarding Screen (NEW)
        self.status_setup = Adw.StatusPage(
            icon_name="dialog-password-symbolic",
            title="Welcome to Seekr",
            description="To power the smart search, please enter your Groq API Key."
        )
        
        setup_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        setup_box.set_halign(Gtk.Align.CENTER)
        setup_box.set_size_request(350, -1)

        self.key_entry = Adw.PasswordEntryRow()
        self.key_entry.set_title("Groq API Key")
        
        preferences_group = Adw.PreferencesGroup()
        preferences_group.add(self.key_entry)

        save_button = Gtk.Button(label="Save & Continue")
        save_button.add_css_class("suggested-action") 
        save_button.connect("clicked", self.on_save_key)

        setup_box.append(preferences_group)
        setup_box.append(save_button)
        self.status_setup.set_child(setup_box)

        #   State 1: Initial/Idle Status Page
        self.status_idle = Adw.StatusPage(
            icon_name="system-search-symbolic",
            title="Ready to Search",
            description="Type a query above to find your files."
        )

        #   State 2: Searching Status Page
        self.status_searching = Adw.StatusPage(
            icon_name="view-refresh-symbolic",
            title="Searching...",
            description="Scanning your directories."
        )

        #   State 3: No Results Status Page
        self.status_empty = Adw.StatusPage(
            icon_name="edit-clear-all-symbolic",
            title="No Results Found",
            description="Try adjusting your query or filters."
        )

        #   State 4: The Results List
        scrolled = Gtk.ScrolledWindow()
        self.listbox = Gtk.ListBox()
        self.listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.listbox.connect("row-activated", self.on_open)
        scrolled.set_child(self.listbox)

        # Add all states to the stack
        self.stack.add_named(self.status_setup, "setup")
        self.stack.add_named(self.status_idle, "idle")
        self.stack.add_named(self.status_searching, "searching")
        self.stack.add_named(self.status_empty, "empty")
        self.stack.add_named(scrolled, "results")

        box.append(self.entry)
        box.append(self.stack)

        # Wrap the box in the toast overlay, then attach to toolbar
        self.toast_overlay.set_child(box)
        toolbar_view.set_content(self.toast_overlay)

        self.set_content(toolbar_view)

        # 🔥 Check API Key on Startup
        self.check_api_key()

    # 🔐 KEYRING: Check if API key is saved
    def check_api_key(self):
        saved_key = keyring.get_password("seekr_app", "groq_api_key")
        
        if saved_key:
            os.environ["GROQ_API_KEY"] = saved_key 
            self.stack.set_visible_child_name("idle")
            self.entry.set_sensitive(True)
            
            # Start the invisible background indexer
            init_db()
            threading.Thread(target=build_index, daemon=True).start()
        else:
            # Lock app to setup screen
            self.stack.set_visible_child_name("setup")
            self.entry.set_sensitive(False)

    # 🔐 KEYRING: Save new API key
    def on_save_key(self, button):
        new_key = self.key_entry.get_text().strip()
        
        if not new_key.startswith("gsk_"): 
            self.show_toast("Invalid API Key format.")
            return
            
        keyring.set_password("seekr_app", "groq_api_key", new_key)
        self.show_toast("API Key saved securely!")
        
        os.environ["GROQ_API_KEY"] = new_key
        self.stack.set_visible_child_name("idle")
        self.entry.set_sensitive(True)
        self.entry.grab_focus()

        # Start DB and indexer now that we have access
        init_db()
        threading.Thread(target=build_index, daemon=True).start()

    # 🔍 1. Triggered when the user hits Enter
    def on_search(self, entry):
        query = entry.get_text().strip()

        if not query:
            self.stack.set_visible_child_name("idle")
            self.clear_results()
            return

        # Show the searching animation page
        self.stack.set_visible_child_name("searching")
        self.clear_results()
        
        self.entry.set_sensitive(False)

        thread = threading.Thread(target=self._run_search_thread, args=(query,), daemon=True)
        thread.start()

    # ⚙️ 2. The Heavy Lifting (Background)
    def _run_search_thread(self, query):
        filters = get_filters(query)
        
        # 🚀 NEW: Query the SQLite DB instead of the hard drive
        results = search_db(filters)

        GLib.idle_add(self._update_ui_with_results, results)

    # 🎨 3. Updating the Screen (Main Thread)
    def _update_ui_with_results(self, results):
        self.entry.set_sensitive(True)
        self.entry.grab_focus()

        if not results:
            self.stack.set_visible_child_name("empty")
            return False

        # Switch view to the results list
        self.stack.set_visible_child_name("results")

        for path in results[:50]:
            self.add_result_row(path)
            
        return False 

    # 📄 Add result row
    def add_result_row(self, path):
        filename = os.path.basename(path)
        directory = os.path.dirname(path)

        row = Adw.ActionRow()
        row.set_title(filename)
        row.set_subtitle(directory)
        
        # 🔥 REQUIRED: Make the ActionRow clickable
        row.set_activatable(True)

        icon = Gtk.Image.new_from_icon_name("text-x-generic-symbolic")
        row.add_prefix(icon)

        row.path = path

        self.listbox.append(row)

    # 📂 Open file manager and highlight the file
    def on_open(self, listbox, row):
        path = getattr(row, "path", None)

        if not path:
            return

        # Check if the file still exists
        if not os.path.exists(path):
            self.show_toast("File no longer exists. It may have been moved or deleted.")
            return

        # 1. Try the standard Linux DBus method to reveal and highlight the file
        try:
            file_uri = f"file://{urllib.parse.quote(path)}"
            subprocess.run([
                "dbus-send", "--session", "--dest=org.freedesktop.FileManager1",
                "--type=method_call", "/org/freedesktop/FileManager1",
                "org.freedesktop.FileManager1.ShowItems",
                f"array:string:{file_uri}", "string:"
            ], check=True)
            
        except Exception:
            # 2. Fallback: If DBus fails for some reason, just open the folder
            directory = os.path.dirname(path)
            try:
                subprocess.run(["xdg-open", directory], check=True)
            except Exception as e:
                self.show_toast(f"Failed to open directory: {str(e)}")

    # 🍞 Helper to show UI notifications
    def show_toast(self, message):
        toast = Adw.Toast(title=message)
        self.toast_overlay.add_toast(toast)

    # 🧹 Clear results
    def clear_results(self):
        while True:
            child = self.listbox.get_first_child()
            if not child:
                break
            self.listbox.remove(child)


class SeekrApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id="com.seekr.app")

    def do_activate(self):
        win = SeekrWindow(self)
        win.present()


if __name__ == "__main__":
    app = SeekrApp()
    app.run([])