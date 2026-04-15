import gi
import os
import subprocess
import threading

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("GLib", "2.0")

from gi.repository import Gtk, Adw, GLib

from core.router import get_filters
from core.search import search_files, fast_search


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

        # 🔹 Title container
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

        # 🔹 Main content
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_margin_top(16)
        box.set_margin_bottom(16)
        box.set_margin_start(16)
        box.set_margin_end(16)

        # 🔹 Search Entry
        self.entry = Gtk.Entry()
        self.entry.set_placeholder_text("Search files...")
        self.entry.connect("activate", self.on_search)

        # 🔹 Scrollable results
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)

        self.listbox = Gtk.ListBox()
        self.listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.listbox.connect("row-activated", self.on_open)

        scrolled.set_child(self.listbox)

        box.append(self.entry)
        box.append(scrolled)

        # 🔥 attach content properly
        toolbar_view.set_content(box)

        # Set the toolbar view as the sole content of the window
        self.set_content(toolbar_view)

    # 🔍 1. Triggered when the user hits Enter (Runs on Main GUI Thread)
    def on_search(self, entry):
        query = entry.get_text().strip()

        self.clear_results()

        if not query:
            return

        self.add_message("Searching...")
        
        # Lock the entry so the user can't spam searches
        self.entry.set_sensitive(False)

        # Fire off the background thread
        thread = threading.Thread(target=self._run_search_thread, args=(query,), daemon=True)
        thread.start()

    # ⚙️ 2. The Heavy Lifting (Runs in Background Thread)
    def _run_search_thread(self, query):
        filters = get_filters(query)

        if filters.get("name"):
            results = fast_search(filters)
        else:
            results = search_files(filters)

        # Safely pass the results back to the Main GUI Thread
        GLib.idle_add(self._update_ui_with_results, results)

    # 🎨 3. Updating the Screen (Runs back on the Main GUI Thread)
    def _update_ui_with_results(self, results):
        self.clear_results()
        
        # Unlock the entry box
        self.entry.set_sensitive(True)
        self.entry.grab_focus()

        if not results:
            self.add_message("No results found")
            return False # Required to stop GLib from looping this function

        for path in results[:50]:
            self.add_result_row(path)
            
        return False # Required to stop GLib from looping this function

    # 📄 Add result row
    def add_result_row(self, path):
        filename = os.path.basename(path)
        directory = os.path.dirname(path)

        row = Gtk.ListBoxRow()

        label = Gtk.Label(
            label=f"{filename}\n{directory}",
            xalign=0
        )

        row.set_child(label)

        # ✅ GTK4 safe way to attach custom data to a row
        row.path = path

        self.listbox.append(row)

    # 📂 Open folder
    def on_open(self, listbox, row):
        path = getattr(row, "path", None)

        if path:
            directory = os.path.dirname(path)
            # Added a try/except block to handle missing folders gracefully
            try:
                subprocess.run(["xdg-open", directory], check=True)
            except Exception as e:
                print(f"Failed to open {directory}: {e}")

    # 🧹 Clear results
    def clear_results(self):
        while True:
            child = self.listbox.get_first_child()
            if not child:
                break
            self.listbox.remove(child)

    # 💬 Add message row
    def add_message(self, text):
        row = Gtk.ListBoxRow()
        label = Gtk.Label(label=text)
        row.set_child(label)
        self.listbox.append(row)


class SeekrApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id="com.seekr.app")

    def do_activate(self):
        win = SeekrWindow(self)
        win.present()


if __name__ == "__main__":
    app = SeekrApp()
    app.run([])