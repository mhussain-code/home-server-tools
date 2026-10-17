import sys
import os
import ffmpeg
import openl3
import soundfile as sf
import numpy as np
import csv
from scipy.spatial.distance import cosine
from tqdm import tqdm

# PARAMETERS
AUDIO_DURATION = 300  # analyze first 5 minutes
CHUNK_SIZE = 2        # 2 seconds per chunk
SIMILARITY_THRESHOLD = 0.90  # how similar chunks must be
MIN_CONSECUTIVE = 3   # at least 3 similar chunks = intro
OUTPUT_FILE = "detected_intros.csv"

def extract_audio(input_path, output_path):
    """Extract audio from video using ffmpeg"""
    (
        ffmpeg
        .input(input_path)
        .output(output_path, format='wav', acodec='pcm_s16le', ac=1, ar='16000', t=AUDIO_DURATION, map='a:0')
        .overwrite_output()
        .run(quiet=True)
    )

def get_audio_chunks(audio_path, model):
    """Get 2-sec audio embeddings from file"""
    audio, sr = sf.read(audio_path)
    if np.all(audio == 0):
        return None

    total_secs = len(audio) // sr
    embeddings = []
    for start_sec in range(0, min(total_secs, AUDIO_DURATION), CHUNK_SIZE):
        chunk = audio[start_sec*sr : (start_sec+CHUNK_SIZE)*sr]
        if len(chunk) == sr * CHUNK_SIZE:
            emb, _ = openl3.get_audio_embedding(chunk, sr, model=model)
            embeddings.append((emb[0], start_sec))
    return embeddings

def detect_intro(embeddings):
    """Detect intro chunks inside one episode"""
    if not embeddings:
        return None

    similarities = []
    timestamps = [ts for _, ts in embeddings]

    for i in range(len(embeddings) - 1):
        emb1, _ = embeddings[i]
        emb2, _ = embeddings[i+1]
        sim = 1 - cosine(emb1, emb2)
        similarities.append(sim)

    # Find consecutive high similarity chunks
    intro_segments = []
    current_segment = []

    for idx, sim in enumerate(similarities):
        if sim >= SIMILARITY_THRESHOLD:
            current_segment.append(timestamps[idx])
        else:
            if len(current_segment) >= MIN_CONSECUTIVE:
                intro_segments.append((current_segment[0], current_segment[-1] + CHUNK_SIZE))
            current_segment = []

    if len(current_segment) >= MIN_CONSECUTIVE:
        intro_segments.append((current_segment[0], current_segment[-1] + CHUNK_SIZE))

    return intro_segments if intro_segments else None

def seconds_to_timestamp(seconds):
    """Convert seconds to HH:MM:SS"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02}:{m:02}:{s:02}"

def main(input_folder):
    print("Loading OpenL3 model...")
    model = openl3.models.load_audio_embedding_model(input_repr="mel256", content_type="music", embedding_size=512)

    filenames = [f for f in os.listdir(input_folder) if f.lower().endswith(('.mp4', '.mkv', '.avi', '.mov'))]

    file_exists = os.path.exists(OUTPUT_FILE)
    with open(OUTPUT_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Filename", "Intro Start", "Intro End"])

        for filename in tqdm(filenames, desc="Processing episodes"):
            episode_path = os.path.join(input_folder, filename)
            audio_path = os.path.join(input_folder, "temp_audio.wav")

            try:
                extract_audio(episode_path, audio_path)
                embeddings = get_audio_chunks(audio_path, model)

                if embeddings is None:
                    print(f"Skipping {filename}: silent or bad audio.")
                    continue

                intro_segments = detect_intro(embeddings)

                if intro_segments:
                    for start, end in intro_segments:
                        writer.writerow([filename, seconds_to_timestamp(start), seconds_to_timestamp(end)])
                else:
                    print(f"No intro found for {filename}")

            except Exception as e:
                print(f"Error processing {filename}: {e}")

            finally:
                if os.path.exists(audio_path):
                    os.remove(audio_path)

    print(f"\nDone! Results saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    input_folder = sys.argv[1]
    main(input_folder)