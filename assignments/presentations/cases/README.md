# APS1053 case selection guide

**23 cases · 6 topics · One page for reading and navigation**

This guide organizes the instructor’s 28-slide case deck for direct reading on GitHub. Case numbers follow the original slides; gaps are intentional. This is not the complete list of all 69 course cases.

[Course home](../../../README.md) · [Presentation requirements](../REQUIREMENTS.md) · [Slide-by-slide extraction](../../../readings/library/documents/APS1053_CaseStudies_Reinforcement_GenerativeAI/index.md) · [Download original slides](../../../materials/02_Cases_and_Presentations/APS1053_CaseStudies_Reinforcement_GenerativeAI.pptx)

## How to use this guide

1. Compare cases by topic in the overview, then follow a case number for details.
2. Use the book and chapter references to locate the source text. This is a selection guide, not a complete textbook.
3. Record preferences in the [candidate list](../CASE_SELECTION.md). Candidate selection, warm-up work, and formal allocation are distinct stages.

**Instructor email guidance:** Submit five cases from this deck in preference order for allocation. The recommended slides 13–14 concern the same **Case 44**: slide 13 introduces the book and slide 14 the case. Hilpisch on slide 2 is an introductory RL reference. These instructions come from the selection email, not additional requirements inferred from the slides.

**Scope:** Explanations summarize the course material, and each entry retains the original English excerpt and slide link. Book titles, page numbers, and paper years follow the slides and have not been independently verified here. The guide does not presume that Q-learning must be selected or that financial-agent cases already include formal verification.

## Case overview

