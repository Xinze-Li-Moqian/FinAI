# Reinforcement learning and preference optimization

Learning note, 2026-09-18. The names below describe different methods and should not be treated as interchangeable.

| Method | Core idea | Primary source |
|---|---|---|
| PPO: Proximal Policy Optimization | Policy-gradient RL with updates constrained through a surrogate objective | [Paper](https://arxiv.org/abs/1707.06347) |
| GRPO: Group Relative Policy Optimization | Uses relative rewards within a group of sampled answers to estimate advantages, avoiding a separately trained value model in the original formulation | [DeepSeekMath](https://arxiv.org/abs/2402.03300) |
| DPO: Direct Preference Optimization | Directly optimizes preferred/dispreferred response pairs; the original offline method does not use a conventional online RL loop | [Paper](https://arxiv.org/abs/2305.18290) |
| GraphGPO: Graph-based Group Policy Optimization | Combines rollouts into a state-transition graph to estimate step-level credit | [Paper](https://arxiv.org/abs/2605.26684) |

GPO is ambiguous: it can refer to different preference or policy optimization methods. Record the full name and source rather than guessing from the acronym.

## Concepts to understand first

1. Policy: how actions are selected from observations or states.
2. Reward: what performance signal is optimized and how it is obtained.
3. Credit assignment: which actions contributed to an outcome.
4. Learning update: how data changes the policy.
5. Constraints: which actions or state transitions are permitted regardless of reward.

The group in GRPO is a group of sampled outputs, not necessarily multiple collaborating agents. Multi-agent coordination can occur without any model training.

## Connection to formal verification

A reward encouraging budget compliance is not a proof that overspending cannot happen. A possible architecture combines a learned allocation policy with a verified execution layer. Its guarantees depend on the model, assumptions, and correspondence to the deployed implementation.

Open question: which decisions benefit from learning, and which rules should remain explicit and mechanically checked?
