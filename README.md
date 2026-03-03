## <u>Downloads File Organizer</u>
Automatically organizes files in the Windows **Downloads** folder by sorting them into category‑based subfolders. Implemented in both **Python** and **C++** to compare language design, structure, and performance while producing identical behavior.

## <u>Overview</u>
The Downloads folder often becomes cluttered with documents, images, installers, code files, and random items. This project scans the folder, identifies each file’s extension, and moves it into a matching category such as Images, Documents, Archives, Code, or Others.

Two complete implementations are included:
- Python version — concise, readable, and quick to develop
- C++ version — lower‑level control using std::filesystem

Both versions follow the same logic and produce the same output.

#### **Note:** This project is designed for Windows systems, as it relies on the USERPROFILE environment variable and Windows-style file paths.

## <u>Folder Structure</u>
```
Downloads_File_Organizer/
│
├── python-version/
│   └── main.py
│
├── cpp-version/
│   └── main.cpp
│
├── .gitignore
├── LICENSE
└── README.md
```
## <u>How It Works</u>
The program:
- Locates the user’s Downloads folder
- Defines a mapping of file categories to extensions
- Iterates through every file in the folder
- Matches each file’s extension to a category
- Creates category folders if they don’t exist
- Moves the file into the correct folder
- Places unmatched files into Others

Categories include:
- Images — .jpg, .png, .gif, .bmp
- Documents — .pdf, .docx, .txt, .csv
- Archives — .zip, .rar, .tar, .gz
- Videos — .mp4, .mkv, .avi
- Audio — .mp3, .wav, .flac
- Code — .py, .cpp, .js, .html
- Executables — .exe, .msi, .bat
- Others — everything else

## <u>Running the Python Version</u>
**Requirements:** Python 3.x installed
```
cd python-version
python main.py
```
The script will automatically organize your Downloads folder.

## <u>Running the C++ version</u>
**Requirements:** A C++ compiler (g++, clang++, or MSVC)
### **Compile:**
```
cd cpp-version
g++ main.cpp -o organizer
```
### **Run:**
```
organizer.exe
```
## <u>Why Two Implementations?</u>
Building the same project in two languages demonstrates:
- Understanding of file systems across languages
- Ability to translate logic between Python and C++
- Awareness of performance and design tradeoffs
- Comfort with both high‑level and low‑level programming styles

This mirrors real‑world engineering where teams often maintain tools in multiple languages.

## <u>What I Learned</u>
- How to structure a small project cleanly across two languages
- How to use Python’s and C++’s filesystem libraries
- How to organize a GitHub repository professionally
- How to write a clear README and use .gitignore effectively
- Differences between Python’s high‑level scripting and C++’s lower‑level control

## <u>Future Improvements</u>
- Add logging to track moved files
- Add a configuration file for custom categories
- Add command‑line options (e.g., dry‑run mode, custom paths)
- Add unit tests for extension matching
- Add a GUI version in Python or C++