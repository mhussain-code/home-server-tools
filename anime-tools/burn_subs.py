import sys
import subprocess
import os


def extract_and_burn_subtitles(video_path, output_folder):
    base_name = os.path.basename(video_path)
    output_path = os.path.join(output_folder, base_name)

    # Check if the output file already exists
    if os.path.exists(output_path):
        print(f"Output file {output_path} already exists. Skipping.")
        return

    # Create a unique name for the subtitle file
    subtitle_filename = f"temp_{os.path.splitext(base_name)[0]}.srt"
    subtitle_path = os.path.join(output_folder, subtitle_filename)

    # Extract subtitles
    try:
        subprocess.run(["ffmpeg", "-y", "-i", video_path, "-map", "0:s:0", subtitle_path], check=True)
        print(f"Subtitles extracted for {base_name}")
    except subprocess.CalledProcessError as e:
        print(f"Error extracting subtitles for {base_name}: {e}")
        return

    # Burn subtitles with specified font size and maintain quality
    try:
        subtitles_filter = f"subtitles='{subtitle_path}':force_style='Fontsize=18'"
        # Adjust CRF for quality (lower is better) and use a slower preset for better compression
        subprocess.run(["ffmpeg", "-y", "-i", video_path, "-vf", subtitles_filter, 
                        "-c:a", "copy", "-crf", "18", "-preset", "slow", output_path], check=True)
        print(f"Subtitles burned successfully into {output_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error burning subtitles for {base_name}: {e}")

    # Delete temporary subtitle file
    if os.path.exists(subtitle_path):
        os.remove(subtitle_path)

def process_folder(folder_path, output_folder):
    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Sort files to ensure they are processed in order
    sorted_files = sorted([f for f in os.listdir(folder_path) if f.endswith(".mp4")])

    # Process each MP4 file in the folder
    for file_name in sorted_files:
        video_path = os.path.join(folder_path, file_name)
        extract_and_burn_subtitles(video_path, output_folder)

# Example usage
input_folder = sys.argv[1]
output_folder = sys.argv[2]
process_folder(input_folder, output_folder)

