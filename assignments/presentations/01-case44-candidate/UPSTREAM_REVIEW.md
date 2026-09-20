# Preliminary publisher code review

Source: PacktPublishing/Machine-Learning-for-Finance, MIT license. Exact versions and hashes are in [sources.json](upstream/sources.json).

| File | Content | Status |
|---|---|---|
| `7.1 Q-Learning.ipynb` | Catch game, neural-network Q values, experience replay | Downloaded and read; original not executed |
| `7.2 A2C Balance.ipynb` | Actor-critic balancing task | Downloaded; not reproduced |
| `7.3 A2C Trading.ipynb` | Multi-asset trading environment and A2C | Downloaded; environment inspected; not reproduced |

Points to address:

- Chapter numbering in the publisher README differs from the instructor material and filenames. Identify the work using Case 44, the chapter title, and the specific notebook together.
- Although titled Q-Learning, `7.1` uses a Keras neural network. Our tabular version is a separate warm-up, not reproduction of the original training run.
- The original `7.1` ends with a standalone `£` code cell that causes a syntax error in Run All. Keep the original intact and record fixes in a working copy.
- The code uses old Keras imports and optimizer interfaces. The mixture of scalars and arrays in `Catch.reset` also needs checking against modern NumPy.
- The trading example reads local stock CSV files and expects 100 stock series. These data are not included in the three notebooks.
- The trading environment uses windows of historical returns and a rolling return/volatility ratio as reward. Review observable information, reward history, data splits, position semantics, and costs before defining the reproduction experiment.

This is a preliminary static inspection, not a complete audit or a report of resolved compatibility issues. Understand the model before choosing a pinned historical environment or a documented compatibility migration.
