# APS1053 — Case Studies in AI in Finance

Course materials and coursework for APS1053, Fall 2026 · Xinze Li.

This repository contains the instructor materials received so far, readable lecture copies, and my work on the course assignments. [Course requirements and schedule](course-info/README.md) · [Piazza](https://piazza.com/class/mtus078qonq1qb)

## Assignments

| Assignment | Weight | Open |
|---|---|---|
| AI-Agent / Generative AI homework | 10% | [Instructions and workspace](assignments/generative-ai/README.md) · [Part 1 progress](assignments/generative-ai/part1/README.md#current-progress) |
| First case presentation | 45% | [Case 44 candidate workspace](assignments/presentations/01-case44-candidate/README.md) |
| Second case presentation | 45% | [Second presentation workspace](assignments/presentations/02-unassigned/README.md) |

These weights follow the tentative administrative scheme. Case assignments and presentation dates still need instructor confirmation. The syllabus also mentions a final-project alternative; its availability has not been confirmed. See [assessment details](course-info/README.md#assessment-and-deliverables).

Progress and next steps are recorded within each assignment. [All assignments](assignments/README.md) · [Presentation requirements](assignments/presentations/REQUIREMENTS.md) · [Case-selection guide](assignments/presentations/cases/README.md)

## Materials and books

- **[Course materials](materials/README.md)** — syllabus, slides, instructor code, supplied transcripts, books, and sample outputs, with an explanation of what is included.
- **[Reading guide](readings/README.md)** — Markdown lecture copies, concepts, and references for reading in the browser.
- **[Book availability](materials/README.md#books)** — the supplied Prolog and prompting books are saved locally. The six case-reference textbooks currently have access links; their full texts have not been found in the received files. This includes the book used for Case 44.
- [Attachment archives](https://github.com/Xinze-Li-Moqian/FinAI/releases/tag/course-materials-2026-09-18) — the packaged downloads accompanying the extracted materials.

## Repository layout

| Folder | Purpose |
|---|---|
| `assignments/` | All assessed work: the AI-Agent homework and both case presentations |
| `course-info/` | Course rules, schedule, and organization notes |
| `materials/` | Instructor attachments and sample outputs in their source package structure |
| `readings/` | Reading guide and Markdown versions of the lectures |
| `research/` | Optional research ideas and earlier background notes |

Instructor sample results remain in `materials/`; my own code, data, and results stay with the relevant assignment. Rebuildable Part 1 transcript copies live in its Git-ignored `generated/` directory.

`private/` and `.env` are local-only backups and API configuration, excluded from Git. Original material attribution is retained. This is a student workspace, and the files received so far do not represent all materials that may be issued during the term.

Our own documentation and code comments are written in English. Preserve source attribution and distinguish proposed ideas, experimental results, and formal guarantees.
