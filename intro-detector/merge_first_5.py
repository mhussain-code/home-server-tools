import sys
import os
import subprocess

def merge_first_5_mkvs(input_folder, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # List all MKV files sorted
    mkv_files = sorted([f for f in os.listdir(input_folder) if f.lower().endswith(".mkv")])
    mkv_files = mkv_files[:5]

    if len(mkv_files) == 0:
        print("Error: No MKV files found.")
        return

    # Full input paths
    mkv_paths = [os.path.join(input_folder, f) for f in mkv_files]

    # Name output after the first file
    base_name = os.path.splitext(mkv_files[0])[0]
    output_path = os.path.join(output_folder, base_name + ".mkv")

    # Build mkvmerge command with quotes around filenames
    command = ["mkvmerge", "-o", f'"{output_path}"']
    command.append(f'"{mkv_paths[0]}"')  # First file
    for extra_file in mkv_paths[1:]:
        command.append(f'+"{extra_file}"')  # Append next files

    print(f"Merging {len(mkv_files)} files into {output_path} using mkvmerge...")
    subprocess.run(" ".join(command), shell=True)

    print(f"\nDone! Merged file saved at:\n{output_path}")

if __name__ == "__main__":
    input_dir = sys.argv[1]
    output_file = sys.argv[2]

    merge_first_5_mkvs(input_dir, output_file)