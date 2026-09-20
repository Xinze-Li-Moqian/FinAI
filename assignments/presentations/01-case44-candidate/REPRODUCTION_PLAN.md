# Formal case reproduction and small experiment

## Preparation

- [x] Check instructor requirements and the source of Case 44.
- [x] Pin publisher notebook versions, licenses, and hashes.
- [x] Complete a tabular Q-learning warm-up and exploration-rate comparison.
- [ ] Obtain instructor confirmation of case allocation.
- [ ] Decide which of the three original notebooks must be covered.

## Remaining financial-case work

- [ ] Explain the trading environment, actor, critic, reward, and learning updates step by step.
- [ ] Locate the original data source and license; select shareable fresh data or a subset of the original.
- [ ] Record the sample, dates, missing-value handling, and chronological splits.
- [ ] Define the dependency environment; fix compatibility in a working copy and record changes.
- [ ] Run the original baseline and save data, notebook outputs, configuration, and metrics.
- [ ] Complete one controlled extension; the toy warm-up cannot substitute for it.

## Candidate extension: from rewards to action constraints

First establish whether actions represent weights, positions, or another quantity, and clarify normalization and leverage. Choose a specific constraint, such as a gross-exposure limit, and compare original actions with checked or projected actions. Report returns, risk, turnover, and the fraction of modified actions using the same data splits, budget, and multiple seeds.

This is an unvalidated experimental proposal. Projection changes executed actions and must be handled consistently during training and evaluation. Backtesting or correcting outputs alone does not prove that the learning algorithm is safe.

If the original model semantics or data are unsuitable, use a smaller transaction-cost sensitivity experiment. Fix one research question before implementation rather than changing rewards, data, and algorithms simultaneously.

## Discussion extension

Possible topics include reward penalties versus execution constraints, statistical risk measures versus program invariants, and which assumptions survive a transfer from financial agents to token allocation. Use several slides to present evidence, examples, and limitations.
