# Warm-up experiment results

This is a tabular Catch toy experiment, not a financial-case reproduction or a completed graded submission.

| Policy | epsilon | Mean success rate across five seeds | Minimum–maximum |
|---|---:|---:|---|
| tabular_q | 0.0 | 1.000 | 1.000–1.000 |
| tabular_q | 0.2 | 1.000 | 1.000–1.000 |
| stay |  | 0.429 | 0.429–0.429 |
| random |  | 0.440 | 0.400–0.514 |

## Data and scope

- `results/training.csv`: rewards for all training episodes.
- `results/metrics.csv`: evaluation metrics by seed.
- `results/evaluation_*.csv`: complete evaluation trajectories for fixed policies.
- `results/run.json`: parameters and scope.

All data come from a simulated environment with fixed rules; no market data, paid APIs, or private material are used. Evaluation enumerates the support of initial states in the training environment; it is not a distribution-shift test. Finite transition checks cover all nonterminal states and actions on this grid, not a Lean proof or a proof for arbitrary grids.

The source Catch example and license are retained in `../upstream/`. Our changes include explicit states, a Q table, a smaller grid, fixed seeds, and evaluation records.
