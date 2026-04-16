import json
import os
import re
import shutil
import subprocess
import sys
import uuid
from typing import Any


def get_downloads_folder() -> str:
    """
    Resolve the user's Downloads directory in an OS-friendly way (localized paths,
    OneDrive on Windows, XDG on Linux, etc.). Creates the folder if missing.
    """
    if sys.platform == "win32":
        try:
            import winreg

            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders",
            ) as key:
                downloads, _ = winreg.QueryValueEx(key, "{374DE290-123F-4565-9164-39C4925E467B}")
            path = os.path.normpath(os.path.expandvars(downloads))
            os.makedirs(path, exist_ok=True)
            return path
        except OSError:
            pass

    if sys.platform == "darwin":
        path = os.path.normpath(os.path.join(os.path.expanduser("~"), "Downloads"))
        os.makedirs(path, exist_ok=True)
        return path

    xdg = os.environ.get("XDG_DOWNLOAD_DIR", "").strip()
    if xdg:
        path = os.path.normpath(os.path.expanduser(xdg))
        os.makedirs(path, exist_ok=True)
        return path

    try:
        result = subprocess.run(
            ["xdg-user-dir", "DOWNLOAD"],
            capture_output=True,
            text=True,
            timeout=3,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            path = os.path.normpath(result.stdout.strip())
            os.makedirs(path, exist_ok=True)
            return path
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    path = os.path.normpath(os.path.join(os.path.expanduser("~"), "Downloads"))
    os.makedirs(path, exist_ok=True)
    return path


def ensure_category_folders(downloads_path: str, categories: list[dict[str, Any]]) -> None:
    """Create empty subfolders for each category under Downloads (preview / organize targets)."""
    for c in categories:
        os.makedirs(os.path.join(downloads_path, c["name"]), exist_ok=True)

# Ordered categories: first matching extension wins. Exactly one category must have extensions: [] (catch-all "Others").
# Stable `id` ties a row to a real folder so renaming in the GUI can rename the folder on disk.
DEFAULT_CATEGORIES: list[dict[str, Any]] = [
    {"id": "images", "name": "Images", "extensions": [".jpg", ".jpeg", ".png", ".gif", ".bmp"]},
    {"id": "documents", "name": "Documents", "extensions": [".pdf", ".doc", ".docx", ".txt"]},
    {"id": "archives", "name": "Archives", "extensions": [".zip", ".rar", ".tar", ".gz"]},
    {"id": "videos", "name": "Videos", "extensions": [".mp4", ".mkv", ".avi", ".mov"]},
    {"id": "audio", "name": "Audio", "extensions": [".mp3", ".wav", ".flac", ".aac"]},
    {"id": "spreadsheets", "name": "Spreadsheets", "extensions": [".xls", ".xlsx", ".ods", ".csv"]},
    {"id": "presentations", "name": "Presentations", "extensions": [".ppt", ".pptx", ".key"]},
    {"id": "code", "name": "Code", "extensions": [".py", ".cpp", ".java", ".js", ".html", ".css"]},
    {"id": "executables", "name": "Executables", "extensions": [".exe", ".msi", ".bat", ".sh"]},
    {"id": "others", "name": "Others", "extensions": []},
]

_EXT_TUPLE_TO_DEFAULT_ID: dict[tuple[str, ...], str] = {}
for _dc in DEFAULT_CATEGORIES:
    _EXT_TUPLE_TO_DEFAULT_ID[tuple(sorted(_dc["extensions"]))] = _dc["id"]


def get_config_path() -> str:
    if os.name == "nt":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
        folder = os.path.join(base, "Downloads_File_Organizer")
    else:
        folder = os.path.join(os.path.expanduser("~"), ".config", "downloads_file_organizer")
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, "config.json")


