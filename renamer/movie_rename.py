import sys
import os
import re
import unicodedata
from tmdbv3api import TMDb, Movie
from tabulate import tabulate
from guessit import guessit

# Initialize TMDb API
tmdb = TMDb()
tmdb.api_key = os.environ['TMDB_API_KEY']
movie_api = Movie()

# Define valid movie and subtitle file extensions
MOVIE_EXTENSIONS = ['.mp4', '.mkv', '.avi', '.mov']
SUBTITLE_EXTENSIONS = ['.srt', '.sub', '.ass']

# Use guessit to extract movie title and year from the file name
def extract_title_and_year(file_name):
    guess = guessit(file_name)
    title = guess.get('title', '')
    year = guess.get('year', None)
    return title, str(year) if year else None

# Sanitize filenames by removing invalid characters
def sanitize_filename(filename):
    # Normalize Unicode characters
    normalized_filename = unicodedata.normalize('NFKD', filename)
    # Encode to ASCII, ignoring errors
    ascii_bytes = normalized_filename.encode('ascii', 'ignore')
    # Decode back to a string
    ascii_filename = ascii_bytes.decode('ascii')
    # Remove invalid filename characters
    sanitized_filename = re.sub(r'[<>:"/\\|?*]', '', ascii_filename).strip()
    return sanitized_filename

def list_movie_files(directory):
    movie_files = []
    subtitle_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.startswith("._"):
                continue  # Ignore macOS hidden dot-underscore files

            file_ext = os.path.splitext(file)[1].lower()
            full_path = os.path.join(root, file)  # Get full file path
            if file_ext in MOVIE_EXTENSIONS:
                movie_files.append(full_path)
            elif file_ext in SUBTITLE_EXTENSIONS:
                subtitle_files.append(full_path)
    return movie_files, subtitle_files

def find_subtitles(movie_file, subtitle_files):
    movie_base = os.path.splitext(movie_file)[0]
    return [s for s in subtitle_files if os.path.splitext(s)[0] == movie_base]

def search_movie_tmdb(movie_title, year=None, num_results=10):
    search_results = movie_api.search(movie_title)
    matches = []

    for result in search_results:
        if hasattr(result, 'title') and hasattr(result, 'release_date'):
            result_year = result.release_date[:4]
            match_str = f"{result.title} ({result_year})"
            if not year or result_year == year:
                if match_str not in matches:
                    matches.append(match_str)
            elif not year:
                if match_str not in matches:
                    matches.append(match_str)
            if len(matches) >= num_results:
                break
    return matches

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def process_directory(directory):
    movie_files, subtitle_files = list_movie_files(directory)

    if not movie_files:
        print("No movie files found.")
        return

    file_mappings = []

    # Process movies and prepare old and new name mappings
    for idx, movie in enumerate(movie_files, start=1):
        # Extract movie title and year from the file name
        movie_file_name = os.path.basename(movie)
        movie_title, movie_year = extract_title_and_year(movie_file_name)

        # Search for the movie on TMDb using title and year
        tmdb_matches = search_movie_tmdb(movie_title, movie_year)
        if not tmdb_matches:
            # Try searching without the year
            tmdb_matches = search_movie_tmdb(movie_title)
        if tmdb_matches:
            # Take the first match as the default new name
            tmdb_match = tmdb_matches[0]
            # Sanitize and clean the match
            tmdb_match_clean = sanitize_filename(tmdb_match)
            # Ensure the sanitized filename is not empty
            if not tmdb_match_clean:
                tmdb_match_clean = 'Unnamed'
            new_name = tmdb_match_clean + os.path.splitext(movie)[1]  # Keep the same extension
            file_mappings.append({'old_path': movie, 'new_name': new_name, 'tmdb_matches': tmdb_matches, 'status': 'Pending'})
        else:
            # No match found
            file_mappings.append({'old_path': movie, 'new_name': 'No match found', 'tmdb_matches': [], 'status': 'Pending'})

        # Clear the screen and display table
        clear_screen()
        headers = ["Old Name", "New Name", "Status"]
        display_data = [(os.path.basename(fm['old_path']), fm['new_name'], fm['status']) for fm in file_mappings]
        print(f"Processing file {idx}/{len(movie_files)}:")
        print(tabulate(display_data, headers=headers))

    # Now, allow the user to review and edit the mappings
    review_and_edit_mappings(file_mappings, subtitle_files)

def review_and_edit_mappings(file_mappings, subtitle_files):
    # First, display the mappings
    while True:
        clear_screen()
        headers = ["Index", "Old Name", "New Name", "Status"]
        display_data = []
        for idx, fm in enumerate(file_mappings, start=1):
            display_data.append((idx, os.path.basename(fm['old_path']), fm['new_name'], fm['status']))

        print("Review and Edit Mappings:")
        print(tabulate(display_data, headers=headers))

        print("\nOptions:")
        print("Enter the index number to edit a file.")
        print("Enter 'r' to rename all pending files.")
        print("Enter 's' to skip renaming and exit.")
        choice = input("Your choice: ")

        if choice.lower() == 'r':
            # Proceed to rename files
            perform_renaming(file_mappings, subtitle_files)
            break
        elif choice.lower() == 's':
            print("Exiting without renaming.")
            break
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(file_mappings):
                edit_mapping(file_mappings[idx])
            else:
                print("Invalid index.")
                input("Press Enter to continue...")
        else:
            print("Invalid choice.")
            input("Press Enter to continue...")

