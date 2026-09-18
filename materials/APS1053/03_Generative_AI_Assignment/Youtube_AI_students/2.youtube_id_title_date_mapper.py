# -*- coding: utf-8 -*-
"""
YouTube channel video exporter

Purpose:
- Retrieve all videos from a YouTube channel
- Export video metadata to CSV
- Does NOT download videos or transcripts

CSV columns:
    video_id
    upload_date
    video_title

Spyder-friendly:
- Edit SETTINGS section
- Press Run
"""

from __future__ import annotations

import csv
import random
import re
import time
from pathlib import Path

import yt_dlp


# ============================================================
# SETTINGS
# ============================================================

# Examples:
# CHANNEL = "@FelixFriends"
# CHANNEL = "UCxxxxxxxxxxxxxxxx"
# CHANNEL = "https://www.youtube.com/@FelixFriends"

CHANNEL = "@HeresyFinancial"

# Output CSV file
OUTPUT_FILE = Path("youtube_channel_videos.csv")

# Conservative pacing
CHANNEL_REQUEST_DELAY = (3, 7)

# ============================================================


def sleep_range(delay_range: tuple[float, float]) -> None:
    time.sleep(random.uniform(*delay_range))


def normalize_channel_input(channel: str) -> str:
    channel = channel.strip()

    if channel.startswith("http://") or channel.startswith("https://"):
        return channel

    if channel.startswith("@"):
        return f"https://www.youtube.com/{channel}"

    if re.fullmatch(r"UC[\w-]{22}", channel):
        return f"https://www.youtube.com/channel/{channel}"

    return f"https://www.youtube.com/{channel}"


def ensure_output_header(output_file: Path) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "video_id",
                "upload_date",
                "video_title",
            ],
        )
        writer.writeheader()


def get_channel_entries(channel: str) -> list[dict]:
    """
    Retrieve all videos from the YouTube channel.
    """

    base_url = normalize_channel_input(channel).rstrip("/")

    candidates = [
        base_url + "/videos",
        base_url,
        base_url + "/streams",
    ]

    ydl_opts = {
        "quiet": True,
        "extract_flat": True,
        "skip_download": True,
        "ignoreerrors": True,
        "nocheckcertificate": True,
    }

    for url in candidates:
        print(f"Trying channel URL: {url}")

        sleep_range(CHANNEL_REQUEST_DELAY)

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

        except Exception as e:
            print(f"Error fetching {url}: {e}")
            continue

        entries = info.get("entries", [])

        if entries:
            print(f"Found {len(entries)} videos")
            return entries

    print("WARNING: No channel entries found.")
    return []


def format_upload_date(upload_date: str) -> str:
    """
    Convert YYYYMMDD -> YYYY-MM-DD
    """

    if not upload_date:
        return ""

    if len(upload_date) != 8:
        return upload_date

    return (
        f"{upload_date[0:4]}-"
        f"{upload_date[4:6]}-"
        f"{upload_date[6:8]}"
    )


def main() -> int:

    print("Starting YouTube channel exporter...\n")
    print(f"Channel:     {CHANNEL}")
    print(f"Output file: {OUTPUT_FILE.resolve()}")

    ensure_output_header(OUTPUT_FILE)

    print("\nFetching channel videos...\n")

    entries = get_channel_entries(CHANNEL)

    if not entries:
        print("No videos found.")
        return 1

    written = 0

    with open(OUTPUT_FILE, "a", encoding="utf-8-sig", newline="") as f:

        writer = csv.DictWriter(
            f,
            fieldnames=[
                "video_id",
                "upload_date",
                "video_title",
            ],
        )

        for idx, entry in enumerate(entries, start=1):

            if not entry:
                continue

            video_id = (entry.get("id") or "").strip()
            title = (entry.get("title") or "").strip()

            upload_date = format_upload_date(
                entry.get("upload_date", "")
            )

            if not video_id:
                continue

            writer.writerow({
                "video_id": video_id,
                "upload_date": upload_date,
                "video_title": title,
            })

            written += 1

            print(
                f"[{idx}] "
                f"{video_id} | "
                f"{upload_date} | "
                f"{title}"
            )

    print("\nDone.")
    print(f"Videos written: {written}")
    print(f"CSV saved to:   {OUTPUT_FILE.resolve()}")

    return 0


if __name__ == "__main__":
    main()