def _normalize_categories(raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for c in raw:
        cid = str(c.get("id", "")).strip()
        name = str(c.get("name", "")).strip()
        exts = c.get("extensions", [])
        if not isinstance(exts, list):
            exts = []
        norm_exts = []
        for e in exts:
            s = str(e).strip().lower()
            if not s.startswith("."):
                s = "." + s
            norm_exts.append(s)
        out.append({"id": cid, "name": name, "extensions": norm_exts})
    return out


def assign_category_ids(categories: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Fill missing `id` fields (legacy configs) and ensure ids are unique."""
    used: set[str] = set()
    out: list[dict[str, Any]] = []
    for c in categories:
        cid = str(c.get("id", "")).strip()
        if cid and cid not in used:
            used.add(cid)
            out.append({**c, "id": cid})
            continue
        t = tuple(sorted(c["extensions"]))
        nid = _EXT_TUPLE_TO_DEFAULT_ID.get(t)
        if nid and nid not in used:
            used.add(nid)
            out.append({**c, "id": nid})
            continue
        base = re.sub(r"[^a-z0-9]+", "_", c["name"].lower()).strip("_") or "category"
        nid = base
        j = 0
        while nid in used:
            j += 1
            nid = f"{base}_{j}"
        used.add(nid)
        out.append({**c, "id": nid})
    return out


def validate_categories(categories: list[dict[str, Any]]) -> None:
    bad_char = re.compile(r'[\\/:*?"<>|]')
    names = [c["name"].strip() for c in categories]
    ids = [str(c.get("id", "")).strip() for c in categories]
    if any(not n for n in names):
        raise ValueError("Every folder name must be non-empty.")
    if any(not i for i in ids):
        raise ValueError("Every category must have a non-empty id.")
    if len(set(names)) != len(names):
        raise ValueError("Folder names must be unique.")
    if len(set(ids)) != len(ids):
        raise ValueError("Internal category ids must be unique.")
    for n in names:
        if bad_char.search(n):
            raise ValueError(f'Invalid folder name: "{n}" (cannot contain \\ / : * ? " < > |)')
    catch = [c for c in categories if not c["extensions"]]
    if len(catch) != 1:
        raise ValueError("There must be exactly one catch-all category with no extensions (Others).")


def _merge_dir_contents(src_dir: str, dst_dir: str) -> None:
    os.makedirs(dst_dir, exist_ok=True)
    for name in os.listdir(src_dir):
        s = os.path.join(src_dir, name)
        d = os.path.join(dst_dir, name)
        if os.path.isdir(s) and os.path.isdir(d):
            _merge_dir_contents(s, d)
            continue
        if os.path.exists(d):
            stem, ext = os.path.splitext(name)
            d = os.path.join(dst_dir, f"{stem}_{uuid.uuid4().hex[:6]}{ext}")
        shutil.move(s, d)
    try:
        shutil.rmtree(src_dir)
    except OSError:
        try:
            os.rmdir(src_dir)
        except OSError:
            pass


def apply_download_folder_renames(
    downloads_path: str,
    before: list[dict[str, Any]],
    after: list[dict[str, Any]],
) -> None:
    """
    When a category's display name changes but `id` stays the same, rename the matching
    subfolder under `downloads_path` from the old name to the new name.
    Handles swaps/chains by using temporary folder names.
    """
    before_by_id = {c["id"]: c["name"] for c in before}
    after_by_id = {c["id"]: c["name"] for c in after}
    pairs: list[tuple[str, str]] = []
    for cid, new_name in after_by_id.items():
        if cid not in before_by_id:
            continue
        old_name = before_by_id[cid]
        if old_name != new_name:
            pairs.append((old_name, new_name))
    if not pairs:
        return

    olds = {o for o, _ in pairs}
    # If a target name is also a source folder in this batch, we must use a two-phase rename.
    use_temp = any(n in olds for _, n in pairs)

    if use_temp:
        tag = uuid.uuid4().hex[:8]
        tmps: list[tuple[str, str]] = []
        for i, (old, new) in enumerate(pairs):
            old_p = os.path.join(downloads_path, old)
            if not os.path.isdir(old_p):
                continue
            tmp = os.path.join(downloads_path, f".__rename_tmp_{tag}_{i}")
            os.rename(old_p, tmp)
            tmps.append((tmp, new))
        for tmp, new in tmps:
            new_p = os.path.join(downloads_path, new)
            if os.path.isdir(new_p):
                _merge_dir_contents(tmp, new_p)
                shutil.rmtree(tmp, ignore_errors=True)
            else:
                os.rename(tmp, new_p)
        return

    for old, new in pairs:
        old_p = os.path.join(downloads_path, old)
        if not os.path.isdir(old_p):
            continue
        new_p = os.path.join(downloads_path, new)
        if os.path.isdir(new_p):
            _merge_dir_contents(old_p, new_p)
        else:
            os.rename(old_p, new_p)


def load_categories() -> list[dict[str, Any]]:
    path = get_config_path()
    if not os.path.isfile(path):
        return [dict(c) for c in DEFAULT_CATEGORIES]
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return [dict(c) for c in DEFAULT_CATEGORIES]
    raw = data.get("categories")
    if not isinstance(raw, list) or not raw:
        return [dict(c) for c in DEFAULT_CATEGORIES]
    categories = assign_category_ids(_normalize_categories(raw))
    try:
        validate_categories(categories)
    except ValueError:
        return [dict(c) for c in DEFAULT_CATEGORIES]
    return categories


def save_categories(
    categories: list[dict[str, Any]],
    downloads_path: str | None = None,
    *,
    skip_disk_renames: bool = False,
) -> None:
    path = get_config_path()
    new_cats = assign_category_ids(_normalize_categories([dict(c) for c in categories]))
    validate_categories(new_cats)

    if downloads_path is None:
        downloads_path = get_downloads_folder()

    if not skip_disk_renames:
        old_cats: list[dict[str, Any]] | None = None
        if os.path.isfile(path):
            try:
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                raw = data.get("categories")
                if isinstance(raw, list) and raw:
                    old_cats = assign_category_ids(_normalize_categories(raw))
            except (OSError, json.JSONDecodeError):
                pass

        # First run (no config file): assume on-disk folders use default names until first save.
        if old_cats is None:
            old_cats = assign_category_ids(
                _normalize_categories([dict(c) for c in DEFAULT_CATEGORIES])
            )

        apply_download_folder_renames(downloads_path, old_cats, new_cats)

    with open(path, "w", encoding="utf-8") as f:
        json.dump({"categories": new_cats}, f, indent=2)


def organize_downloads(
    downloads_path: str | None = None,
    categories: list[dict[str, Any]] | None = None,
) -> dict[str, int]:
    """
    Organize files in the Downloads folder into subfolders by extension.

    Returns a dict mapping destination folder name -> number of files moved.
    """
    if downloads_path is None:
        downloads_path = get_downloads_folder()

    if categories is None:
        categories = load_categories()
    else:
        categories = assign_category_ids(_normalize_categories([dict(c) for c in categories]))
    validate_categories(categories)

    others = next(c for c in categories if not c["extensions"])
    others_name = others["name"]
    ordered_match = [c for c in categories if c["extensions"]]

    if not os.path.isdir(downloads_path):
        raise FileNotFoundError(f"Downloads folder not found: {downloads_path}")

    moved_counts: dict[str, int] = {}

    for filename in os.listdir(downloads_path):
        file_path = os.path.join(downloads_path, filename)

        if not os.path.isfile(file_path):
            continue

        _, ext = os.path.splitext(filename)
        ext = ext.lower()

        moved = False
        for cat in ordered_match:
            if ext in cat["extensions"]:
                folder_name = cat["name"]
                target_folder = os.path.join(downloads_path, folder_name)
                os.makedirs(target_folder, exist_ok=True)
                shutil.move(file_path, os.path.join(target_folder, filename))
                moved_counts[folder_name] = moved_counts.get(folder_name, 0) + 1
                moved = True
                break

        if not moved:
            target_folder = os.path.join(downloads_path, others_name)
            os.makedirs(target_folder, exist_ok=True)
            shutil.move(file_path, os.path.join(target_folder, filename))
            moved_counts[others_name] = moved_counts.get(others_name, 0) + 1

    return moved_counts


def run_gui() -> None:
    try:
        from PyQt6.QtCore import QDir, QObject, Qt, QThread, pyqtSignal
        from PyQt6.QtGui import QCloseEvent, QFileSystemModel
        from PyQt6.QtWidgets import (
            QAbstractItemView,
            QApplication,
            QHBoxLayout,
            QLabel,
            QMainWindow,
            QMessageBox,
            QPushButton,
            QTreeView,
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

        def __init__(self, categories: list[dict[str, Any]], downloads_path: str) -> None:
            super().__init__()
            self._categories = categories
            self._downloads_path = downloads_path

        def run(self) -> None:
            try:
                stats = organize_downloads(
                    downloads_path=self._downloads_path,
                    categories=self._categories,
                )
            except Exception as e:
                self.failed.emit(str(e))
                return
            self.finished.emit(stats)

    class MainWindow(QMainWindow):
        def __init__(self) -> None:
            super().__init__()
            self.setWindowTitle("Downloads File Organizer")
            self._downloads_path = get_downloads_folder()

            self._path_label = QLabel()
            self._path_label.setWordWrap(True)
            self._path_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

            self._fs_model = QFileSystemModel()
            self._fs_model.setReadOnly(False)
            self._fs_model.setFilter(QDir.Filter.AllEntries | QDir.Filter.NoDotAndDotDot)
            self._fs_model.fileRenamed.connect(self._on_file_renamed)

            self._tree = QTreeView()
            self._tree.setModel(self._fs_model)
            self._tree.setAnimated(True)
            self._tree.setSortingEnabled(True)
            self._tree.setEditTriggers(
                QAbstractItemView.EditTrigger.EditKeyPressed
                | QAbstractItemView.EditTrigger.DoubleClicked
            )
            for col in (1, 2, 3):
                self._tree.setColumnHidden(col, True)
            self._tree.setColumnWidth(0, 360)

            intro = QLabel(
                "Live view of your Downloads folder. "
                "Rename a category subfolder here (F2, or click once then again slowly) — "
                "only folders that match your organizer list update saved names. "
                "Expand rows to see all files and folders."
            )
            intro.setWordWrap(True)

            self._btn_defaults = QPushButton("Restore default folder names")
            self._btn_defaults.clicked.connect(self._on_restore_defaults)

            self._btn_organize = QPushButton("Organize Downloads")
            self._btn_organize.clicked.connect(self.on_click)

            row = QHBoxLayout()
            row.addWidget(self._btn_defaults)
            row.addWidget(self._btn_organize)

            self._status = QLabel("Ready.")
            self._status.setWordWrap(True)

            layout = QVBoxLayout()
            layout.addWidget(QLabel("Downloads location:"))
            layout.addWidget(self._path_label)
            layout.addWidget(intro)
            layout.addWidget(self._tree, stretch=1)
            layout.addLayout(row)
            layout.addWidget(self._status)

            central = QWidget()
            central.setLayout(layout)
            self.setCentralWidget(central)

            _cats = load_categories()
            ensure_category_folders(self._downloads_path, _cats)
            self._refresh_tree()

            self._thread: QThread | None = None
            self._worker: Worker | None = None

        def _same_dir(self, a: str, b: str) -> bool:
            return os.path.normcase(os.path.normpath(a)) == os.path.normcase(os.path.normpath(b))

        def _refresh_tree(self) -> None:
            self._downloads_path = get_downloads_folder()
            self._path_label.setText(self._downloads_path)
            if os.path.isdir(self._downloads_path):
                self._fs_model.setRootPath("")
                idx = self._fs_model.setRootPath(self._downloads_path)
                self._tree.setRootIndex(idx)
                self._tree.expandToDepth(1)

        def _on_file_renamed(self, path: str, old_name: str, new_name: str) -> None:
            if not self._same_dir(path, self._downloads_path):
                return
            cats = load_categories()
            updated: list[dict[str, Any]] | None = None
            for c in cats:
                if c["name"] == old_name:
                    updated = [dict(x) for x in cats]
                    for u in updated:
                        if u["id"] == c["id"]:
                            u["name"] = new_name.strip()
                    break
            if updated is None:
                return
            try:
                validate_categories(updated)
            except ValueError as e:
                try:
                    os.rename(
                        os.path.join(self._downloads_path, new_name),
                        os.path.join(self._downloads_path, old_name),
                    )
                except OSError:
                    pass
                QMessageBox.warning(self, "Invalid folder name", str(e))
                self._refresh_tree()
                return
            try:
                save_categories(updated, downloads_path=self._downloads_path, skip_disk_renames=True)
            except OSError as ex:
                try:
                    os.rename(
                        os.path.join(self._downloads_path, new_name),
                        os.path.join(self._downloads_path, old_name),
                    )
                except OSError:
                    pass
                QMessageBox.warning(self, "Could not save", str(ex))
                self._refresh_tree()
                return
            self._status.setText(f"Updated organizer folder: {old_name!r} → {new_name!r}")

        def _on_restore_defaults(self) -> None:
            ans = QMessageBox.question(
                self,
                "Restore defaults",
                "Reset all category folder names and order to the built-in defaults? "
                "Folders on disk will be renamed to match.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if ans != QMessageBox.StandardButton.Yes:
                return
            defaults = assign_category_ids(
                _normalize_categories([dict(c) for c in DEFAULT_CATEGORIES])
            )
            try:
                save_categories(defaults, downloads_path=self._downloads_path)
            except (OSError, ValueError) as e:
                QMessageBox.warning(self, "Could not restore defaults", str(e))
                return
            self._downloads_path = get_downloads_folder()
            ensure_category_folders(self._downloads_path, defaults)
            self._status.setText("Restored default folder names and order.")
            self._refresh_tree()

        def on_click(self) -> None:
            cats = load_categories()
            self._btn_organize.setEnabled(False)
            self._btn_defaults.setEnabled(False)
            self._status.setText("Organizing...")

            self._thread = QThread()
            self._worker = Worker(cats, self._downloads_path)
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
                self._status.setText("Done. No files to move.")
            else:
                parts = [f"{k}: {v}" for k, v in sorted(stats.items())]
                self._status.setText("Done. Moved " + str(total) + " file(s).\n" + ", ".join(parts))
            self._refresh_tree()
            self._btn_organize.setEnabled(True)
            self._btn_defaults.setEnabled(True)

        def on_failed(self, message: str) -> None:
            QMessageBox.critical(self, "Error", message)
            self._status.setText("Error. See message.")
            self._btn_organize.setEnabled(True)
            self._btn_defaults.setEnabled(True)

        def closeEvent(self, event: QCloseEvent) -> None:
            super().closeEvent(event)

    app = QApplication([])
    window = MainWindow()
    window.resize(780, 640)
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
