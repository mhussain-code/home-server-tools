# Home server tools

Python scripts I wrote for the Linux server I run at home. The server hosts my website and a Plex media library, so most of these handle video files. Each folder is a separate tool with its own command-line entry points.

## Requirements

- Python 3 and the packages in `requirements.txt` (grouped by tool in the file)
- [ffmpeg](https://ffmpeg.org/) for all the video tools
- [MKVToolNix](https://mkvtoolnix.download/) (`mkvextract` and `mkvmerge`) for the intro tools

```
pip install -r requirements.txt
```

## Configuration

API keys are read from environment variables. See `.env.example`.

| Variable | Used by |
|---|---|
| `TMDB_API_KEY` | `renamer/movie_rename.py` |
| `ANIME_SKIP_TOKEN`, `ANIME_SKIP_CLIENT_ID` | `anime-tools/skip_times.py` |

## Tools

### intro-detector

Finds the opening theme in each episode of a show so it can be skipped.

| Command | What it does |
|---|---|
| `detect_intros.py <folder>` | Takes the first five minutes of each episode's audio, splits it into 2-second chunks and gets an OpenL3 audio embedding for each chunk. Three or more chunks in a row with cosine similarity above 0.9 count as the intro. Writes start and end times to `detected_intros.csv` |
| `chapter_merge.py <input folder> <output folder>` | For MKV files that already have chapters. Keeps chapters 3 and 4, splits the file by chapter, joins the two clips and fixes the audio tracks |
| `cut_first_5s.py <input folder> <output folder>` | Trims the first five seconds off every MKV in a folder |
| `merge_first_5.py <input folder> <output folder>` | Joins the first five MKVs in a folder into one file |

### mkv-to-mp4-watcher

`convert_watch.py` watches the folder it is run from. When an MKV appears, ffmpeg copies the streams into an MP4 without re-encoding, and the MKV is deleted if that worked. MKVs already in the folder are converted on start-up.

### renamer

Renames episodes and films so Plex matches them.

| Command | What it does |
|---|---|
| `tv_rename.py <tvmaze id> "<show name>" <folder>` | Gets the episode list from the TVMaze API and renames files to `Show - S01E01 - Title` |
| `tv_rename_absolute.py` | Same, for shows whose files are numbered straight through instead of by season |
| `movie_rename.py <folder>` | Reads title and year from each file name with guessit and searches TMDb. I check and edit the matches in the terminal, then it renames the films and their subtitles |

### anime-tools

| Command | What it does |
|---|---|
| `burn_subs.py <input folder> <output folder>` | Extracts the subtitle track from each video and burns it into the picture with ffmpeg |
| `skip_times.py <MyAnimeList id> <episode>` | Queries the anime-skip.com GraphQL API for an episode's skip times (start, end and type of each section) |

### drone-photo-sorter

`sort_by_date.py <SD card folder>` moves drone photos and videos into folders named by each file's creation date.

### pdf-tools

| Command | What it does |
|---|---|
| `split_pdf.py <file>` | Splits a PDF into two halves |
| `pdf_to_epub.py <pdf> <epub>` | Converts a PDF to EPUB, going through Word format first |

## Licence

MIT. See `LICENSE`.