def edit_mapping(mapping):
    old_name = os.path.basename(mapping['old_path'])
    print(f"Editing: {old_name}")
    print(f"Current new name: {mapping['new_name']}")

    if mapping['new_name'] == 'No match found' or not mapping['tmdb_matches']:
        # No matches found, allow user to enter a new search term
        new_search_term = input("Enter new search term (or press Enter to skip): ")
        if new_search_term:
            new_tmdb_matches = search_movie_tmdb(new_search_term)
            if new_tmdb_matches:
                print("Please select the correct movie:")
                for idx, match in enumerate(new_tmdb_matches):
                    print(f"{idx + 1}. {match}")
                selection = input("Enter the number of the correct movie (or press Enter to skip): ")
                if selection.isdigit():
                    selection_idx = int(selection) - 1
                    if 0 <= selection_idx < len(new_tmdb_matches):
                        selected_match = new_tmdb_matches[selection_idx]
                        tmdb_match_clean = sanitize_filename(selected_match)
                        if not tmdb_match_clean:
                            tmdb_match_clean = 'Unnamed'
                        mapping['new_name'] = tmdb_match_clean + os.path.splitext(mapping['old_path'])[1]
                        mapping['tmdb_matches'] = new_tmdb_matches
                        mapping['status'] = 'Pending'
                    else:
                        print("Invalid selection.")
                else:
                    print("No selection made.")
            else:
                print(f"No matches found for '{new_search_term}'")
                input("Press Enter to continue...")
        else:
            print("Skipped editing.")
    else:
        # Show existing matches and allow user to select
        print("Please select the correct movie:")
        for idx, match in enumerate(mapping['tmdb_matches']):
            print(f"{idx + 1}. {match}")
        selection = input("Enter the number of the correct movie (or press Enter to skip): ")
        if selection.isdigit():
            selection_idx = int(selection) - 1
            if 0 <= selection_idx < len(mapping['tmdb_matches']):
                selected_match = mapping['tmdb_matches'][selection_idx]
                tmdb_match_clean = sanitize_filename(selected_match)
                if not tmdb_match_clean:
                    tmdb_match_clean = 'Unnamed'
                mapping['new_name'] = tmdb_match_clean + os.path.splitext(mapping['old_path'])[1]
                mapping['status'] = 'Pending'
            else:
                print("Invalid selection.")
        else:
            print("No selection made.")

def perform_renaming(file_mappings, subtitle_files):
    for mapping in file_mappings:
        old_path = mapping['old_path']
        old_name = os.path.basename(old_path)
        new_name = mapping['new_name']
        status = mapping['status']

        if status != 'Pending':
            continue  # Skip files not marked as pending

        if new_name == "No match found" or new_name.strip() == '':
            print(f"Skipping {old_name} because no new name was provided.")
            continue

        if old_name == new_name:
            print(f"Skipping {old_name} because the name is already correct.")
            continue

        new_path = os.path.join(os.path.dirname(old_path), new_name)

        # Ensure new_path is not equal to the directory path
        if os.path.abspath(new_path) == os.path.abspath(os.path.dirname(old_path)):
            print(f"Error: New filename '{new_name}' is invalid or conflicts with directory name.")
            continue

        # Check if the new path already exists
        if os.path.exists(new_path):
            print(f"Error: A file or directory with the name '{new_name}' already exists.")
            continue

        # Verify that the source file exists
        if not os.path.exists(old_path):
            print(f"Source file does not exist: {old_path}")
            continue

        # Find matching subtitle files and rename them together with the movie
        matched_subtitles = find_subtitles(old_path, subtitle_files)

        try:
            os.rename(old_path, new_path)
            print(f"Renamed {old_name} to {new_name}")

            # Rename the corresponding subtitle files
            for subtitle in matched_subtitles:
                subtitle_old_name = os.path.basename(subtitle)
                subtitle_new_name = os.path.splitext(new_name)[0] + os.path.splitext(subtitle)[1]
                subtitle_new_path = os.path.join(os.path.dirname(subtitle), subtitle_new_name)

                os.rename(subtitle, subtitle_new_path)
                print(f"Renamed {subtitle_old_name} to {subtitle_new_name}")
            mapping['status'] = 'Renamed'
        except OSError as e:
            print(f"Error renaming {old_name} to {new_name}: {e}")
            mapping['status'] = 'Error'

def main():
    directory_to_scan = sys.argv[1]

    if not os.path.exists(directory_to_scan):
        print(f"Directory {directory_to_scan} does not exist.")
        return

    # Process the directory
    process_directory(directory_to_scan)

if __name__ == "__main__":
    main()
