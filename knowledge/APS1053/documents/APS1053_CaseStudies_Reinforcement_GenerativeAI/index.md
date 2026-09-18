# APS1053_CaseStudies_Reinforcement_GenerativeAI

**[阅读重新组织的案例指南：中文总览、23 个案例与书目](../../../../courses/APS1053/cases/README.md)**

下面保留逐页提取稿，便于与原 PPT 对照。

原文件：[打开原稿](<../../../../materials/APS1053/02_Cases_and_Presentations/APS1053_CaseStudies_Reinforcement_GenerativeAI.pptx>)

自动整理的阅读副本，保留作者内容，不代表已校正其论证或技术主张。原稿是版式依据。

> 按幻灯片编号提取文字与内嵌图片。形状位置、连接线、动画和部分图表不在此副本中重建；需要查看图示时请对照原 PPT。

## Slide 1

CASES TO SELECT FROM TO PRESENT IN APS1053

Reinforcement Learning

Generative AI

1

## Slide 2

Reinforcement Learning Cases

BOOK 1:  Reinforcement Learning for Finance by Hilpisch: UofT:

https://librarysearch.library.utoronto.ca/permalink/01UTORONTO_INST/1dl2m71/alma991107425685806196 

2

原页链接：<https://librarysearch.library.utoronto.ca/permalink/01UTORONTO_INST/1dl2m71/alma991107425685806196>

## Slide 3

Reinforcement Learning Cases

THE BASICS:

Case Study 1: Chapter 1: Learning through interaction [p.3]: The first chapter focuses on learning through interaction with four major examples: probability matching, Bayesian updating, RL, and DQL.

Case Study 2: Chapter 2: Deep Q Learning [p.19]: The second chapter introduces concepts from dynamic programming (DP) and discusses DQL as an approach to approximate solutions to DP problems. The major theme is the derivation of optimal policies to maximize a given objective function through taking a sequence of actions and updating the optimal policy iteratively. DQL is illustrated on the basis of a DQL agent that learns to play the CartPole game from the Gymnasium Python package.

3

## Slide 4

Reinforcement Learning Cases

Case Study 3: Chapter 3: Financial Q Learning [p.37]: The third chapter develops a first Finance environment that allows the DQL agent from Chapter 2 to learn a financial prediction game. Although the environment formally replicates the API of the CartPole game, it misses some important characteristics that are needed to apply RL successfully.

4

## Slide 5

Reinforcement Learning Cases

DATA AUGMENTATION:

Case Study 4: Chapter 4: Simulated Data [p.51]: The fourth chapter is about data augmentation based on Monte Carlo simulation (MCS) approaches, and it discusses the addition of noise to historical data and the simulation of stochastic processes.

5

## Slide 6

Reinforcement Learning Cases

Case Study 5: Chapter 5: Generated Data [p.67]: The fifth chapter introduces generative adversarial networks (GANs) to synthetically generate time series data that has statistical characteristics that are similar to those of historical time series data on which a GAN was trained.

6

## Slide 7

Reinforcement Learning Cases

FINANCIAL APPLICATIONS:

Case Study 6: Chapter 6: Algorithmic Trading [p.85]: Building on the example from Chapter 3, this chapter applies DQL to the problem of algorithmic trading based on the prediction of the next price movement’s direction.

7

## Slide 8

Reinforcement Learning Cases

Case Study 7: Chapter 7: Dynamic Hedging [p.105]: The seventh chapter is about learning optimal dynamic hedging strategies for an option with European exercise in the Black-Scholes-Merton (1973) model. In other words, delta hedging or dynamic replication of the option is the goal.

8

## Slide 9

Reinforcement Learning Cases

Case Study 8: Chapter 8: Dynamic Asset Allocation [p.129]: This chapter applies DQL to three canonical examples in asset management: one risky asset and one risk-free asset, two risky assets, and three risky assets. The problem is to dynamically allocate funds to the available assets to maximize a profit target or a risk-adjusted return (Sharpe ratio).

9

## Slide 10

Reinforcement Learning Cases

Case Study 9: Chapter 9: Optimal Execution [p.167]: The ninth chapter is about the optimal liquidation of a large position in a stock. Given a certain risk aversion, the total execution costs are to be minimized. This use case differs from the others in that all actions are tightly connected with each other through an additional constraint. The chapter also introduces an additional RL algorithm in the form of an actor-critic implementation.

10

## Slide 11

Reinforcement Learning Cases

BOOK 2:  Machine Learning Blueprints for Finance by Tatsat UofT:

https://librarysearch.library.utoronto.ca/permalink/01UTORONTO_INST/14bjeso/alma991107061413606196 

11

原页链接：<https://librarysearch.library.utoronto.ca/permalink/01UTORONTO_INST/14bjeso/alma991107061413606196>

## Slide 12

Reinforcement Learning Cases

Case Study 23: Reinforcement Learning–Based Trading Strategy [p.298]:                        

Blueprint for Creating a Reinforcement Learning–Based Trading Strategy  

Case Study 24: Derivatives Hedging  [p.316]:                                                                         

Blueprint for Implementing a Reinforcement Learning–Based Hedging Strategy  (See Part III of Benninga in Nyholm minicourse).

Case Study 25: Portfolio Allocation [p.334] 

Blueprint for Implementing a Reinforcement Learning–Based Portfolio Allocation (See Part II of Benninga in Nyholm minicourse)

12

## Slide 13

Reinforcement Learning Cases

BOOK 6:  Machine Learning for Finance by Klaas: UofT:

https://librarysearch.library.utoronto.ca/permalink/01UTORONTO_INST/10oudkq/cdi_walterdegruyter_books_10_0000_9781789134698_001 

