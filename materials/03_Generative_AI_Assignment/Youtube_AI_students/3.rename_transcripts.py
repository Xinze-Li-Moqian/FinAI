"""
rename_transcripts.py

INPUT1: Transcript .md files in transcripts_ids/ folder (working directory)
        Filename format: YYYYMMDD_VIDEOID.md

INPUT2: youtube_channel_videos.csv in working directory
        Columns: video_id, upload_date, video_title

OUTPUT: transcripts/ folder containing renamed transcripts:
        Filename format: YYYYMMDD_VIDEOTITLE.md
"""

import os
import re
import shutil
import csv


def sanitize_filename(name: str) -> str:
    """Remove or replace characters that are invalid in filenames."""
    # Replace characters that are problematic on Windows/Mac/Linux
    name = re.sub(r'[\\/*?:"<>|]', '', name)
    # Replace newlines/tabs with spaces
    name = re.sub(r'[\n\r\t]', ' ', name)
    # Collapse multiple spaces
    name = re.sub(r' +', ' ', name)
    return name.strip()


def main():
    # ── Paths ──────────────────────────────────────────────────────────────
    working_dir       = os.getcwd()                                  # Spyder CWD
    transcripts_ids   = os.path.join(working_dir, 'transcripts_ids') # INPUT1
    csv_path          = os.path.join(working_dir, 'youtube_channel_videos.csv')  # INPUT2
    output_dir        = os.path.join(working_dir, 'transcripts')     # OUTPUT

    # ── Validate inputs ────────────────────────────────────────────────────
    if not os.path.isdir(transcripts_ids):
        raise FileNotFoundError(
            f"Source folder not found: {transcripts_ids}\n"
            "Make sure 'transcripts_ids/' exists in your Spyder working directory."
        )
    if not os.path.isfile(csv_path):
        raise FileNotFoundError(
            f"CSV file not found: {csv_path}\n"
            "Make sure 'youtube_channel_videos.csv' is in your Spyder working directory."
        )

    # ── Load CSV into a dict {video_id -> video_title} ────────────────────
    video_lookup: dict[str, str] = {}
    with open(csv_path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            vid   = row['video_id'].strip()
            title = row['video_title'].strip()
            if vid:
                video_lookup[vid] = title

    print(f"Loaded {len(video_lookup)} video records from CSV.")

    # ── Create output directory ────────────────────────────────────────────
    os.makedirs(output_dir, exist_ok=True)
    print(f"Output directory: {output_dir}")

    # ── Process each transcript ────────────────────────────────────────────
    txt_files = [f for f in os.listdir(transcripts_ids) if f.endswith('.md')]
    if not txt_files:
        print("No .md files found in transcripts_ids/. Nothing to do.")
        return

    success = skipped = 0

    for filename in sorted(txt_files):
        stem = os.path.splitext(filename)[0]          # e.g. 20251010_yHsF-FsJDE4

        # Parse date and video_id
        parts = stem.split('_', 1)
        if len(parts) != 2:
            print(f"  [SKIP] Cannot parse filename: {filename}")
            skipped += 1
            continue

        date_part, video_id = parts[0], parts[1]

        # Validate date portion (8 digits)
        if not re.fullmatch(r'\d{8}', date_part):
            print(f"  [SKIP] Date portion '{date_part}' is not YYYYMMDD: {filename}")
            skipped += 1
            continue

        # Look up video title
        if video_id not in video_lookup:
            print(f"  [SKIP] video_id '{video_id}' not found in CSV: {filename}")
            skipped += 1
            continue

        video_title   = sanitize_filename(video_lookup[video_id])
        new_filename  = f"{date_part}_{video_title}.md"
        src_path      = os.path.join(transcripts_ids, filename)
        dst_path      = os.path.join(output_dir, new_filename)

        shutil.copy2(src_path, dst_path)
        print(f"  [OK]   {filename}  →  {new_filename}")
        success += 1

    # ── Summary ───────────────────────────────────────────────────────────
    print(f"\nDone. {success} file(s) renamed, {skipped} skipped.")


if __name__ == '__main__':
    main()
