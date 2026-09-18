# FinAI

Learning notes and research questions on financial modelling, reinforcement learning, formal verification, and resource allocation for AI agents.

## Research question

How can collaborative AI systems allocate compute and complete verification tasks efficiently, while preserving explicit guarantees about budgets, authorization, and settlement?

This repository records learning and exploratory work. Proposed mechanisms are not established results, and no improvement in allocation efficiency is claimed without evaluation.

## Contents

- [Course overview](courses/README.md): APS1050, APS1053, and Mathematics for AI Safety.
- [APS1053 study notes](courses/APS1053/notes.md): course tasks, case selection, and reading priorities.
- [Material coverage](materials/COVERAGE.md): received packages and outstanding material.
- [Course material index](materials/INDEX.md): descriptions and local links to original attachments.
- [RL and preference optimization](reading/rl-and-preference-optimization.md): PPO, GRPO, DPO, and GraphGPO.
- [Research questions](questions/research-directions.md): allocation, incentives, and verifiable constraints.
- [Experiments](experiments/README.md): proposed small experiments.
- [Discussions](discussions/README.md): space for shareable discussion notes.

## Local materials

Original course attachments are stored under `local-materials/APS1053_Fall2026/` and excluded from Git. They include instructor documents, slides, reference books, assignment code, transcript datasets, and original archives. The material index works locally; its attachment links will not resolve on GitHub or in a fresh clone without the attachments.

Only study notes and the material index are published. Private correspondence, registration details, travel plans, and non-public employer materials are not included.

## Working method

For each reading, record the problem, assumptions, main mechanism, remaining questions, and relevance to the research question. Keep formal guarantees separate from empirical performance, and proposals separate from implemented or evaluated results.

LeanSwap implementation remains in its own repository. FinAI is for the underlying learning, models, and research questions.