13

原页链接：<https://librarysearch.library.utoronto.ca/permalink/01UTORONTO_INST/10oudkq/cdi_walterdegruyter_books_10_0000_9781789134698_001>

## Slide 14

Reinforcement Learning Cases

Case 44 Chapter 7 [p.277]  – Reinforcement Learning for Financial Markets

Presents reinforcement learning concepts and algorithms (Q-learning, actor-critic methods) and connects them to economic theory. Practical examples illustrate how RL can be applied to trading, portfolio construction, and sequential decision-making under uncertainty.

14

## Slide 15

Reinforcement Learning Cases

BOOK 7: Machine learning for algorithmic trading : predictive models to extract signals from market and alternative data for systematic trading strategies with Python, 2nd edition

By Stephen Jansen @ uoft:

https://librarysearch.library.utoronto.ca/permalink/01UTORONTO_INST/1dl2m71/alma991107212149706196  

15

原页链接：<https://librarysearch.library.utoronto.ca/permalink/01UTORONTO_INST/1dl2m71/alma991107212149706196>

## Slide 16

Reinforcement Learning Cases

Case 60 Chapter 22, Deep Reinforcement Learning – Building a Trading Agent [p.679], presents how reinforcement learning (RL) permits the design and training of agents that learn to optimize decisions over time in response to their environment. You will see how to create a custom trading environment and build an agent that responds to market signals using OpenAI Gym. 

16

## Slide 17

Generative AI Cases

BOOK 8: Generative AI for Trading and Asset Management by Jesse Hamlet, 2025  UofT: 

https://librarysearch.library.utoronto.ca/permalink/01UTORONTO_INST/1dl2m71/alma991107753593906196  

17

原页链接：<https://librarysearch.library.utoronto.ca/permalink/01UTORONTO_INST/1dl2m71/alma991107753593906196>

## Slide 18

Generative AI Cases

Case 61 Ch. 4 — Understanding Generative AI  (THEORETICAL CHAPTER)

Why Generative Models, Difference with Discriminative Models, Probability Density Estimation, Generating New Data, Learning New Data Representations, Language Modeling, Sampling, Conditional Language Generation, Representation Learning with ChatGPT, Hybrid Modeling: Combining Generative and Discriminative Models, Taxonomy of Generative Models

18

## Slide 19

Generative AI Cases

Case 62  Ch. 5 — Deep Autoregressive Models for Sequence Modeling (THEORETICAL CHAPTER)

Logistic regression/FVSN, MADE, causal masked networks/WaveNet, RNNs, Transformers (attention, positional encoding, multi-head attention, encoder), time-series transformers (Chronos, Lag-Llama)

19

## Slide 20

Generative AI Cases

Case 63 Ch. 9 — Leveraging LLMs for Sentiment Analysis in Trading (FINAL PROJECT CASE)

Sentiment Analysis in Fed Press Conference Speeches Using Large Language Models; Data: Video+Market Prices, Speech-to-text Conversion, Sentiment Analysis, Experiment Results

20

## Slide 21

Generative AI Cases

BOOK 9: Machine Learning For Trading 3rd Edition by Stefan Jansen, 2026  UofT:  

https://librarysearch.library.utoronto.ca/permalink/01UTORONTO_INST/10oudkq/cdi_walterdegruyter_books_10_0000_9781789342710_001 

https://learning.oreilly.com/library/view/machine-learning-for/9781803246970/?sso_link=yes&sso_link_from=utoronto-edu  

21

原页链接：<https://learning.oreilly.com/library/view/machine-learning-for/9781803246970/?sso_link=yes&sso_link_from=utoronto-edu>

原页链接：<https://librarysearch.library.utoronto.ca/permalink/01UTORONTO_INST/10oudkq/cdi_walterdegruyter_books_10_0000_9781789342710_001>

## Slide 22

Generative AI Cases

Case 64  Ch. 22 — RAG for Financial Research

Builds retrieval-augmented generation grounded in SEC filings, from ingestion and domain embeddings through hybrid retrieval, evaluation, and the transition to agentic workflows.

22

## Slide 23

Generative AI Cases

Case 65  Ch. 23 — Knowledge Graphs

Covers KG construction from filings, Graph RAG for multi-hop reasoning, graph features for ML, and temporal-leakage prevention

23

## Slide 24

Generative AI Cases

Case 66  Ch. 24 — Autonomous Agents

 Covers agent architectures, memory and tools, the engineering stack, a stateful equity-research agent, and multi-agent forecasting with adversarial debate.

24

## Slide 25

Generative AI Cases

OTHER  (GITHUB)

25

## Slide 26

Generative AI Cases

Case 67 GITHUB: 

StockTime: A Time Series Specialized Large Language Model Architecture for Stock Price Prediction (Wang et al., 2024-- https://arxiv.org/abs/2409

26

## Slide 27

Generative AI Cases

Case 68 GITHUB: 

QuantHarness: Price-Driven Multi-Agent LLMs for High-Frequency Trading  (Xiong et al., 2025— https://arxiv.org/abs/2509.09995 )

27

## Slide 28

Generative AI Cases

Case 69 GITHUB: 

Kronos: A Foundation Model for the Language of Financial Markets (Shi et al., 2025 — https://github.com/shiyu-coder/Kronos )

Analyzes prices in terms of Japanese candle stick patterns which are “phrase like” components:

e.g. https://ca.investing.com/indices/s-p-tsx-composite-candlestick 

28

原页链接：<https://ca.investing.com/indices/s-p-tsx-composite-candlestick>

