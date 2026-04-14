import sys
import os
import subprocess
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLineEdit,
    QListWidget, QListWidgetItem, QLabel
)
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from core.router import get_filters
from core.search import search_files, fast_search


# 🔹 Worker Thread
class SearchWorker(QThread):
    finished = pyqtSignal(list)

    def __init__(self, filters):
        super().__init__()
        self.filters = filters

    def run(self):
        if self.filters["name"]:
            results = fast_search(self.filters)
        else:
            results = search_files(self.filters)

        self.finished.emit(results)


# 🔹 Main App
class SeekrApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Seekr")
        self.setGeometry(200, 200, 850, 600)

        self.setStyleSheet("""
            QWidget {
                background-color: #121212;
                color: #E0E0E0;
                font-family: Arial;
            }
            QLineEdit {
                background-color: #1E1E1E;
                border: 1px solid #333;
                padding: 12px;
                border-radius: 10px;
                font-size: 16px;
            }
            QListWidget {
                background-color: #1E1E1E;
                border: none;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #2a2a2a;
            }
            QListWidget::item:hover {
                background-color: #2a2a2a;
            }
        """)

        layout = QVBoxLayout()

        # 🔹 Title
        title = QLabel("Seekr")
        title.setFont(QFont("Arial", 22, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # 🔹 Input
        self.input = QLineEdit()
        self.input.setPlaceholderText("Ask like: 'python files today'...")
        self.input.returnPressed.connect(self.handle_search)

        # 🔹 Results
        self.results = QListWidget()
        self.results.itemDoubleClicked.connect(self.open_in_explorer)

        layout.addWidget(title)
        layout.addWidget(self.input)
        layout.addWidget(self.results)

        self.setLayout(layout)

    # 🔹 Search handler
    def handle_search(self):
        query = self.input.text()
        if not query:
            return

        self.results.clear()
        self.results.addItem("🔍 Searching...")

        filters = get_filters(query)

        self.worker = SearchWorker(filters)
        self.worker.finished.connect(self.display_results)
        self.worker.start()

        self.input.clear()

    # 🔹 Display results nicely
    def display_results(self, results):
        self.results.clear()

        if not results:
            self.results.addItem("❌ No files found")
            return

        for path in results[:50]:
            filename = os.path.basename(path)
            directory = os.path.dirname(path)

            item = QListWidgetItem()
            item.setIcon(self.get_icon(path))

            # 🔥 Clean display (filename + path)
            item.setText(f"{filename}\n{directory}")

            # store full path
            item.setData(Qt.ItemDataRole.UserRole, path)

            self.results.addItem(item)

    # 🔹 Open folder in file explorer
    def open_in_explorer(self, item):
        path = item.data(Qt.ItemDataRole.UserRole)
        folder = os.path.dirname(path)

        subprocess.run(["xdg-open", folder])

    # 🔹 Icons
    def get_icon(self, path):
        if os.path.isdir(path):
            return QIcon.fromTheme("folder")

        ext = path.split(".")[-1].lower()

        if ext == "py":
            return QIcon.fromTheme("text-x-python")
        elif ext == "pdf":
            return QIcon.fromTheme("application-pdf")
        elif ext in ["jpg", "png"]:
            return QIcon.fromTheme("image-x-generic")
        elif ext in ["mp4", "mkv"]:
            return QIcon.fromTheme("video-x-generic")
        elif ext in ["mp3", "wav"]:
            return QIcon.fromTheme("audio-x-generic")
        else:
            return QIcon.fromTheme("text-x-generic")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SeekrApp()
    window.show()
    sys.exit(app.exec())