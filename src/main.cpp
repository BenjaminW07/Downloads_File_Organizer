/*
Benjamin Walker 

Psuedocode - When this runs it reads the file name extension and sorts the files into folders
             in the main "Downloads" folder on Windows OS.
*/

#include <iostream>
#include <filesystem>
#include <string>
#include <map>
#include <vector>
#include <algorithm>
#include <cctype>

namespace fs = std::filesystem;

void organize_downloads() {
    // Get the Downloads folder path (works on Windows, adjust if needed)
    std::string home = std::getenv("USERPROFILE"); // On Linux/Mac use HOME
    std::string downloads_path = home + "\\Downloads";

    // Define file type categories
    std::map<std::string, std::vector<std::string>> file_types = {
        {"Images", {".jpg", ".jpeg", ".png", ".gif", ".bmp"}},
        {"Documents", {".pdf", ".docs", ".docx", ".txt", ".csv"}},
        {"Archives", {".zip", ".rar", ".tar", ".gz"}},
        {"Videos", {".mp4", ".mkv", ".avi", ".mov"}},
        {"Audio", {".mp3", ".wav", ".flac", ".aac"}},
        {"Spreadsheets", {".xls", ".xlsx", ".ods", ".csv"}},
        {"Presentations", {".ppt", ".pptx", ".key"}},
        {"Code", {".py", ".cpp", ".java", ".js", ".html", ".css"}},
        {"Executables", {".exe", ".msi", ".bat", ".sh"}},
        {"Others", {}}
    };

    try {
        // Iterates through downloads folder and references it to entry.
        for (const auto& entry : fs::directory_iterator(downloads_path)) {
            if (!fs::is_regular_file(entry)) 
                continue; // skip folders

            // Converts filesystem::path into a plain string, entry.path() returns std::filesystem::path
            // .filename() is a memeber function of filesystem::path that returns another path containing
            // only the last component ex. "photo.jpg"
            std::string filename = entry.path().filename().string();
            std::string ext = entry.path().extension().string(); // Just stores the extension ex. ".jpg"
            for (auto& c : ext) 
                c = std::tolower(c); // lowercase extension

            bool moved = false;
            for (const auto& [folder_name, extensions] : file_types) {
                if (!extensions.empty() && std::find(extensions.begin(), extensions.end(), ext) != extensions.end()) {
                    
                    fs::path target_folder = downloads_path + "\\" + folder_name;
                    fs::create_directories(target_folder);
                    fs::rename(entry.path(), target_folder / filename);
                    moved = true;
                    break;
                }
            }

            // If no category matched, move to "Others"
            if (!moved) {
                fs::path target_folder = downloads_path + "\\Others";
                fs::create_directories(target_folder);
                fs::rename(entry.path(), target_folder / filename);
            }
        }
    } catch (const fs::filesystem_error& e) {
        std::cerr << "Error: " << e.what() << std::endl;
    }
}

int main() {
    
    organize_downloads();

    std::cout << "Downloads folder organized successfully!\n";
    return 0;
}


