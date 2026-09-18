# Generative AI assignment — Part 1

APS1053 · Xinze Li · started 18 September 2026

**Goal:** prepare the financial-video transcript corpus and a title-based theme list for the later knowledge-base pipeline. The instructor says **nothing needs to be submitted for Part 1 yet**. This is the preparatory stage of the 10% AI-Agent homework, separate from the two case presentations.

## Current status

**Started, not yet complete.** On 18 September 2026:

- Indexed all **952 supplied transcripts**, matched every video title, and checked for empty files and exact duplicates.
- Downloaded **16 additional transcripts**, giving **968 transcripts** in the prepared corpus.
- Saved **1,468 channel titles** and a **13-theme** preliminary map.
- Built the merged, title-named local corpus and verified byte-for-byte preservation against each source.
- **24 update candidates remain.** YouTube returned `IpBlocked` on video `YAwg5V95dQA`; the downloader stopped. Do not restart while the block persists. No proxy rotation or repeated retry loop was used.
- No paid API calls were made. The final knowledge-base synthesis and evaluation belong to Part 2 and are not completed here.

## Read the work

- [Theme map](THEMES.md): 13 provisional themes, subtopics and linked example videos.
- [Transcript manifest](transcript_manifest.csv): dates, titles, original paths, YouTube links, output filenames and SHA-256 checksums.
- [Channel title index](youtube_channel_videos.csv): 1,468 videos from the public `/videos` listing, retrieved 18 September 2026. A blank date means not retrieved.
- [Inventory](inventory.json): exact counts and data-quality checks from the latest preparation run.
- [Remaining downloads](BACKLOG.md): 24 candidates still to fetch.
- [Download log](download_log.json): per-video outcomes for the update batch.
- [New transcripts](new_transcripts/): additions to the instructor's corpus.

The original **952 transcripts** are already tracked under [the course attachments](../../../../../materials/APS1053/03_Generative_AI_Assignment/Youtube_AI_students/transcripts_ids_upto_20260514/). Their filenames span **2021-11-03 to 2026-05-14**; these dates are inherited from the instructor and have not been independently checked. All 952 video IDs match the current channel title index; none of the original files is empty or byte-identical to another.

## Work against the instructions

| Instruction | Implementation |
|---|---|
| Set up Python | Small isolated environment with the two required download libraries. The original Anaconda environment remains available in the course attachments. |
| Select the channel | `@HeresyFinancial`, as explicitly requested in `INSTRUCTIONS.txt`; the supplied transcripts also name this channel. |
| Fill the gap after 14 May | A bounded, resumable downloader processes the 40 entries preceding the instructor's latest video in the current channel listing, checking individual dates before saving. Consult the log for actual completion. This is not an audit of missing older videos, Shorts or livestreams. |
| Map IDs to titles | All supplied transcripts matched; channel-wide title CSV saved. Dates from original filenames and fresh YouTube metadata are labeled separately. |
| Extract themes from titles | Initial theme map saved. Explicit keyword matches support navigation and review, not factual verification or final semantic classification. |
| Rename and combine transcripts | `prepare.py --materialize` builds `generated/transcripts/`, preserving bytes. Names include date, title and video ID to avoid collisions. |
| Prepare DeepSeek for Part 2 | Not purchased or configured; no paid LLM calls made. |

The generated directory is intentionally not versioned: it duplicates tracked source transcripts exactly and can be rebuilt using the script and manifest. Original attachments and newly downloaded transcripts remain in the repository.

## Reproduce locally

Run from this directory. Python 3.12 was used for this run.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

# Fetch only public metadata; no account cookies or API key needed.
python -m yt_dlp --flat-playlist --skip-download --socket-timeout 20 \
  --retries 1 --extractor-retries 1 --dump-single-json \
  'https://www.youtube.com/@HeresyFinancial/videos' > channel.json

# Bounded continuation. Already completed IDs are skipped.
python download_gap.py --limit 4 --delay 25

# Rebuild the combined corpus, manifest and title map.
python prepare.py --repo ../../../../.. --metadata channel.json --materialize
python build_themes.py
```

`download_gap.py` is scoped to this assignment snapshot: 2026-05-15 through 2026-09-18, using the supplied 14 May video as its boundary. Review these settings before using it for a later update. It stops on unexpected/network errors instead of retrying indefinitely. This run initially used a 10-second inter-video pause; the conservative continuation default is 25 seconds. Dates and subtitles require separate public requests.

`prepare.py` and `build_themes.py` use only the Python standard library. After metadata and transcripts have been saved, the preparation stages work offline. Materialization checks that each copied file has the same SHA-256 as its source.

## What this prepares us for

Part 2 will synthesize transcripts into **Claim → Theme → Argument → Evidence & EvolutionOverTime**. For example, a video's forecast about inflation should retain its author, date and supporting passage; a later conflicting forecast should not silently overwrite it. The current title map does not establish financial truth or eliminate hallucinations.

The immediate next learning step is to inspect a small set of related transcripts, distinguish the speaker's claims from supporting evidence, and use that sample to assess the later synthesis pipeline. The full Part 2 requirements and grading details still need to be read when available.

## Assignment sources

- [Part 1 handout](../../../../../materials/APS1053/03_Generative_AI_Assignment/AssignmentOnGenerativeAIPart1.txt)
- [Original step-by-step instructions](../../../../../materials/APS1053/03_Generative_AI_Assignment/Youtube_AI_students/INSTRUCTIONS.txt)
- [Course administration / grading](../../../../../knowledge/APS1053/documents/ADMINISTRATIVE_APS1053/index.md)

The saved channel JSON contains public metadata, not video media. Auto-generated subtitles can contain transcription errors. Source links and checksums make the corpus traceable; they do not validate the speaker's economic claims.
