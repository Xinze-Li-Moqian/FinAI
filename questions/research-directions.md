# Research questions

These are exploratory questions, not completed results or agreed collaborations.

## Allocation

- How should a fixed compute budget be distributed across proof or software-verification tasks?
- What information predicts marginal progress, and how should uncertainty be represented?
- When is a heuristic or optimization model sufficient, and when is reinforcement learning useful?

## Incentives and contributions

- How should useful intermediate results be credited when the overall task is unfinished?
- How can contribution rewards avoid encouraging duplication, artificial task splitting, or collusion?
- What role could forecasts of milestone completion play in allocation?

A prediction estimates an uncertain event; a verifier checks a stated obligation; a settlement rule distributes funds. These functions need distinct specifications.

## Global invariants

Possible properties to specify include conservation of accounted funds, budget bounds, authorization, and prevention of duplicate settlement. Clarify assumptions about verifiers, metering, service quality, and blockchain execution.

Improving allocation efficiency is an empirical objective. Preserving an invariant is a formal claim within an explicit model. Neither establishes the other automatically.

## Context and possible applications

- [Prove2Me](https://prove2.me/about): collaborative mathematical formalization.
- [Prove2Me paper](https://arxiv.org/abs/2608.28433): platform design and agent collaboration.
- [Justin Sun Prize](https://www.hejustinsun.com/prize): mathematical bounty initiative.
- Crowdsourced software verification and AI service marketplaces.

LeanSwap is a related implementation direction. Keep its design status, measured results, and verified properties explicit in its own repository.
