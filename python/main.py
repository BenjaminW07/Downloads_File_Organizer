import os
import shutil

def organize_downloads(downloads_path: str | None = None) -> dict[str, int]:
    """
    Organize files in the Downloads folder into subfolders by extension.

    Returns a dict mapping destination folder name -> number of files moved.
    """
    if downloads_path is None:
        downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")

    # Define how to group file types into folders
    file_types = {
        "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp"],
        "Documents": [".pdf", ".doc", ".docx", ".txt"],
        "Archives": [".zip", ".rar", ".tar", ".gz"],
        "Videos": [".mp4", ".mkv", ".avi", ".mov"],
        "Audio": [".mp3", ".wav", ".flac", ".aac"],
        "Spreadsheets": [".xls", ".xlsx", ".ods", ".csv"],
        "Presentations": [".ppt", ".pptx", ".key"],
        "Code": [".py", ".cpp", ".java", ".js", ".html", ".css"],
        "Executables": [".exe", ".msi", ".bat", ".sh"],
        "Others": []
    }

    if not os.path.isdir(downloads_path):
        raise FileNotFoundError(f"Downloads folder not found: {downloads_path}")

    moved_counts: dict[str, int] = {}

    # Loop through files in Downloads
    for filename in os.listdir(downloads_path):
        file_path = os.path.join(downloads_path, filename)

        # skip folders, we only want to move files
        if not os.path.isfile(file_path):
            continue

        # Extract file extension
        _, ext = os.path.splitext(filename)
        ext = ext.lower()

        # Find the right category folder
        moved = False
        for folder_name, extensions in file_types.items():
            if ext in extensions:
                target_folder = os.path.join(downloads_path, folder_name)
                os.makedirs(target_folder, exist_ok=True)  # Create folder if it doesn't exist
                shutil.move(file_path, os.path.join(target_folder, filename))
                moved_counts[folder_name] = moved_counts.get(folder_name, 0) + 1
                moved = True
                break

        # If no category matched, move to "Others"
        if not moved:
            target_folder = os.path.join(downloads_path, "Others")
            os.makedirs(target_folder, exist_ok=True)
            shutil.move(file_path, os.path.join(target_folder, filename))
            moved_counts["Others"] = moved_counts.get("Others", 0) + 1

    return moved_counts


def run_gui() -> None:
    try:
        from PyQt6.QtCore import QObject, QThread, pyqtSignal
        from PyQt6.QtWidgets import (
            QApplication,
            QLabel,
            QMainWindow,
            QMessageBox,
            QPushButton,
            QVBoxLayout,
            QWidget,
        )
    except ModuleNotFoundError as e:
        raise ModuleNotFoundError(
            "PyQt6 is not installed in the Python interpreter you're running.\n\n"
            "If you created a virtual environment, run with:\n"
            r'  .\.venv\Scripts\python.exe .\python\main.py' "\n\n"
            "Or install into the current interpreter:\n"
            "  python -m pip install PyQt6"
        ) from e

    class Worker(QObject):
        finished = pyqtSignal(dict)
        failed = pyqtSignal(str)

        def run(self) -> None:
            try:
                stats = organize_downloads()
            except Exception as e:  # keep GUI friendly
                self.failed.emit(str(e))
                return
            self.finished.emit(stats)

    class MainWindow(QMainWindow):
        def __init__(self) -> None:
            super().__init__()
            self.setWindowTitle("Downloads File Organizer")

            self.button = QPushButton("Organize Downloads")
            self.status = QLabel("Ready.")
            self.status.setWordWrap(True)

            layout = QVBoxLayout()
            layout.addWidget(self.button)
            layout.addWidget(self.status)

            container = QWidget()
            container.setLayout(layout)
            self.setCentralWidget(container)

            self.button.clicked.connect(self.on_click)
            self._thread: QThread | None = None
            self._worker: Worker | None = None

        def on_click(self) -> None:
            self.button.setEnabled(False)
            self.status.setText("Organizing...")

            self._thread = QThread()
            self._worker = Worker()
            self._worker.moveToThread(self._thread)

            self._thread.started.connect(self._worker.run)
            self._worker.finished.connect(self.on_finished)
            self._worker.failed.connect(self.on_failed)

            self._worker.finished.connect(self._thread.quit)
            self._worker.failed.connect(self._thread.quit)
            self._worker.finished.connect(self._worker.deleteLater)
            self._worker.failed.connect(self._worker.deleteLater)
            self._thread.finished.connect(self._thread.deleteLater)

            self._thread.start()

        def on_finished(self, stats: dict) -> None:
            total = sum(int(v) for v in stats.values())
            if total == 0:
                self.status.setText("Done. No files to move.")
            else:
                parts = [f"{k}: {v}" for k, v in sorted(stats.items())]
                self.status.setText("Done. Moved " + str(total) + " file(s).\n" + ", ".join(parts))
            self.button.setEnabled(True)

        def on_failed(self, message: str) -> None:
            QMessageBox.critical(self, "Error", message)
            self.status.setText("Error. See message.")
            self.button.setEnabled(True)

    app = QApplication([])
    window = MainWindow()
    window.resize(360, 140)
    window.show()
    app.exec()

def main():
    import sys

    if "--cli" in sys.argv:
        stats = organize_downloads()
        total = sum(stats.values())
        print(f"Moved {total} file(s). Details: {stats}")
        return

    run_gui()

if __name__ == "__main__":
    main()


