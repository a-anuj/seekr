import gi
import os
import subprocess
import threading
import urllib.parse
import keyring

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
gi.require_version("GLib", "2.0")
gi.require_version("Pango", "1.0")

from gi.repository import Gtk, Adw, GLib, Pango

from app.core.router import get_filters
from app.storage.db import init_db, search_db
from app.core.indexer import build_index


APP_NAME = "Seekr"
APP_VERSION = "v1.0"


def format_size(size_bytes: int | None) -> str:
    """Return a human-readable file size string."""
    if size_bytes is None:
        return ""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.1f} KB"
    if size_bytes < 1024 ** 3:
        return f"{size_bytes / 1024 ** 2:.1f} MB"
    return f"{size_bytes / 1024 ** 3:.2f} GB"


def format_snippet_markup(raw: str) -> str:
    """
    Convert FTS5 snippet with ** markers into Pango markup with bold highlights.
    E.g. "foo **bar** baz" → "foo <b>bar</b> baz"
    """
    # Escape the whole string for Pango, then re-insert bold tags
    escaped = GLib.markup_escape_text(raw)
    parts = escaped.split("**")
    result = ""
    for i, part in enumerate(parts):
        result += f"<b>{part}</b>" if i % 2 == 1 else part
    return result


class SeekrWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_icon_name("com.seekr.app")
        

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

        # search_db now returns [(path, snippet_or_None, size_bytes), ...]
        results = search_db(filters)

        GLib.idle_add(self._update_ui_with_results, results)

    # 🎨 3. Updating the Screen (Main Thread)
    def _update_ui_with_results(self, results):
        self.entry.set_sensitive(True)
        self.entry.grab_focus()

        if not results:
            self.stack.set_visible_child_name("empty")
            return False

        self.stack.set_visible_child_name("results")

        for path, snippet, size in results[:50]:
            self.add_result_row(path, snippet=snippet, size_bytes=size)

        return False

    # 📄 Add a rich result row: filename + size + directory + optional bold snippet
    def add_result_row(self, path: str, snippet: str | None = None, size_bytes: int | None = None):
        filename  = os.path.basename(path)
        directory = os.path.dirname(path)

        # ── Outer row (makes the whole thing clickable) ───────────────────────
        outer_row = Gtk.ListBoxRow()
        outer_row.path = path

        # ── Horizontal container: icon | text block ───────────────────────────
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        hbox.set_margin_top(10)
        hbox.set_margin_bottom(10)
        hbox.set_margin_start(14)
        hbox.set_margin_end(14)

        icon_name = "edit-find-symbolic" if snippet else "text-x-generic-symbolic"
        icon = Gtk.Image.new_from_icon_name(icon_name)
        icon.set_valign(Gtk.Align.START)
        icon.set_margin_top(2)
        hbox.append(icon)

        # ── Vertical text block ───────────────────────────────────────────────
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        vbox.set_hexpand(True)

        # Row 1: filename (bold) + size (right-aligned, dim)
        title_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)

        name_label = Gtk.Label(label=filename)
        name_label.set_xalign(0.0)
        name_label.set_hexpand(True)
        name_label.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
        name_label.add_css_class("heading")
        title_row.append(name_label)

        if size_bytes is not None:
            size_label = Gtk.Label(label=format_size(size_bytes))
            size_label.set_xalign(1.0)
            size_label.add_css_class("dim-label")
            size_label.add_css_class("caption")
            title_row.append(size_label)

        vbox.append(title_row)

        # Row 2: directory path (dim, ellipsized from start)
        dir_label = Gtk.Label(label=directory)
        dir_label.set_xalign(0.0)
        dir_label.set_ellipsize(Pango.EllipsizeMode.START)
        dir_label.add_css_class("dim-label")
        dir_label.add_css_class("caption")
        vbox.append(dir_label)

        # Row 3 (optional): content snippet with bold highlights
        if snippet:
            snip_label = Gtk.Label()
            snip_label.set_markup(format_snippet_markup(snippet))
            snip_label.set_xalign(0.0)
            snip_label.set_ellipsize(Pango.EllipsizeMode.END)
            snip_label.add_css_class("caption")
            vbox.append(snip_label)

        hbox.append(vbox)
        outer_row.set_child(hbox)
        self.listbox.append(outer_row)

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

def main():
    app = SeekrApp()
    app.run([])

if __name__ == "__main__":
    app = SeekrApp()
    app.run([])