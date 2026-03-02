import os
import shutil

def organize_downloads():
# Get the Downloads folder path
    downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")

    # Define how to group file types into folders
    file_types = {
        "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp"],
        "Documents": [".pdf", ".docs", ".docx", ".txt", ".csv"],
        "Archives": [".zip", ".rar", ".tar", ".gz"],
        "Videos": [".mp4", ".mkv", ".avi", ".mov"],
        "Audio": [".mp3", ".wav", ".flac", ".aac"],
        "Spreadsheets": [ ".xls", ".xlsx", ".ods", ".csv"],
        "Presentations": [".ppt", ".pptx", ".key"],
        "Code": [".py", ".cpp", ".java", ".js", ".html", ".css"],
        "Executables": [".exe", ".msi", ".bat", ".sh"],
        "Others": []
    }
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
                os.makedirs(target_folder, exist_ok=True) # Create folder if it doesn't exist
                shutil.move(file_path, os.path.join(target_folder, filename))
                moved = True
                break

        # If no category matched, move to "Others"
        if not moved:
            target_folder = os.path.join(downloads_path, "Others")
            os.makedirs(target_folder, exist_ok=True)
            shutil.move(file_path, os.path.join(target_folder, filename))

def main():
    organize_downloads()

if __name__ == "__main__":
    main()


