import sys
import os
import subprocess
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLineEdit,
    QListWidget, QListWidgetItem
)
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from app.core.router import get_filters
from app.core.search import search_files, fast_search


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


class SeekrApp(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Seekr")
        self.setGeometry(400, 200, 700, 500)

        # 🔥 minimal styling
        self.setStyleSheet("""
            QWidget {
                background-color: #0b0f14;
                color: #e5e7eb;
                font-family: Inter, Arial;
            }

            QLineEdit {
                background-color: #111827;
                border: none;
                padding: 16px;
                border-radius: 10px;
                font-size: 18px;
            }

            QListWidget {
                background-color: transparent;
                border: none;
            }

            QListWidget::item {
                padding: 10px;
            }

            QListWidget::item:selected {
                background-color: #1f2937;
                border-radius: 6px;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 20)
        layout.setSpacing(15)

        # 🔹 Input (center focus)
        self.input = QLineEdit()
        self.input.setPlaceholderText("Search files...")
        self.input.returnPressed.connect(self.handle_search)

        # 🔹 Results
        self.results = QListWidget()
        self.results.itemDoubleClicked.connect(self.open_folder)

        layout.addWidget(self.input)
        layout.addWidget(self.results)

        self.setLayout(layout)

    def handle_search(self):
        query = self.input.text()
        if not query:
            return

        self.results.clear()
        self.results.addItem("Searching...")

        filters = get_filters(query)

        self.worker = SearchWorker(filters)
        self.worker.finished.connect(self.display_results)
        self.worker.start()

    def display_results(self, results):
        self.results.clear()

        if not results:
            self.results.addItem("No results")
            return

        for path in results[:50]:
            filename = os.path.basename(path)
            directory = os.path.dirname(path)

            item = QListWidgetItem()
            item.setIcon(self.get_icon(path))

            # 🔥 clean text (no emojis, no noise)
            item.setText(f"{filename}    {directory}")

            item.setData(Qt.ItemDataRole.UserRole, path)

            self.results.addItem(item)

    def open_folder(self, item):
        path = item.data(Qt.ItemDataRole.UserRole)
        subprocess.run(["xdg-open", os.path.dirname(path)])

    def get_icon(self, path):
        if os.path.isdir(path):
            return QIcon.fromTheme("folder")
        return QIcon.fromTheme("text-x-generic")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SeekrApp()
    window.show()
    sys.exit(app.exec())