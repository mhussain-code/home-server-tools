import sys
import re
import requests
import os
from tabulate import tabulate

# TVMaze API details for the series
# Usage: python tv_rename.py <tvmaze show id> "<show name>" <folder>
TVMAZE_SHOW_ID = sys.argv[1]
TVMAZE_API_URL = f"https://api.tvmaze.com/shows/{TVMAZE_SHOW_ID}/episodes"
SHOW_NAME = sys.argv[2]

# File extensions that the script will process
VALID_EXTENSIONS = ['.mkv', '.mp4', '.srt', '.m4v']

def get_episodes_from_tvmaze():
    response = requests.get(TVMAZE_API_URL)
    if response.status_code == 200:
        return response.json()
    else:
        print("Failed to fetch data from TVMaze API")
        return []

def extract_season_episode(filename):
    patterns = [
        re.compile(r'[Ss](\d+)[Ee](\d+)'),
        re.compile(r'Series[_\s](\d+)[^\d]+(\d+)'),
        re.compile(r'Series[_\s](\d+)[^\d]+[Ee]p[^\d]+(\d+)')
    ]
    for pattern in patterns:
        match = pattern.search(filename)
        if match:
            return int(match.group(1)), int(match.group(2))
    return None, None

def extract_subtitle_suffix(filename):
    if not filename.lower().endswith('.srt'):
        return ''

    base = filename[:-4]  # strip .srt

    # Check for long-form language name like "Chinese (Simplified).chi" or "Spanish (Latin America).spa"
    long_lang = re.search(r'([A-Z][a-zA-Z\s]+\([^)]+\)\.[a-z]{2,3})$', base)
    if long_lang:
        return '.' + long_lang.group(1)

    # Check for SDH.eng style
    sdh = re.search(r'(SDH\.[a-z]{2,3})$', base, re.IGNORECASE)
    if sdh:
        return '.' + sdh.group(1)

    # Plain 3-letter language code at the very end
    plain = re.search(r'\.([a-z]{2,3})$', base, re.IGNORECASE)
    if plain:
        return '.' + plain.group(1)

    return ''

def is_valid_file(filename):
    return (
        filename.lower().endswith(tuple(VALID_EXTENSIONS))
        and not filename.startswith("._")
    )

def display_rename_table(rename_suggestions):
    table = []
    for old_path, new_path in rename_suggestions:
        table.append([os.path.basename(old_path), os.path.basename(new_path)])

    def sort_key(x):
        match = re.search(r'S(\d+)E(\d+)', x[1])
        if match:
            return int(match.group(1)), int(match.group(2))
        return float('inf'), float('inf')

    table.sort(key=sort_key)
    print(tabulate(table, headers=["Old Name", "New Name"], tablefmt="grid"))
    choice = input("\nDo you want to rename all files? (y/n): ").strip().lower()
    return choice == 'y'

def rename_files(directory, episodes):
    rename_suggestions = []

    for root, dirs, files in os.walk(directory):
        for filename in files:
            if not is_valid_file(filename):
                continue

            season, episode = extract_season_episode(filename)
            if season is None or episode is None:
                continue

            matched_episode = next(
                (ep for ep in episodes if ep['season'] == season and ep['number'] == episode),
                None
            )
            if not matched_episode:
                continue

            title = matched_episode['name']
            # Sanitise title for filesystem safety
            title = re.sub(r'[\\/*?:"<>|]', '', title)

            if filename.lower().endswith('.srt'):
                lang_suffix = extract_subtitle_suffix(filename)
                new_filename = f"{SHOW_NAME} - S{season:02d}E{episode:02d} - {title}{lang_suffix}.srt"
            else:
                ext = os.path.splitext(filename)[1]
                new_filename = f"{SHOW_NAME} - S{season:02d}E{episode:02d} - {title}{ext}"

            if filename == new_filename:
                continue

            old_path = os.path.join(root, filename)
            new_path = os.path.join(root, new_filename)
            rename_suggestions.append((old_path, new_path))

    if rename_suggestions:
        if display_rename_table(rename_suggestions):
            for old_path, new_path in rename_suggestions:
                try:
                    print(f"Renaming '{old_path}' to '{new_path}'")
                    os.rename(old_path, new_path)
                except Exception as e:
                    print(f"Failed to rename '{old_path}': {e}")
        else:
            print("No files were renamed.")
    else:
        print("No files to rename.")

def main(directory):
    episodes = get_episodes_from_tvmaze()
    if episodes:
        rename_files(directory, episodes)

if __name__ == "__main__":
    directory = sys.argv[3]
    main(directory)