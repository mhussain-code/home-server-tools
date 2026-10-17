import sys
import os
import re
import requests
from tabulate import tabulate

# TVMaze API URL for Fairy Tail (2009)
# Usage: python tv_rename_absolute.py <tvmaze show id> "<show name>" <folder>
TVMAZE_API_URL = f"https://api.tvmaze.com/shows/{sys.argv[1]}/episodes"
SHOW_NAME = sys.argv[2]
VALID_EXTENSIONS = (".mkv", ".mp4", ".srt", ".m4v")

def fetch_episode_data():
    """
    Fetch all episodes from TVMaze. Ensure the full list is obtained.
    """
    try:
        response = requests.get(TVMAZE_API_URL)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Failed to fetch episodes: {e}")
        return []

def extract_absolute_number(filename):
    """
    Extract absolute episode number from filenames like:
      '[Anime Time] Fairy Tail - 173 - Some Title.ext'
    """
    pattern = re.compile(r'Fairy\s*Tail\s*-\s*(\d+)', re.IGNORECASE)
    match = pattern.search(filename)
    if match:
        return int(match.group(1))
    return None

def find_episode_by_absolute_number(abs_number, episodes):
    """
    Match the absolute number to an episode in the metadata.
    """
    if abs_number > len(episodes):
        return None  # No match if abs_number exceeds available episodes
    # TVMaze episodes are already ordered by airdate
    return episodes[abs_number - 1] if abs_number > 0 else None

def is_valid_file(filename):
    """
    Check if the file is a valid media file and not a hidden or metadata file.
    """
    return filename.lower().endswith(VALID_EXTENSIONS) and not filename.startswith("._")

def suggest_renames(directory, episodes):
    """
    Walk the directory and suggest renames based on the episode data.
    """
    rename_suggestions = []
    for root, dirs, files in os.walk(directory):
        for filename in files:
            if not is_valid_file(filename):
                continue

            abs_number = extract_absolute_number(filename)
            if abs_number is None:
                continue  # Skip files without an absolute number

            matched_episode = find_episode_by_absolute_number(abs_number, episodes)
            if matched_episode:
                season = matched_episode["season"]
                episode_number = matched_episode["number"]
                title = matched_episode["name"]
                ext = os.path.splitext(filename)[1]
                new_filename = f"{SHOW_NAME} - S{season:02d}E{episode_number:02d} - {title}{ext}"
                
                old_path = os.path.join(root, filename)
                new_path = os.path.join(root, new_filename)
                
                if old_path != new_path:
                    rename_suggestions.append((old_path, new_path))

    return rename_suggestions

def display_preview(rename_suggestions):
    """
    Display the rename suggestions in a table and ask for confirmation.
    """
    if not rename_suggestions:
        print("No files to rename.")
        return False

    table = []
    for old_path, new_path in rename_suggestions:
        table.append([os.path.basename(old_path), os.path.basename(new_path)])
    
    print(tabulate(table, headers=["Old Name", "New Name"], tablefmt="grid"))
    choice = input("\nProceed with renaming? (y/n): ").strip().lower()
    return choice == 'y'

def perform_renames(rename_suggestions):
    """
    Perform the renaming after user confirmation.
    """
    for old_path, new_path in rename_suggestions:
        try:
            print(f"Renaming:\n  {old_path}\n=> {new_path}")
            os.rename(old_path, new_path)
        except Exception as e:
            print(f"Failed to rename {old_path}: {e}")

def main():
    directory = sys.argv[3]
    
    print("Fetching episode data from TVMaze...")
    episodes = fetch_episode_data()
    if not episodes:
        print("No episodes found. Check your network or TVMaze API.")
        return

    print("Scanning directory for valid files...")
    rename_suggestions = suggest_renames(directory, episodes)
    if display_preview(rename_suggestions):
        print("Renaming files...")
        perform_renames(rename_suggestions)
    else:
        print("No files were renamed.")

if __name__ == "__main__":
    main()
