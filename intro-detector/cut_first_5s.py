import sys
import os
import subprocess

def cut_first_5_seconds(input_folder, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    for filename in os.listdir(input_folder):
        if filename.lower().endswith(".mkv"):
            input_path = os.path.join(input_folder, filename)
            output_path = os.path.join(output_folder, filename)

            # Corrected ffmpeg command
            command = [
                "ffmpeg",
                "-y",  # Overwrite output
                "-i", input_path,  # Input first (for safer seeking with subtitles)
                "-ss", "00:00:05",  # Start time after input
                "-map", "0",  # Map all streams: video, audio, subs
                "-c", "copy",  # Copy all streams
                output_path
            ]

            print(f"Processing {filename}...")
            subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    print("\nDone! All files processed.")

if __name__ == "__main__":
    input_dir = sys.argv[1]
    output_dir = sys.argv[2]

    cut_first_5_seconds(input_dir, output_dir)