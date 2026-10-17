import sys
import os
import subprocess
import xml.etree.ElementTree as ET
import shutil

def run_command(command_list, description="Running command"):
    """Run a system command and log it."""
    print(f"\n=== {description} ===")
    print("COMMAND:", " ".join(command_list))
    result = subprocess.run(command_list)
    if result.returncode != 0:
        print(f"ERROR during: {description}\n")
    else:
        print(f"Done: {description}\n")

def extract_chapters(mkv_path, chapter_xml_path):
    """Extract chapters from MKV."""
    description = f"Extracting chapters from {os.path.basename(mkv_path)}"
    print(f"\n=== {description} ===")
    command = f'mkvextract chapters "{mkv_path}" > "{chapter_xml_path}"'
    print("COMMAND:", command)
    result = subprocess.run(command, shell=True)
    if result.returncode != 0:
        print(f"ERROR during: {description}\n")
    else:
        print(f"Done: {description}\n")

def filter_chapters(chapter_xml_path, new_chapter_xml_path):
    """Keep only chapters 3 and 4."""
    print(f"\n=== Filtering chapters to keep only 3 and 4 in {os.path.basename(chapter_xml_path)} ===")
    tree = ET.parse(chapter_xml_path)
    root = tree.getroot()

    edition = root.find(".//EditionEntry")
    all_chapters = edition.findall("ChapterAtom")

    # Remove unwanted chapters
    for idx, chapter in enumerate(all_chapters):
        if idx not in [2, 3]:  # Keep chapter 3 and 4
            edition.remove(chapter)

    tree.write(new_chapter_xml_path, encoding="utf-8", xml_declaration=True)
    print("Done filtering chapters.\n")

def remux_with_chapters(original_mkv, new_chapter_xml, output_mkv):
    """Remux MKV using only selected chapters."""
    run_command(
        ["mkvmerge", "-o", output_mkv, "--chapters", new_chapter_xml, original_mkv],
        description=f"Remuxing MKV with chapters 3 and 4: {os.path.basename(original_mkv)}"
    )

def split_by_chapters(mkv_path, output_folder):
    """Split MKV by chapters."""
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    run_command(
        ["mkvmerge", "-o", os.path.join(output_folder, "split.mkv"), "--split", "chapters:all", mkv_path],
        description=f"Splitting MKV by chapters: {os.path.basename(mkv_path)}"
    )

def merge_two_clips(folder_path, output_path):
    """Merge two clips (chapter 3+4) into one clip."""
    clips = sorted([os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith(".mkv")])

    if len(clips) < 2:
        print(f"Error: Less than 2 clips found in {folder_path}")
        return

    run_command(
        ["mkvmerge", "-o", output_path, clips[0], f"+{clips[1]}"],
        description=f"Merging two chapter clips into: {os.path.basename(output_path)}"
    )

def merge_final_files(final_clips, output_path):
    """Merge all final clips into one big MKV."""
    if not final_clips:
        print("Error: No clips to merge.")
        return

    command = [
        "mkvmerge", "--append-mode", "track",
        "--no-track-tags", "--no-global-tags", "--engage", "no_variable_data",
        "-o", output_path, final_clips[0]
    ]
    for clip in final_clips[1:]:
        command.append(f"+{clip}")

    run_command(
        command,
        description="Merging all final files into one output"
    )

def fix_extra_audio_tracks(input_mkv, fixed_mkv):
    """Remove extra audio tracks if more than 2 exist."""
    print(f"\n=== Checking audio tracks in {os.path.basename(input_mkv)} ===")

    result = subprocess.run(["mkvmerge", "-i", input_mkv], capture_output=True, text=True)
    output = result.stdout

    audio_tracks = [line for line in output.splitlines() if "audio" in line]

    if len(audio_tracks) <= 2:
        print("Audio tracks OK. No fix needed.")
        shutil.copy(input_mkv, fixed_mkv)
        return

    # Keep first two audio tracks (normally 0 and 1)
    track_ids = []
    for line in output.splitlines():
        if "audio" in line:
            parts = line.split()
            track_id = parts[2][:-1]  # format: "ID n:"
            track_ids.append(track_id)

    keep_tracks = ",".join(track_ids[:2])

    run_command(
        ["mkvmerge", "-o", fixed_mkv, "--audio-tracks", keep_tracks, input_mkv],
        description=f"Fixing audio: keeping tracks {keep_tracks}"
    )

def main():
    print("\n===== Auto-Cut and Merge Program Started =====\n")

    input_folder = sys.argv[1]
    output_folder = sys.argv[2]

    temp_folder = os.path.join(output_folder, "temp")
    if not os.path.exists(temp_folder):
        os.makedirs(temp_folder)

    mkv_files = sorted([f for f in os.listdir(input_folder) if f.lower().endswith(".mkv")])

    if len(mkv_files) < 5:
        print("\nError: Less than 5 MKV files found in input folder.\n")
        return

    mkv_files = mkv_files[:5]  # Only first 5 episodes

    final_clips = []
    for idx, mkv_file in enumerate(mkv_files):
        print(f"\n=== Processing file {idx+1}: {mkv_file} ===")

        original_mkv_path = os.path.join(input_folder, mkv_file)
        base_name = os.path.splitext(mkv_file)[0]

        fixed_mkv_path = os.path.join(temp_folder, f"{base_name}_fixed.mkv")
        chapter_xml = os.path.join(temp_folder, f"{base_name}_chapters.xml")
        new_chapter_xml = os.path.join(temp_folder, f"{base_name}_filtered_chapters.xml")
        remuxed_mkv = os.path.join(temp_folder, f"{base_name}_remuxed.mkv")
        split_folder = os.path.join(temp_folder, f"{base_name}_split")
        merged_clip = os.path.join(temp_folder, f"{base_name}_final.mkv")

        # 0. Fix extra audio tracks
        fix_extra_audio_tracks(original_mkv_path, fixed_mkv_path)

        # 1. Extract chapters
        extract_chapters(fixed_mkv_path, chapter_xml)

        # 2. Filter chapters (keep only 3 and 4)
        filter_chapters(chapter_xml, new_chapter_xml)

        # 3. Remux with filtered chapters
        remux_with_chapters(fixed_mkv_path, new_chapter_xml, remuxed_mkv)

        # 4. Split MKV
        split_by_chapters(remuxed_mkv, split_folder)

        # 5. Merge 2 selected chapters
        merge_two_clips(split_folder, merged_clip)

        final_clips.append(merged_clip)

    # 6. Merge all final files
    first_base_name = os.path.splitext(mkv_files[0])[0]
    final_output_path = os.path.join(output_folder, f"{first_base_name}_merged.mkv")

    merge_final_files(final_clips, final_output_path)

    # 7. Clean up
    print("\nCleaning up temporary files...")
    shutil.rmtree(temp_folder)

    print(f"\n===== All Done! Final merged file saved at: =====\n{final_output_path}\n")

if __name__ == "__main__":
    main()