| Topic | Case | Content | Source / special designation | Slide |
|---|---|---|---|---|
| RL foundations | [Case 1](#case-1) | Learning through interaction | Book 1 · Chapter 1 · p.3 | 3 |
| RL foundations | [Case 2](#case-2) | Deep Q Learning | Book 1 · Chapter 2 · p.19 | 3 |
| RL foundations | [Case 3](#case-3) | Financial Q Learning | Book 1 · Chapter 3 · p.37 | 4 |
| RL foundations | [Case 44](#case-44) | Reinforcement Learning for Financial Markets | Book 6 · Chapter 7 · p.277 | 14 |
| Simulated and generated data | [Case 4](#case-4) | Simulated Data | Book 1 · Chapter 4 · p.51 | 5 |
| Simulated and generated data | [Case 5](#case-5) | Generated Data | Book 1 · Chapter 5 · p.67 | 6 |
| Financial decisions: trading, hedging, and allocation | [Case 6](#case-6) | Algorithmic Trading | Book 1 · Chapter 6 · p.85 | 7 |
| Financial decisions: trading, hedging, and allocation | [Case 7](#case-7) | Dynamic Hedging | Book 1 · Chapter 7 · p.105 | 8 |
| Financial decisions: trading, hedging, and allocation | [Case 8](#case-8) | Dynamic Asset Allocation | Book 1 · Chapter 8 · p.129 | 9 |
| Financial decisions: trading, hedging, and allocation | [Case 9](#case-9) | Optimal Execution | Book 1 · Chapter 9 · p.167 | 10 |
| Financial decisions: trading, hedging, and allocation | [Case 23](#case-23) | Reinforcement Learning-Based Trading Strategy | Book 2 · p.298 | 12 |
| Financial decisions: trading, hedging, and allocation | [Case 24](#case-24) | Derivatives Hedging | Book 2 · p.316 | 12 |
| Financial decisions: trading, hedging, and allocation | [Case 25](#case-25) | Portfolio Allocation | Book 2 · p.334 | 12 |
| Financial decisions: trading, hedging, and allocation | [Case 60](#case-60) | Deep Reinforcement Learning: Building a Trading Agent | Book 7 · Chapter 22 · p.679 | 16 |
| Generative AI and sequence models | [Case 61](#case-61) | Understanding Generative AI | Book 8 · Chapter 4 · Theoretical chapter | 18 |
| Generative AI and sequence models | [Case 62](#case-62) | Deep Autoregressive Models for Sequence Modeling | Book 8 · Chapter 5 · Theoretical chapter | 19 |
| Generative AI and sequence models | [Case 63](#case-63) | Leveraging LLMs for Sentiment Analysis in Trading | Book 8 · Chapter 9 · FINAL PROJECT CASE | 20 |
| Financial research: retrieval, graphs, and agents | [Case 64](#case-64) | RAG for Financial Research | Book 9 · Chapter 22 | 22 |
| Financial research: retrieval, graphs, and agents | [Case 65](#case-65) | Knowledge Graphs | Book 9 · Chapter 23 | 23 |
| Financial research: retrieval, graphs, and agents | [Case 66](#case-66) | Autonomous Agents | Book 9 · Chapter 24 | 24 |
| Papers and code projects | [Case 67](#case-67) | Time Series Specialized LLM for Stock Price Prediction | Wang et al. · 2024 (as listed in the slides) | 26 |
| Papers and code projects | [Case 68](#case-68) | Price-Driven Multi-Agent LLMs for High-Frequency Trading | Xiong et al. · 2025 (as listed in the slides) | 27 |
| Papers and code projects | [Case 69](#case-69) | Foundation Model for the Language of Financial Markets | Shi et al. · 2025 (as listed in the slides) | 28 |

## Case details

### RL foundations

<a id="case-1"></a>

#### Case 1 · Learning through interaction

**Learning through interaction**

**Source: **[Book 1](#book-1) · Chapter 1 · p.3 · [Slide 3](../../../readings/library/documents/APS1053_CaseStudies_Reinforcement_GenerativeAI/index.md#slide-3)

Introduces learning through interaction using probability matching, Bayesian updating, reinforcement learning (RL), and deep Q-learning (DQL).

<details>
<summary>Expand original slide text</summary>

Case Study 1: Chapter 1: Learning through interaction [p.3]: The first chapter focuses on learning through interaction with four major examples: probability matching, Bayesian updating, RL, and DQL.

</details>

[Back to case overview](#case-overview)

<a id="case-2"></a>

#### Case 2 · Deep Q Learning

**Deep Q Learning**

**Source: **[Book 1](#book-1) · Chapter 2 · p.19 · [Slide 3](../../../readings/library/documents/APS1053_CaseStudies_Reinforcement_GenerativeAI/index.md#slide-3)

Starts from dynamic programming (DP) and introduces DQL as an approximate solution method. Policies improve through sequences of actions and iterative updates. A DQL agent playing Gymnasium’s CartPole illustrates the method.

<details>
<summary>Expand original slide text</summary>

Case Study 2: Chapter 2: Deep Q Learning [p.19]: The second chapter introduces concepts from dynamic programming (DP) and discusses DQL as an approach to approximate solutions to DP problems. The major theme is the derivation of optimal policies to maximize a given objective function through taking a sequence of actions and updating the optimal policy iteratively. DQL is illustrated on the basis of a DQL agent that learns to play the CartPole game from the Gymnasium Python package.

</details>

[Back to case overview](#case-overview)

<a id="case-3"></a>

#### Case 3 · Financial Q Learning

**Financial Q Learning**

**Source: **[Book 1](#book-1) · Chapter 3 · p.37 · [Slide 4](../../../readings/library/documents/APS1053_CaseStudies_Reinforcement_GenerativeAI/index.md#slide-4)

Builds a financial prediction environment for the DQL agent from Chapter 2. The slides note that reproducing the CartPole API does not supply all the characteristics needed to apply RL successfully.

<details>
<summary>Expand original slide text</summary>

Case Study 3: Chapter 3: Financial Q Learning [p.37]: The third chapter develops a first Finance environment that allows the DQL agent from Chapter 2 to learn a financial prediction game. Although the environment formally replicates the API of the CartPole game, it misses some important characteristics that are needed to apply RL successfully.

</details>

[Back to case overview](#case-overview)

<a id="case-44"></a>

#### Case 44 · Reinforcement Learning for Financial Markets

**Reinforcement Learning for Financial Markets**

**Source: **[Book 6](#book-6) · Chapter 7 · p.277 · [Slide 14](../../../readings/library/documents/APS1053_CaseStudies_Reinforcement_GenerativeAI/index.md#slide-14)

Introduces RL concepts and algorithms, including Q-learning and actor-critic methods, and relates them to economic theory. Examples cover trading, portfolio construction, and sequential decisions under uncertainty.

**Selection status:** Suggested by the instructor. The Q-learning experiment in the [preparation workspace](../01-case44-candidate/README.md) is optional warm-up work; the presentation scope is not confirmed and the original case has not been reproduced.

<details>
<summary>Expand original slide text</summary>

Case 44 Chapter 7 [p.277]  – Reinforcement Learning for Financial Markets

Presents reinforcement learning concepts and algorithms (Q-learning, actor-critic methods) and connects them to economic theory. Practical examples illustrate how RL can be applied to trading, portfolio construction, and sequential decision-making under uncertainty.

</details>

[Back to case overview](#case-overview)

### Simulated and generated data

<a id="case-4"></a>

#### Case 4 · Simulated Data

**Simulated Data**

**Source: **[Book 1](#book-1) · Chapter 4 · p.51 · [Slide 5](../../../readings/library/documents/APS1053_CaseStudies_Reinforcement_GenerativeAI/index.md#slide-5)

Uses Monte Carlo simulation for data augmentation, including adding noise to historical data and simulating stochastic processes.

<details>
<summary>Expand original slide text</summary>

DATA AUGMENTATION:

Case Study 4: Chapter 4: Simulated Data [p.51]: The fourth chapter is about data augmentation based on Monte Carlo simulation (MCS) approaches, and it discusses the addition of noise to historical data and the simulation of stochastic processes.

</details>

[Back to case overview](#case-overview)

<a id="case-5"></a>

#### Case 5 · Generated Data

**Generated Data**

**Source: **[Book 1](#book-1) · Chapter 5 · p.67 · [Slide 6](../../../readings/library/documents/APS1053_CaseStudies_Reinforcement_GenerativeAI/index.md#slide-6)

Uses generative adversarial networks (GANs) to generate financial time series with statistical characteristics resembling the historical training data.

<details>
<summary>Expand original slide text</summary>

Case Study 5: Chapter 5: Generated Data [p.67]: The fifth chapter introduces generative adversarial networks (GANs) to synthetically generate time series data that has statistical characteristics that are similar to those of historical time series data on which a GAN was trained.

</details>

[Back to case overview](#case-overview)

### Financial decisions: trading, hedging, and allocation

<a id="case-6"></a>

#### Case 6 · Algorithmic Trading

**Algorithmic Trading**

**Source: **[Book 1](#book-1) · Chapter 6 · p.85 · [Slide 7](../../../readings/library/documents/APS1053_CaseStudies_Reinforcement_GenerativeAI/index.md#slide-7)

Extends Case 3 to algorithmic trading by using DQL to predict the direction of the next price movement.

<details>
<summary>Expand original slide text</summary>

FINANCIAL APPLICATIONS:

Case Study 6: Chapter 6: Algorithmic Trading [p.85]: Building on the example from Chapter 3, this chapter applies DQL to the problem of algorithmic trading based on the prediction of the next price movement’s direction.

</details>

[Back to case overview](#case-overview)

<a id="case-7"></a>

#### Case 7 · Dynamic Hedging

**Dynamic Hedging**

**Source: **[Book 1](#book-1) · Chapter 7 · p.105 · [Slide 8](../../../readings/library/documents/APS1053_CaseStudies_Reinforcement_GenerativeAI/index.md#slide-8)

Learns dynamic hedging strategies for European options under the Black–Scholes–Merton (1973) model, aiming at delta hedging or dynamic option replication.

<details>
<summary>Expand original slide text</summary>

Case Study 7: Chapter 7: Dynamic Hedging [p.105]: The seventh chapter is about learning optimal dynamic hedging strategies for an option with European exercise in the Black-Scholes-Merton (1973) model. In other words, delta hedging or dynamic replication of the option is the goal.

</details>

[Back to case overview](#case-overview)

<a id="case-8"></a>

#### Case 8 · Dynamic Asset Allocation

**Dynamic Asset Allocation**

**Source: **[Book 1](#book-1) · Chapter 8 · p.129 · [Slide 9](../../../readings/library/documents/APS1053_CaseStudies_Reinforcement_GenerativeAI/index.md#slide-9)

Applies DQL to three allocation settings: one risky and one risk-free asset, two risky assets, and three risky assets. Funds are allocated dynamically to maximize a profit target or risk-adjusted return measured by the Sharpe ratio.

<details>
<summary>Expand original slide text</summary>

Case Study 8: Chapter 8: Dynamic Asset Allocation [p.129]: This chapter applies DQL to three canonical examples in asset management: one risky asset and one risk-free asset, two risky assets, and three risky assets. The problem is to dynamically allocate funds to the available assets to maximize a profit target or a risk-adjusted return (Sharpe ratio).

</details>

[Back to case overview](#case-overview)

<a id="case-9"></a>

#### Case 9 · Optimal Execution

**Optimal Execution**

**Source: **[Book 1](#book-1) · Chapter 9 · p.167 · [Slide 10](../../../readings/library/documents/APS1053_CaseStudies_Reinforcement_GenerativeAI/index.md#slide-10)

Minimizes total execution costs when liquidating a large stock position under a given risk aversion. Actions are linked by an additional constraint, and the chapter introduces an actor-critic implementation.

<details>
<summary>Expand original slide text</summary>

Case Study 9: Chapter 9: Optimal Execution [p.167]: The ninth chapter is about the optimal liquidation of a large position in a stock. Given a certain risk aversion, the total execution costs are to be minimized. This use case differs from the others in that all actions are tightly connected with each other through an additional constraint. The chapter also introduces an additional RL algorithm in the form of an actor-critic implementation.

</details>

[Back to case overview](#case-overview)

<a id="case-23"></a>

#### Case 23 · Reinforcement Learning-Based Trading Strategy

**Reinforcement Learning–Based Trading Strategy**

**Source: **[Book 2](#book-2) · p.298 · [Slide 12](../../../readings/library/documents/APS1053_CaseStudies_Reinforcement_GenerativeAI/index.md#slide-12)

An implementation blueprint for an RL-based trading strategy.

<details>
<summary>Expand original slide text</summary>

Case Study 23: Reinforcement Learning–Based Trading Strategy [p.298]:

Blueprint for Creating a Reinforcement Learning–Based Trading Strategy

</details>

[Back to case overview](#case-overview)

<a id="case-24"></a>

#### Case 24 · Derivatives Hedging

**Derivatives Hedging**

**Source: **[Book 2](#book-2) · p.316 · [Slide 12](../../../readings/library/documents/APS1053_CaseStudies_Reinforcement_GenerativeAI/index.md#slide-12)

Implements an RL-based hedging strategy. The slides also refer to Part III of Benninga in the Nyholm minicourse.

<details>
<summary>Expand original slide text</summary>

Case Study 24: Derivatives Hedging  [p.316]:

Blueprint for Implementing a Reinforcement Learning–Based Hedging Strategy  (See Part III of Benninga in Nyholm minicourse).

</details>

[Back to case overview](#case-overview)

<a id="case-25"></a>

#### Case 25 · Portfolio Allocation

**Portfolio Allocation**

**Source: **[Book 2](#book-2) · p.334 · [Slide 12](../../../readings/library/documents/APS1053_CaseStudies_Reinforcement_GenerativeAI/index.md#slide-12)

Implements RL-based portfolio allocation. The slides also refer to Part II of Benninga in the Nyholm minicourse.

<details>
<summary>Expand original slide text</summary>

Case Study 25: Portfolio Allocation [p.334]

Blueprint for Implementing a Reinforcement Learning–Based Portfolio Allocation (See Part II of Benninga in Nyholm minicourse)

</details>

[Back to case overview](#case-overview)

<a id="case-60"></a>

#### Case 60 · Deep Reinforcement Learning: Building a Trading Agent

**Deep Reinforcement Learning – Building a Trading Agent**

**Source: **[Book 7](#book-7) · Chapter 22 · p.679 · [Slide 16](../../../readings/library/documents/APS1053_CaseStudies_Reinforcement_GenerativeAI/index.md#slide-16)

Explains how to design and train agents that improve decisions through environmental interaction, create a custom trading environment, and build an agent responding to market signals using OpenAI Gym.

<details>
<summary>Expand original slide text</summary>

Case 60 Chapter 22, Deep Reinforcement Learning – Building a Trading Agent [p.679], presents how reinforcement learning (RL) permits the design and training of agents that learn to optimize decisions over time in response to their environment. You will see how to create a custom trading environment and build an agent that responds to market signals using OpenAI Gym.

</details>

[Back to case overview](#case-overview)

### Generative AI and sequence models

<a id="case-61"></a>

#### Case 61 · Understanding Generative AI

**Understanding Generative AI**

**Source: **[Book 8](#book-8) · Chapter 4 · Theoretical chapter · [Slide 18](../../../readings/library/documents/APS1053_CaseStudies_Reinforcement_GenerativeAI/index.md#slide-18)

Covers the motivation for generative models, their distinction from discriminative models, density estimation, new data and representations, language modeling, sampling, conditional generation, representation learning with ChatGPT, hybrid modeling, and a taxonomy of generative models.

**Slide designation:** THEORETICAL CHAPTER. Confirm how code and experiment deliverables apply if selecting this case.

<details>
<summary>Expand original slide text</summary>

Case 61 Ch. 4 — Understanding Generative AI  (THEORETICAL CHAPTER)

Why Generative Models, Difference with Discriminative Models, Probability Density Estimation, Generating New Data, Learning New Data Representations, Language Modeling, Sampling, Conditional Language Generation, Representation Learning with ChatGPT, Hybrid Modeling: Combining Generative and Discriminative Models, Taxonomy of Generative Models

</details>

[Back to case overview](#case-overview)

<a id="case-62"></a>

#### Case 62 · Deep Autoregressive Models for Sequence Modeling

**Deep Autoregressive Models for Sequence Modeling**

**Source: **[Book 8](#book-8) · Chapter 5 · Theoretical chapter · [Slide 19](../../../readings/library/documents/APS1053_CaseStudies_Reinforcement_GenerativeAI/index.md#slide-19)

Covers logistic regression/FVSN, MADE, causal masked networks/WaveNet, RNNs, Transformers (attention, positional encoding, multi-head attention, and encoders), and time-series Transformers such as Chronos and Lag-Llama.

**Slide designation:** THEORETICAL CHAPTER. Confirm how code and experiment deliverables apply if selecting this case.

<details>
<summary>Expand original slide text</summary>

Case 62  Ch. 5 — Deep Autoregressive Models for Sequence Modeling (THEORETICAL CHAPTER)

Logistic regression/FVSN, MADE, causal masked networks/WaveNet, RNNs, Transformers (attention, positional encoding, multi-head attention, encoder), time-series transformers (Chronos, Lag-Llama)

</details>

[Back to case overview](#case-overview)

<a id="case-63"></a>

#### Case 63 · Leveraging LLMs for Sentiment Analysis in Trading

**Leveraging LLMs for Sentiment Analysis in Trading**

**Source: **[Book 8](#book-8) · Chapter 9 · FINAL PROJECT CASE · [Slide 20](../../../readings/library/documents/APS1053_CaseStudies_Reinforcement_GenerativeAI/index.md#slide-20)

Analyzes sentiment in Federal Reserve press-conference speeches using video and market-price data, speech-to-text conversion, sentiment analysis, and experimental results. The deck specifically designates it as a final-project case.

**Slide designation:** FINAL PROJECT CASE. Do not assume it counts as one of the two regular presentations; follow the delivery route confirmed by the instructor.

<details>
<summary>Expand original slide text</summary>

Case 63 Ch. 9 — Leveraging LLMs for Sentiment Analysis in Trading (FINAL PROJECT CASE)

Sentiment Analysis in Fed Press Conference Speeches Using Large Language Models; Data: Video+Market Prices, Speech-to-text Conversion, Sentiment Analysis, Experiment Results

</details>

[Back to case overview](#case-overview)

### Financial research: retrieval, graphs, and agents

<a id="case-64"></a>

#### Case 64 · RAG for Financial Research

**RAG for Financial Research**

**Source: **[Book 9](#book-9) · Chapter 22 · [Slide 22](../../../readings/library/documents/APS1053_CaseStudies_Reinforcement_GenerativeAI/index.md#slide-22)

Builds RAG grounded in SEC filings, covering ingestion, domain embeddings, hybrid retrieval, evaluation, and a transition to agentic workflows.

<details>
<summary>Expand original slide text</summary>

Case 64  Ch. 22 — RAG for Financial Research

Builds retrieval-augmented generation grounded in SEC filings, from ingestion and domain embeddings through hybrid retrieval, evaluation, and the transition to agentic workflows.

</details>

[Back to case overview](#case-overview)

<a id="case-65"></a>

#### Case 65 · Knowledge Graphs

**Knowledge Graphs**

**Source: **[Book 9](#book-9) · Chapter 23 · [Slide 23](../../../readings/library/documents/APS1053_CaseStudies_Reinforcement_GenerativeAI/index.md#slide-23)

Constructs knowledge graphs from filings, uses Graph RAG for multi-hop reasoning, creates graph features for machine learning, and addresses temporal information leakage.

<details>
<summary>Expand original slide text</summary>

Case 65  Ch. 23 — Knowledge Graphs

Covers KG construction from filings, Graph RAG for multi-hop reasoning, graph features for ML, and temporal-leakage prevention

</details>

[Back to case overview](#case-overview)

<a id="case-66"></a>

#### Case 66 · Autonomous Agents

**Autonomous Agents**

**Source: **[Book 9](#book-9) · Chapter 24 · [Slide 24](../../../readings/library/documents/APS1053_CaseStudies_Reinforcement_GenerativeAI/index.md#slide-24)

Covers agent architectures, memory, tools, and the engineering stack, including a stateful equity-research agent and multi-agent forecasting with adversarial debate.

<details>
<summary>Expand original slide text</summary>

Case 66  Ch. 24 — Autonomous Agents

 Covers agent architectures, memory and tools, the engineering stack, a stateful equity-research agent, and multi-agent forecasting with adversarial debate.

</details>

[Back to case overview](#case-overview)

### Papers and code projects

<a id="case-67"></a>

#### Case 67 · Time Series Specialized LLM for Stock Price Prediction

**StockTime**

**Source: **Wang et al. · 2024 (as listed in the slides) · [Slide 26](../../../readings/library/documents/APS1053_CaseStudies_Reinforcement_GenerativeAI/index.md#slide-26)

The deck gives the title StockTime: A Time Series Specialized Large Language Model Architecture for Stock Price Prediction. Its arXiv address is truncated to https://arxiv.org/abs/2409, so the slide link alone does not identify the paper completely.

<details>
<summary>Expand original slide text</summary>

Case 67 GITHUB:

StockTime: A Time Series Specialized Large Language Model Architecture for Stock Price Prediction (Wang et al., 2024-- https://arxiv.org/abs/2409

</details>

[Back to case overview](#case-overview)

<a id="case-68"></a>

#### Case 68 · Price-Driven Multi-Agent LLMs for High-Frequency Trading

**QuantHarness**

**Source: **Xiong et al. · 2025 (as listed in the slides) · [Slide 27](../../../readings/library/documents/APS1053_CaseStudies_Reinforcement_GenerativeAI/index.md#slide-27)

The deck gives the title QuantHarness: Price-Driven Multi-Agent LLMs for High-Frequency Trading and an arXiv link. The correspondence between title, authors, and link has not been verified in this guide.

[arXiv link listed in the slides](https://arxiv.org/abs/2509.09995) (not verified).

<details>
<summary>Expand original slide text</summary>

Case 68 GITHUB:

QuantHarness: Price-Driven Multi-Agent LLMs for High-Frequency Trading  (Xiong et al., 2025— https://arxiv.org/abs/2509.09995 )

</details>

[Back to case overview](#case-overview)

<a id="case-69"></a>

#### Case 69 · Foundation Model for the Language of Financial Markets

**Kronos**

**Source: **Shi et al. · 2025 (as listed in the slides) · [Slide 28](../../../readings/library/documents/APS1053_CaseStudies_Reinforcement_GenerativeAI/index.md#slide-28)

The slides describe Japanese candlestick patterns as phrase-like components and link to the Kronos repository and an Investing.com candlestick example.

[GitHub repository listed in the slides](https://github.com/shiyu-coder/Kronos) · [Candlestick example listed in the slides](https://ca.investing.com/indices/s-p-tsx-composite-candlestick).

<details>
<summary>Expand original slide text</summary>

Case 69 GITHUB:

Kronos: A Foundation Model for the Language of Financial Markets (Shi et al., 2025 — https://github.com/shiyu-coder/Kronos )

Analyzes prices in terms of Japanese candle stick patterns which are “phrase like” components:

e.g. https://ca.investing.com/indices/s-p-tsx-composite-candlestick

</details>

[Back to case overview](#case-overview)

## Books and reading links

Book numbers follow the slides. These are the access links listed on the original pages; university resources may require a UofT login. Link availability and bibliographic matches have not been verified here.

<a id="book-1"></a>

### Book 1 · Hilpisch — Reinforcement Learning for Finance

Cases: [Case 1](#case-1) · [Case 2](#case-2) · [Case 3](#case-3) · [Case 4](#case-4) · [Case 5](#case-5) · [Case 6](#case-6) · [Case 7](#case-7) · [Case 8](#case-8) · [Case 9](#case-9).

- [UofT library](https://librarysearch.library.utoronto.ca/permalink/01UTORONTO_INST/1dl2m71/alma991107425685806196)
- [Original book reference: slide 2](../../../readings/library/documents/APS1053_CaseStudies_Reinforcement_GenerativeAI/index.md#slide-2)

<a id="book-2"></a>

### Book 2 · Tatsat — Machine Learning Blueprints for Finance

Cases: [Case 23](#case-23) · [Case 24](#case-24) · [Case 25](#case-25).

- [UofT library](https://librarysearch.library.utoronto.ca/permalink/01UTORONTO_INST/14bjeso/alma991107061413606196)
- [Original book reference: slide 11](../../../readings/library/documents/APS1053_CaseStudies_Reinforcement_GenerativeAI/index.md#slide-11)

<a id="book-6"></a>

### Book 6 · Klaas — Machine Learning for Finance

Cases: [Case 44](#case-44).

- [UofT library](https://librarysearch.library.utoronto.ca/permalink/01UTORONTO_INST/10oudkq/cdi_walterdegruyter_books_10_0000_9781789134698_001)
- [Original book reference: slide 13](../../../readings/library/documents/APS1053_CaseStudies_Reinforcement_GenerativeAI/index.md#slide-13)

<a id="book-7"></a>

### Book 7 · Jansen — Machine Learning for Algorithmic Trading, 2nd edition

Cases: [Case 60](#case-60).

- [UofT library](https://librarysearch.library.utoronto.ca/permalink/01UTORONTO_INST/1dl2m71/alma991107212149706196)
- [Original book reference: slide 15](../../../readings/library/documents/APS1053_CaseStudies_Reinforcement_GenerativeAI/index.md#slide-15)

<a id="book-8"></a>

### Book 8 · Generative AI for Trading and Asset Management (credited in the slides to Jesse Hamlet, 2025)

Cases: [Case 61](#case-61) · [Case 62](#case-62) · [Case 63](#case-63).

- [UofT library](https://librarysearch.library.utoronto.ca/permalink/01UTORONTO_INST/1dl2m71/alma991107753593906196)
- [Original book reference: slide 17](../../../readings/library/documents/APS1053_CaseStudies_Reinforcement_GenerativeAI/index.md#slide-17)

<a id="book-9"></a>

### Book 9 · Stefan Jansen — Machine Learning for Trading, 3rd edition (2026 as listed in the slides)

Cases: [Case 64](#case-64) · [Case 65](#case-65) · [Case 66](#case-66).

- [O’Reilly access through UofT](https://learning.oreilly.com/library/view/machine-learning-for/9781803246970/?sso_link=yes&sso_link_from=utoronto-edu)
- [UofT library](https://librarysearch.library.utoronto.ca/permalink/01UTORONTO_INST/10oudkq/cdi_walterdegruyter_books_10_0000_9781789342710_001)
- [Original book reference: slide 21](../../../readings/library/documents/APS1053_CaseStudies_Reinforcement_GenerativeAI/index.md#slide-21)

## Coverage of the original deck

- Slide 1 is the title; slide 25 introduces the OTHER (GITHUB) category.
- Slides 2, 11, 13, 15, 17, and 21 are book references collected above.
- All 23 cases from the remaining slides appear in the overview and details, with source descriptions in expandable sections.
- The original Case 67 paper link is incomplete. This guide records the issue without guessing a replacement.
- Personal selection advice and subsequent experiments belong in their respective workspaces, separate from instructor case descriptions.

Source: APS1053_CaseStudies_Reinforcement_GenerativeAI.pptx, version received on 2026-09-18. Attribution and rights remain with the original authors; this is a student reading guide.
