import os
import time
import subprocess
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

def convert_file(file_path):
    if file_path.endswith('.mkv') and '.crdownload' not in file_path:
        mp4_file = file_path.replace('.mkv', '.mp4')
        result = subprocess.run(['ffmpeg', '-i', file_path, '-codec', 'copy', mp4_file], capture_output=True, text=True)
        if result.returncode == 0:  # If the conversion was successful
            print(f"Conversion of {file_path} was successful. Deleting the source file.")
            os.remove(file_path)  # Delete the source file
        else:
            print(f"Conversion of {file_path} failed. Not deleting the source file. Error: {result.stderr}")

def on_created(event):
    print(f"{event.src_path} has been created!")
    convert_file(event.src_path)

def on_deleted(event):
    print(f"{event.src_path} has been deleted!")

def on_modified(event):
    print(f"{event.src_path} has been modified")

def on_moved(event):
    print(f"{event.src_path} moved to {event.dest_path}")

def convert_existing_files(path):
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith('.mkv'):
                file_path = os.path.join(root, file)
                convert_file(file_path)

if __name__ == "__main__":
    patterns = "*"
    ignore_patterns = ""
    ignore_directories = False
    case_sensitive = True
    my_event_handler = PatternMatchingEventHandler(patterns, ignore_patterns, ignore_directories, case_sensitive)

    my_event_handler.on_created = on_created
    my_event_handler.on_deleted = on_deleted
    my_event_handler.on_modified = on_modified
    my_event_handler.on_moved = on_moved

    path = os.getcwd()
    go_recursively = True
    my_observer = Observer()
    my_observer.schedule(my_event_handler, path, recursive=go_recursively)

    # convert all existing .mkv files in the directory
    convert_existing_files(path)

    my_observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        my_observer.stop()
        my_observer.join()
