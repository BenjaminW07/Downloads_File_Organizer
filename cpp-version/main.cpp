#include <iostream>
#include <filesystem>
#include <string>
#include <map>
#include <vector>
#include <algorithm>
#include <cctype>

namespace fs = std::filesystem;

void organize_downloads() {
    // Path to the user's Downloads folder (Windows).
    std::string home = std::getenv("USERPROFILE"); // On Linux/Mac use HOME
    std::string downloads_path = home + "\\Downloads";

    // File categories mapped to their extensions.
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
            // Skip directories; only process files.
            if (!fs::is_regular_file(entry)) 
                continue; 

            // Extract filename and extension.
            std::string filename = entry.path().filename().string();
            std::string ext = entry.path().extension().string();
            // Normalize extension to lowercase.
            for (auto& c : ext) 
                c = std::tolower(c); 

            bool moved = false;

            // Attempt to match the file extension to a category.
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


