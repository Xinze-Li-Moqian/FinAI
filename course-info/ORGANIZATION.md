# Repository organization

Updated 2026-09-20. The entire **FinAI** repository is the APS1053 workspace. [README.md](../README.md) is the course home. Each assignment records its own progress.

## Root directories

| Directory | Purpose |
|---|---|
| `course-info/` | Course requirements, schedule, organization rules, and organization notes |
| `assignments/` | All assessed work: 10% AI-Agent homework under `generative-ai/`; both case presentations, their case-selection materials, notebooks, and experiments under `presentations/` |
| `materials/` | Received instructor attachments and sample outputs, retaining their package structure and attribution |
| `readings/` | Reading guide and the `library/` of Markdown conversions, assets, concepts, and references |
| `notes/` | Personal course reflections and supplemental learning notes |
| `research/` | Optional verification research and historical background; not additional course requirements |
| `private/` | Ignored local source backups and the earlier private knowledge base |

The old `courses/APS1053/`, `materials/APS1053/`, and `knowledge/APS1053/` wrappers are removed. The repository is no longer presented as a multi-course or general financial-AI workspace. Broad ideas and other-course interests are retained under research rather than discarded.

## Adding files

Write our own filenames, documentation, and code comments in English. Preserve the filenames and attribution of received originals. Add new instructor versions under distinct names, recording their provenance. Link to shared source material instead of copying it into each assignment.

In each homework stage, use `scripts/` for code, `data/` for inputs and collected source text, `manifests/` for state and provenance, `analysis/` for our interpretation, and `generated/` for rebuildable outputs. Instructor sample outputs stay in `materials/`; our outputs belong to the relevant working area.

Maintain current actions and blockers in the relevant assignment README. The per-video backlog records download details and the inventory records machine-checked counts. Dated reviews describe the work performed at that date. Create final submission folders only when requirements and contents are known.

Keep transcript and generated-output folders collapsed during normal browsing. Archives, extracted sources, and reading copies have distinct purposes; they were not deleted as apparent duplicates. The personal API key remains only in the ignored repository-root `.env`.

## Migration record

| Former location | Current location |
|---|---|
| `courses/APS1053/README.md` | Root `README.md` |
| `courses/APS1053/course-info/`, `assignments/`, `notes/`, `research/` | Corresponding root directories |
| `courses/APS1053/presentations/` | `assignments/presentations/` |
| `courses/APS1053/cases/` before the first cleanup | `assignments/presentations/cases/` |
| `materials/APS1053/` | `materials/`, retaining package subdirectories |
| `knowledge/APS1053/` | `readings/library/`; personal code reviews and research plans are in `research/` |
| `reading/` | Supplemental note in `notes/` |
| `questions/`, `experiments/`, `discussions/` | Background files in `research/` |
| Earlier root README and multi-course index | `research/archive/` |
| Standalone task list and dashboard | Retired from the public workspace; progress consolidated into the relevant assignment README |
| `local-materials/` | `private/original-materials/`, still excluded from Git |

The first cleanup also grouped Part 1's formerly flat files into `scripts/`, `data/`, `manifests/`, and `analysis/`. Script paths, Markdown navigation, and generated transcript source paths were updated to the final root layout.

## Validation

The final layout is checked by rebuilding the corpus and theme outputs, validating source/generated checksums, checking local Markdown file targets, and loading the downloader's relocated state with network access disabled. Existing instructor attachment contents, experiment results, private backup contents, and credentials are preserved. External links and Markdown heading anchors are outside the local file-link check.

The remaining 12 transcript downloads, contextual review, and Part 2 remain open; reorganization does not mark them complete.


The former materials index and coverage pages are consolidated in `materials/README.md`. The full file catalog and publication manifest remain available there for lookup and provenance.
