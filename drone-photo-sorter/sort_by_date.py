import sys
import os
import time
import shutil
import datetime

# Path to the SD card location
# Folder on the SD card, e.g. /Volumes/Drone/DCIM/DJI_001
sd_card_path = sys.argv[1]


# Function to handle each file
def handle_file(file_path, file):
    # Skip hidden files
    if file.startswith('.'):
        return

    # Try to get the creation time of the file
    try:
        creation_time = os.path.getctime(file_path)
    except FileNotFoundError:
        print(f"File {file} not found. Skipping...")
        return

    # Convert the creation time to the original format (e.g., 2023-12-16)
    formatted_date = time.strftime("%Y-%m-%d", time.localtime(creation_time))

    # Create the destination folder path based on the formatted date
    destination_folder = os.path.join(sd_card_path, formatted_date)

    # Create the destination folder if it doesn't exist
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)

    # Move the file to the destination folder
    shutil.move(file_path, os.path.join(destination_folder, file))

# Function to recursively traverse directories
def traverse_dir(dir_path):
    for item in os.listdir(dir_path):
        item_path = os.path.join(dir_path, item)
        if os.path.isfile(item_path):
            handle_file(item_path, item)
        elif os.path.isdir(item_path):
            # If the directory is named like '20', '23', '12', etc., or a date, handle the files inside
            if item.isdigit() or "-" in item:
                # Check if the directory name is a valid date
                try:
                    datetime.datetime.strptime(item, "%Y-%m-%d")
                except ValueError:
                    # If not, rename the directory to the correct date format
                    correct_date = datetime.datetime.strptime(item, "%d-%m-%y").strftime("%Y-%m-%d")
                    correct_path = os.path.join(dir_path, correct_date)

                    # If the correct_path directory already exists, move the files from item_path to correct_path
                    if os.path.exists(correct_path):
                        for file in os.listdir(item_path):
                            shutil.move(os.path.join(item_path, file), correct_path)
                    else:
                        os.rename(item_path, correct_path)

                    item_path = correct_path

                for subitem in os.listdir(item_path):
                    subitem_path = os.path.join(item_path, subitem)
                    if os.path.isfile(subitem_path):
                        handle_file(subitem_path, subitem)
            else:
                traverse_dir(item_path)

# Start the traversal
traverse_dir(sd_card_path)