# First presentation candidate: Case 44 — Reinforcement Learning for Financial Markets

Stage: candidate / warm-up. Instructor allocation, financial-case reproduction, and the course presentation are not complete.

## Start here

1. Open the [tabular Q-learning warm-up notebook](warmup/00_tabular_q_learning.ipynb) to study states, actions, rewards, the Q table, and updates.
2. Read the [results and limitations](warmup/RESULTS.md). These concern a toy Catch environment, not financial performance.
3. Compare the [publisher code review](UPSTREAM_REVIEW.md) with the [original notebooks](upstream/).
4. Follow the [formal reproduction plan](REPRODUCTION_PLAN.md) to prepare data and the A2C trading implementation.
5. Use the [presentation outline](../PRESENTATION_TEMPLATE.md) to develop the explanation.

## Files

- `upstream/`: three publisher notebooks with a pinned commit and SHA-256 hashes; MIT license retained. Originals have not been executed or modified.
- `warmup/`: a simplified experiment without neural networks, using only the Python standard library, with generated data, metrics, and trajectories.
- `REPRODUCTION_PLAN.md`: formal reproduction and extension tasks.
- `talk-notes.md`: questions to be able to explain independently.

## Run the warm-up

From this directory:

```sh
python3 warmup/tabular_catch.py
```

Outputs go to `warmup/results/`. No GPU, API key, or paid call is needed. The notebook uses the same module; change to `warmup/` when using Jupyter. Each code cell was executed through Python and outputs were saved, but interactive use in the Jupyter frontend has not been tested.
