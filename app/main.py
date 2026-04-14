import sys
import subprocess
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout,
    QLineEdit, QTextEdit
)
from core.parser import parse_query
from core.search import search_files, fast_search


class SeekrApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Seekr")
        self.setGeometry(200, 200, 700, 500)

        layout = QVBoxLayout()

        # chat display
        self.chat = QTextEdit()
        self.chat.setReadOnly(True)

        # input box
        self.input = QLineEdit()
        self.input.setPlaceholderText("Ask something...")
        self.input.returnPressed.connect(self.handle_search)

        layout.addWidget(self.chat)
        layout.addWidget(self.input)

        self.setLayout(layout)

    def add_message(self, sender, text):
        if sender == "user":
            self.chat.append(f"<b>You:</b> {text}")
        else:
            self.chat.append(f"<b>Seekr:</b><br>{text}<br>")

    def handle_search(self):
        query = self.input.text()
        if not query:
            return

        self.add_message("user", query)

        filters = parse_query(query)

        if filters["name"]:
            results = fast_search(filters)
        else:
            results = search_files(filters)

        if not results:
            response = "No files found."
        else:
            # show top 10 nicely
            response = "<br>".join(results[:10])

        self.add_message("bot", response)

        self.input.clear()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SeekrApp()
    window.show()
    sys.exit(app.exec())