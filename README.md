# Downloads File Organizer

A small **Python** app that sorts **loose files** in your **Downloads** folder into category subfolders (Images, Documents, Archives, and so on). It includes a **desktop window** so you can see your Downloads, rename those category folders, and run the organizer in one place.

---

## What you need

- **Python 3.10+** (3.13 works fine)
- **PyQt6** (for the window)

---

## Install and run

1. Open a terminal in the project folder (where this `README.md` lives).

2. Create a virtual environment (recommended):

   ```bash
   python -m venv .venv
   ```

3. Activate it:

   - **Windows (PowerShell):** `.\.venv\Scripts\Activate.ps1`
   - **macOS / Linux:** `source .venv/bin/activate`

4. Install PyQt6:

   ```bash
   python -m pip install PyQt6
   ```

5. Start the app:

   ```bash
   python python/main.py
   ```

   On Windows, if you use the venv without activating it:

   ```text
   .\.venv\Scripts\python.exe .\python\main.py
   ```

### Command line only (no window)

To organize Downloads once from the terminal, without opening the GUI:

```bash
python python/main.py --cli
```

---

## Using the window

1. **Downloads path**  
   The app finds your real Downloads folder (Windows registry / macOS `~/Downloads` / Linux `xdg-user-dir` when available). The path is shown at the top.

2. **Live tree**  
   The big tree is your **actual** Downloads folder. Expand rows to see files and subfolders.

3. **Default folders**  
   When you start the app, it **creates empty category folders** under Downloads if they are missing (for example `Images`, `Archives`, `Others`), so you always have a clear place for sorted files.

4. **Rename a category folder**  
   In the tree, select a **direct subfolder of Downloads** that matches a category (for example `Archives`). Rename it with **F2** or **double-click** the name.  
   If that name is one of your organizer categories, the app **updates your saved settings** to match. Other folders are not tied to the organizer.

5. **Restore default folder names**  
   Button **“Restore default folder names”** resets names and order to the built-in defaults and renames folders on disk to match (after you confirm).

6. **Organize Downloads**  
   Button **“Organize Downloads”** moves **only loose files** in the Downloads root into the right category folders. Files already inside subfolders are left as they are.

---

## How files are sorted

- Each category has a list of **file extensions** (for example `.pdf` goes to Documents).
- The order of categories in your saved config matters: the **first** category that matches an extension wins.
- Anything that does not match goes to the **Others** category (the one with no extensions listed).

To change which extensions go where, edit the settings file (see below) or change the defaults in `python/main.py` if you are comfortable editing code.

---

## Where settings are saved

Settings are stored as JSON:

- **Windows:** `%APPDATA%\Downloads_File_Organizer\config.json`
- **macOS / Linux:** `~/.config/downloads_file_organizer/config.json`

The file lists categories with stable `id` values and display `name` values, plus `extensions` per category. Keeping `id` stable is what lets the app match a folder on disk to a category when you rename things.

---

## Project layout

```text
Downloads_File_Organizer/
├── python/
│   └── main.py      # entry point (GUI + --cli)
├── README.md
└── ...
```

---

## Safety notes

- The organizer **moves** files; it does not copy them. Run it on a folder you are okay changing.
- Use **Restore default folder names** only if you intend to reset names and order; it renames folders on disk after confirmation.

If something goes wrong, you can always fix or delete `config.json` and restart the app to get a fresh default configuration (after backing up the file if you care about your custom names).
