# FinAI

Learning notes and research questions on financial modelling, reinforcement learning, formal verification, and resource allocation for AI agents.

## Research question

How can collaborative AI systems allocate compute and complete verification tasks efficiently, while preserving explicit guarantees about budgets, authorization, and settlement?

This repository records learning and exploratory work. Proposed mechanisms are not established results, and no improvement in allocation efficiency is claimed without evaluation.

## Contents

- **[APS1053 案例选题指南：23 个案例的 Markdown 阅读版](courses/APS1053/cases/README.md)** — 中文总览、英文原文、书目与原始页码。

- [Course overview](courses/README.md): APS1050, APS1053, and Mathematics for AI Safety.
- [APS1053 presentation workspace](courses/APS1053/presentations/README.md): requirements, candidate Case 44, upstream notebooks, and an executed tabular-RL warm-up.
- [APS1053 study notes](courses/APS1053/notes.md): course tasks, case selection, and reading priorities.
- [Material coverage](materials/COVERAGE.md): received packages and outstanding material.
- [Course material index](materials/INDEX.md): descriptions and local links to original attachments.
- [RL and preference optimization](reading/rl-and-preference-optimization.md): PPO, GRPO, DPO, and GraphGPO.
- [Research questions](questions/research-directions.md): allocation, incentives, and verifiable constraints.
- [Experiments](experiments/README.md): proposed small experiments.
- [Discussions](discussions/README.md): space for shareable discussion notes.

## Course materials — browse and download

- **[Read the course material in Markdown](knowledge/APS1053/README.md)**
- **[Browse all received attachments](materials/APS1053/README.md)**: Word, PowerPoint, reference books, Python/Notebook files, prompts, transcripts and sample outputs.
- **[Download the attachment packages](https://github.com/Xinze-Li-Moqian/FinAI/releases/tag/course-materials-2026-09-18)**

These files are uploaded to this repository and its GitHub Release. The original local backup remains separate. Credentials, personal correspondence and administrative records are excluded; a sanitized ZIP replaces the archive containing a credential. Instructor materials retain their attribution and are not presented as original work by this repository's owner. Third-party rights are unchanged.

Coverage is limited to materials received so far; see [coverage](materials/COVERAGE.md). Conversion and static inspection do not establish correctness or reproducibility.

## Working method

For each reading, record the problem, assumptions, main mechanism, remaining questions, and relevance to the research question. Keep formal guarantees separate from empirical performance, and proposals separate from implemented or evaluated results.

LeanSwap implementation remains in its own repository. FinAI is for the underlying learning, models, and research questions.
