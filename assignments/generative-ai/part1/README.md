# Generative AI homework — Part 1

APS1053 · Xinze Li · started 18 September 2026

[Assignment overview](../README.md) · [Course home](../../../README.md)

Prepare financial-video transcripts and a detailed title-based theme list for the later knowledge-base pipeline. The instructor's Part 1 handout says **nothing needs to be submitted yet** and gives no precise deadline.

## Current progress

Updated 2026-09-20. Part 1 is in progress; this is not a submission record.

- **980 transcripts prepared:** 952 supplied by the instructor and 28 additional downloads. All titles match; no files are empty or byte-identical duplicates; generated copies match source SHA-256 checksums.
- **12 of 40 update candidates remain.** The latest retries returned `IpBlocked`. The fixed update window is 2026-05-15 through 2026-09-18; see the [per-video backlog](manifests/BACKLOG.md) and [download log](manifests/download_log.json).
- **Theme list prepared:** 16 themes from 1,468 channel titles. There are 185 unmatched titles in the review queue; 119 have prepared transcripts. Keyword matches also need transcript-level evidence review.
- **Piazza:** the download problem was posted on 2026-09-20, as reported by the user. An instructor reply has not been checked.
- **DeepSeek:** the personal key is configured locally. Account credit and API authentication have not been verified; no paid API calls have been made for this work. The instructor requests CAD 12–15 of credit for later work.

### Next steps

1. Review a small group of related transcripts, correcting theme labels and preserving the author's claims, dates, and supporting passages.
2. Resume the remaining downloads when access is available or follow the instructor's Piazza guidance; then rebuild the corpus and theme index.
3. Confirm the detailed Part 2 requirements, submission arrangements, and deadline before running the full knowledge-base workflow and evaluation.

### Preparation history

| Date | Completed |
|---|---|
| 2026-09-18 | Prepared the Python environment, indexed 952 supplied transcripts and 1,468 titles, downloaded 16 additions, and built the first merged corpus and theme map |
| 2026-09-19 | Downloaded 12 more transcripts, expanded the taxonomy to 16 themes, prepared the review queue, configured the local API key, and validated the 980-transcript corpus |
| 2026-09-20 | Retried blocked downloads without new files; recorded the user-reported Piazza post; reorganized the workspace, rebuilt the corpus, and revalidated paths and checksums |

## Start here

| Need | Open |
|---|---|
| Remaining downloads and latest retry | [Download backlog](manifests/BACKLOG.md) |
| Exact corpus counts and quality checks | [Inventory](manifests/inventory.json) |
| Read the thematic findings | [Theme map](analysis/THEMES.md) and [review notes](analysis/THEME_REVIEW.md) |
| Review ambiguous titles | [Review queue](analysis/title_review_queue.csv) |
| Trace a transcript to its source | [Transcript manifest](manifests/transcript_manifest.csv) |

## File layout

| Directory | Contents | How to maintain it |
|---|---|---|
| `scripts/` | Download, preparation, and theme-processing Python code | Update code here; the workspace root is resolved from each script's location |
| `data/` | Saved channel snapshot, title index, and newly downloaded transcripts | Preserve the snapshot and downloaded source text; the title CSV is rebuilt from metadata and the corpus |
| `manifests/` | Download state, backlog, transcript checksums, and inventory | Downloader and preparation scripts update machine records; record retry outcomes in the backlog |
| `analysis/` | Theme rules, theme report, match evidence, and review queue | Edit theme rules and review notes; rebuild deterministic outputs with `build_themes.py` |
| `generated/` | Combined transcripts with date, title, and video ID filenames | Rebuildable local copies; ignored by Git |

The instructor's source corpus stays in [the original materials](../../../materials/03_Generative_AI_Assignment/Youtube_AI_students/transcripts_ids_upto_20260514/). The original dates come from supplied filenames, while new transcript dates come from YouTube metadata; the manifest records that distinction. Auto-generated subtitles may contain errors.

The downloader covers the fixed **2026-05-15 through 2026-09-18** snapshot for `@HeresyFinancial`. It does not audit older missing videos, Shorts, or livestreams. Do not replace `data/channel.json` with a later listing without reviewing the window and boundary.

## Run from this directory

Install the pinned download dependencies in an isolated environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Resume a small batch after access is available. Already downloaded IDs are skipped; blocking stops the run:

```bash
python scripts/download_gap.py --limit 2 --delay 25
```

Alternatively, use the existing `uv` environment:

```bash
uv run --with-requirements requirements.txt python scripts/download_gap.py --limit 2 --delay 25
```

Rebuild and check the local corpus, then refresh the title-theme reports. These steps use only the standard library and make no network or paid API requests:

```bash
python3 scripts/prepare.py --repo ../../.. --metadata data/channel.json --materialize
python3 scripts/build_themes.py
```

Materialization verifies each generated copy against its source SHA-256. Inspect `manifests/inventory.json` after rebuilding for unmatched titles, empty files, duplicates, and unresolved update candidates.

To collect metadata for a **future** snapshot, save it separately first:

```bash
python -m yt_dlp --flat-playlist --skip-download --socket-timeout 20 \
  --retries 1 --extractor-retries 1 --dump-single-json \
  'https://www.youtube.com/@HeresyFinancial/videos' > data/channel-next.json
```

## API configuration for later work

The personal DeepSeek key belongs only in the repository-root `.env`, using `DEEPSEEK_API_KEY`. Transcript preparation does not use it. Account credit and authentication are not yet verified; update the progress section above when checked. Keep credentials out of code, notebooks, logs, and submissions.

## Assignment sources

- [Part 1 handout](../../../materials/03_Generative_AI_Assignment/AssignmentOnGenerativeAIPart1.txt)
- [Instructor instructions](../../../materials/03_Generative_AI_Assignment/Youtube_AI_students/INSTRUCTIONS.txt)
- [Assessment and course arrangements](../../../course-info/README.md)

Theme matches are navigation aids. Read the transcript and preserve supporting passages before extracting claims for the later knowledge base.
