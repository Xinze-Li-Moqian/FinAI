# APS1053 案例选题指南

**23 个案例 · 6 个主题 · 一页阅读与跳转**

把老师的 28 页案例目录整理为可直接在 GitHub 阅读的中文导航。案例编号沿用原 PPT，缺号并非遗漏；这份文件并不是课程全部 69 个案例的总表。

[课程首页](../README.md) · [展示要求](../presentations/REQUIREMENTS.md) · [逐页英文提取稿](../../../knowledge/APS1053/documents/APS1053_CaseStudies_Reinforcement_GenerativeAI/index.md) · [下载原 PPT](../../../materials/APS1053/02_Cases_and_Presentations/APS1053_CaseStudies_Reinforcement_GenerativeAI.pptx)

## 怎么使用

1. 先浏览下方总览，按主题比较案例，再点编号阅读详情。
2. 通过详情中的书目与章节找到正文；这里是选题目录，不是完整教材。
3. 选题偏好记录在[候选清单](../presentations/CASE_SELECTION.md)。候选、预习和正式分配是不同状态。

**老师邮件的指引：**从这份 PPT 中提交 5 个按偏好排序的案例供分配；老师推荐的第 13–14 页对应同一个 **Case 44**（第 13 页是书目，第 14 页是案例）。第 2 页的 Hilpisch 是 RL 入门参考。上述说明来自选题邮件，不是 PPT 中额外增加的课程规定。

**材料边界：**中文说明是对课件的整理；每个条目保留英文原文和原页链接。书目名称、页码及论文年份按课件记录，未在本次整理中独立核验。这里不预设必须选择 Q-learning，也不把金融代理案例当作已经包含形式化验证。

## 案例总览

| 主题 | 案例 | 内容 | 出处 / 特别标记 | PPT 页 |
|---|---|---|---|---|
| RL 基础与整体框架 | [Case 1](#case-1) | 通过交互学习 | Book 1 · 第 1 章 · p.3 | 3 |
| RL 基础与整体框架 | [Case 2](#case-2) | 深度 Q 学习 | Book 1 · 第 2 章 · p.19 | 3 |
| RL 基础与整体框架 | [Case 3](#case-3) | 金融 Q 学习 | Book 1 · 第 3 章 · p.37 | 4 |
| RL 基础与整体框架 | [Case 44](#case-44) | 金融市场强化学习 | Book 6 · 第 7 章 · p.277 | 14 |
| 模拟数据与生成数据 | [Case 4](#case-4) | 模拟数据 | Book 1 · 第 4 章 · p.51 | 5 |
| 模拟数据与生成数据 | [Case 5](#case-5) | 生成数据 | Book 1 · 第 5 章 · p.67 | 6 |
| 金融决策：交易、对冲与配置 | [Case 6](#case-6) | 算法交易 | Book 1 · 第 6 章 · p.85 | 7 |
| 金融决策：交易、对冲与配置 | [Case 7](#case-7) | 动态对冲 | Book 1 · 第 7 章 · p.105 | 8 |
| 金融决策：交易、对冲与配置 | [Case 8](#case-8) | 动态资产配置 | Book 1 · 第 8 章 · p.129 | 9 |
| 金融决策：交易、对冲与配置 | [Case 9](#case-9) | 最优交易执行 | Book 1 · 第 9 章 · p.167 | 10 |
| 金融决策：交易、对冲与配置 | [Case 23](#case-23) | 基于强化学习的交易策略 | Book 2 · p.298 | 12 |
| 金融决策：交易、对冲与配置 | [Case 24](#case-24) | 衍生品对冲 | Book 2 · p.316 | 12 |
| 金融决策：交易、对冲与配置 | [Case 25](#case-25) | 投资组合配置 | Book 2 · p.334 | 12 |
| 金融决策：交易、对冲与配置 | [Case 60](#case-60) | 深度强化学习：构建交易代理 | Book 7 · 第 22 章 · p.679 | 16 |
| 生成式 AI 与序列模型 | [Case 61](#case-61) | 理解生成式 AI | Book 8 · 第 4 章 · 理论章节 | 18 |
| 生成式 AI 与序列模型 | [Case 62](#case-62) | 用于序列建模的深度自回归模型 | Book 8 · 第 5 章 · 理论章节 | 19 |
| 生成式 AI 与序列模型 | [Case 63](#case-63) | 用 LLM 分析交易相关情绪 | Book 8 · 第 9 章 · FINAL PROJECT CASE | 20 |
| 金融研究：检索、知识图谱与代理 | [Case 64](#case-64) | 金融研究的检索增强生成 | Book 9 · 第 22 章 | 22 |
| 金融研究：检索、知识图谱与代理 | [Case 65](#case-65) | 知识图谱 | Book 9 · 第 23 章 | 23 |
| 金融研究：检索、知识图谱与代理 | [Case 66](#case-66) | 自主代理 | Book 9 · 第 24 章 | 24 |
| 论文与代码项目 | [Case 67](#case-67) | 用于股价预测的时间序列专用大语言模型 | Wang et al. · 2024（课件标注） | 26 |
| 论文与代码项目 | [Case 68](#case-68) | 价格驱动的多代理 LLM 高频交易 | Xiong et al. · 2025（课件标注） | 27 |
| 论文与代码项目 | [Case 69](#case-69) | 金融市场语言基础模型 | Shi et al. · 2025（课件标注） | 28 |

## 案例详情

### RL 基础与整体框架

<a id="case-1"></a>

#### Case 1 · 通过交互学习

**Learning through interaction**

**出处：**[Book 1](#book-1) · 第 1 章 · p.3 · [PPT 第 3 页](../../../knowledge/APS1053/documents/APS1053_CaseStudies_Reinforcement_GenerativeAI/index.md#slide-3)

通过四个例子介绍交互学习：概率匹配、贝叶斯更新、强化学习（RL）和深度 Q 学习（DQL）。

<details>
<summary>展开课件英文原文</summary>

Case Study 1: Chapter 1: Learning through interaction [p.3]: The first chapter focuses on learning through interaction with four major examples: probability matching, Bayesian updating, RL, and DQL.

</details>

[返回案例总览](#案例总览)

<a id="case-2"></a>

#### Case 2 · 深度 Q 学习

**Deep Q Learning**

**出处：**[Book 1](#book-1) · 第 2 章 · p.19 · [PPT 第 3 页](../../../knowledge/APS1053/documents/APS1053_CaseStudies_Reinforcement_GenerativeAI/index.md#slide-3)

从动态规划（DP）出发，将 DQL 作为近似求解 DP 问题的方法。通过一系列动作和反复更新策略来最大化目标函数；使用 Gymnasium 的 CartPole 游戏演示 DQL 代理。

<details>
<summary>展开课件英文原文</summary>

Case Study 2: Chapter 2: Deep Q Learning [p.19]: The second chapter introduces concepts from dynamic programming (DP) and discusses DQL as an approach to approximate solutions to DP problems. The major theme is the derivation of optimal policies to maximize a given objective function through taking a sequence of actions and updating the optimal policy iteratively. DQL is illustrated on the basis of a DQL agent that learns to play the CartPole game from the Gymnasium Python package.

</details>

[返回案例总览](#案例总览)

<a id="case-3"></a>

#### Case 3 · 金融 Q 学习

**Financial Q Learning**

**出处：**[Book 1](#book-1) · 第 3 章 · p.37 · [PPT 第 4 页](../../../knowledge/APS1053/documents/APS1053_CaseStudies_Reinforcement_GenerativeAI/index.md#slide-4)

构建金融预测游戏环境，让第 2 章的 DQL 代理在其中学习。课件特别指出：虽然这个环境沿用了 CartPole 的 API，但仍缺少成功应用 RL 所需的一些重要特征。

<details>
<summary>展开课件英文原文</summary>

Case Study 3: Chapter 3: Financial Q Learning [p.37]: The third chapter develops a first Finance environment that allows the DQL agent from Chapter 2 to learn a financial prediction game. Although the environment formally replicates the API of the CartPole game, it misses some important characteristics that are needed to apply RL successfully.

</details>

[返回案例总览](#案例总览)

<a id="case-44"></a>

#### Case 44 · 金融市场强化学习

**Reinforcement Learning for Financial Markets**

**出处：**[Book 6](#book-6) · 第 7 章 · p.277 · [PPT 第 14 页](../../../knowledge/APS1053/documents/APS1053_CaseStudies_Reinforcement_GenerativeAI/index.md#slide-14)

介绍强化学习概念与算法，包括 Q-learning 和 actor-critic，并联系经济理论。实例涉及交易、投资组合构建，以及不确定性下的序贯决策。

**选题状态：**老师建议的案例；[现有准备工作区](../presentations/01-case44-candidate/README.md)中的 Q-learning 小实验属于可选预习，不代表已确定展示范围或已完成原案例复现。

<details>
<summary>展开课件英文原文</summary>

Case 44 Chapter 7 [p.277]  – Reinforcement Learning for Financial Markets

Presents reinforcement learning concepts and algorithms (Q-learning, actor-critic methods) and connects them to economic theory. Practical examples illustrate how RL can be applied to trading, portfolio construction, and sequential decision-making under uncertainty.

</details>

[返回案例总览](#案例总览)

### 模拟数据与生成数据

<a id="case-4"></a>

#### Case 4 · 模拟数据

**Simulated Data**

**出处：**[Book 1](#book-1) · 第 4 章 · p.51 · [PPT 第 5 页](../../../knowledge/APS1053/documents/APS1053_CaseStudies_Reinforcement_GenerativeAI/index.md#slide-5)

使用蒙特卡洛模拟进行数据增强，包括对历史数据加入噪声和模拟随机过程。

<details>
<summary>展开课件英文原文</summary>

DATA AUGMENTATION:

Case Study 4: Chapter 4: Simulated Data [p.51]: The fourth chapter is about data augmentation based on Monte Carlo simulation (MCS) approaches, and it discusses the addition of noise to historical data and the simulation of stochastic processes.

</details>

[返回案例总览](#案例总览)

<a id="case-5"></a>

#### Case 5 · 生成数据

**Generated Data**

**出处：**[Book 1](#book-1) · 第 5 章 · p.67 · [PPT 第 6 页](../../../knowledge/APS1053/documents/APS1053_CaseStudies_Reinforcement_GenerativeAI/index.md#slide-6)

使用生成对抗网络（GAN）生成金融时间序列，使其统计特征接近训练所用的历史时间序列。

<details>
<summary>展开课件英文原文</summary>

Case Study 5: Chapter 5: Generated Data [p.67]: The fifth chapter introduces generative adversarial networks (GANs) to synthetically generate time series data that has statistical characteristics that are similar to those of historical time series data on which a GAN was trained.

</details>

[返回案例总览](#案例总览)

### 金融决策：交易、对冲与配置

<a id="case-6"></a>

#### Case 6 · 算法交易

**Algorithmic Trading**

**出处：**[Book 1](#book-1) · 第 6 章 · p.85 · [PPT 第 7 页](../../../knowledge/APS1053/documents/APS1053_CaseStudies_Reinforcement_GenerativeAI/index.md#slide-7)

在 Case 3 的例子上扩展，通过预测下一次价格变动的方向，将 DQL 用于算法交易。

<details>
<summary>展开课件英文原文</summary>

FINANCIAL APPLICATIONS:

Case Study 6: Chapter 6: Algorithmic Trading [p.85]: Building on the example from Chapter 3, this chapter applies DQL to the problem of algorithmic trading based on the prediction of the next price movement’s direction.

</details>

[返回案例总览](#案例总览)

<a id="case-7"></a>

#### Case 7 · 动态对冲

**Dynamic Hedging**

**出处：**[Book 1](#book-1) · 第 7 章 · p.105 · [PPT 第 8 页](../../../knowledge/APS1053/documents/APS1053_CaseStudies_Reinforcement_GenerativeAI/index.md#slide-8)

在 Black–Scholes–Merton（1973）模型下，学习欧式期权的最优动态对冲策略；目标是 delta 对冲或期权的动态复制。

<details>
<summary>展开课件英文原文</summary>

Case Study 7: Chapter 7: Dynamic Hedging [p.105]: The seventh chapter is about learning optimal dynamic hedging strategies for an option with European exercise in the Black-Scholes-Merton (1973) model. In other words, delta hedging or dynamic replication of the option is the goal.

</details>

[返回案例总览](#案例总览)

<a id="case-8"></a>

#### Case 8 · 动态资产配置

**Dynamic Asset Allocation**

**出处：**[Book 1](#book-1) · 第 8 章 · p.129 · [PPT 第 9 页](../../../knowledge/APS1053/documents/APS1053_CaseStudies_Reinforcement_GenerativeAI/index.md#slide-9)

将 DQL 用于三种配置场景：一种风险资产与一种无风险资产、两种风险资产、三种风险资产。动态分配资金，以最大化利润目标或风险调整收益（Sharpe ratio）。

<details>
<summary>展开课件英文原文</summary>

Case Study 8: Chapter 8: Dynamic Asset Allocation [p.129]: This chapter applies DQL to three canonical examples in asset management: one risky asset and one risk-free asset, two risky assets, and three risky assets. The problem is to dynamically allocate funds to the available assets to maximize a profit target or a risk-adjusted return (Sharpe ratio).

</details>

[返回案例总览](#案例总览)

<a id="case-9"></a>

#### Case 9 · 最优交易执行

**Optimal Execution**

**出处：**[Book 1](#book-1) · 第 9 章 · p.167 · [PPT 第 10 页](../../../knowledge/APS1053/documents/APS1053_CaseStudies_Reinforcement_GenerativeAI/index.md#slide-10)

给定风险厌恶程度，最小化卖出大量股票持仓的总执行成本。课件强调，各次动作通过额外约束紧密关联；本章还引入 actor-critic 实现。

<details>
<summary>展开课件英文原文</summary>

Case Study 9: Chapter 9: Optimal Execution [p.167]: The ninth chapter is about the optimal liquidation of a large position in a stock. Given a certain risk aversion, the total execution costs are to be minimized. This use case differs from the others in that all actions are tightly connected with each other through an additional constraint. The chapter also introduces an additional RL algorithm in the form of an actor-critic implementation.

</details>

[返回案例总览](#案例总览)

<a id="case-23"></a>

#### Case 23 · 基于强化学习的交易策略

**Reinforcement Learning–Based Trading Strategy**

**出处：**[Book 2](#book-2) · p.298 · [PPT 第 12 页](../../../knowledge/APS1053/documents/APS1053_CaseStudies_Reinforcement_GenerativeAI/index.md#slide-12)

创建基于强化学习的交易策略的实现蓝图。

<details>
<summary>展开课件英文原文</summary>

Case Study 23: Reinforcement Learning–Based Trading Strategy [p.298]:                        

Blueprint for Creating a Reinforcement Learning–Based Trading Strategy

</details>

[返回案例总览](#案例总览)

<a id="case-24"></a>

#### Case 24 · 衍生品对冲

**Derivatives Hedging**

**出处：**[Book 2](#book-2) · p.316 · [PPT 第 12 页](../../../knowledge/APS1053/documents/APS1053_CaseStudies_Reinforcement_GenerativeAI/index.md#slide-12)

实现基于强化学习的对冲策略。课件另指向 Nyholm minicourse 中 Benninga 的 Part III。

<details>
<summary>展开课件英文原文</summary>

Case Study 24: Derivatives Hedging  [p.316]:                                                                         

Blueprint for Implementing a Reinforcement Learning–Based Hedging Strategy  (See Part III of Benninga in Nyholm minicourse).

</details>

[返回案例总览](#案例总览)

<a id="case-25"></a>

#### Case 25 · 投资组合配置

**Portfolio Allocation**

**出处：**[Book 2](#book-2) · p.334 · [PPT 第 12 页](../../../knowledge/APS1053/documents/APS1053_CaseStudies_Reinforcement_GenerativeAI/index.md#slide-12)

实现基于强化学习的投资组合配置。课件另指向 Nyholm minicourse 中 Benninga 的 Part II。

<details>
<summary>展开课件英文原文</summary>

Case Study 25: Portfolio Allocation [p.334] 

Blueprint for Implementing a Reinforcement Learning–Based Portfolio Allocation (See Part II of Benninga in Nyholm minicourse)

</details>

[返回案例总览](#案例总览)

<a id="case-60"></a>

#### Case 60 · 深度强化学习：构建交易代理

**Deep Reinforcement Learning – Building a Trading Agent**

**出处：**[Book 7](#book-7) · 第 22 章 · p.679 · [PPT 第 16 页](../../../knowledge/APS1053/documents/APS1053_CaseStudies_Reinforcement_GenerativeAI/index.md#slide-16)

介绍如何设计和训练代理，使其通过与环境交互优化长期决策；创建自定义交易环境，并使用 OpenAI Gym 构建响应市场信号的代理。

<details>
<summary>展开课件英文原文</summary>

Case 60 Chapter 22, Deep Reinforcement Learning – Building a Trading Agent [p.679], presents how reinforcement learning (RL) permits the design and training of agents that learn to optimize decisions over time in response to their environment. You will see how to create a custom trading environment and build an agent that responds to market signals using OpenAI Gym.

</details>

[返回案例总览](#案例总览)

### 生成式 AI 与序列模型

<a id="case-61"></a>

#### Case 61 · 理解生成式 AI

**Understanding Generative AI**

**出处：**[Book 8](#book-8) · 第 4 章 · 理论章节 · [PPT 第 18 页](../../../knowledge/APS1053/documents/APS1053_CaseStudies_Reinforcement_GenerativeAI/index.md#slide-18)

讨论生成模型的动机、与判别模型的区别、概率密度估计、生成新数据、学习数据的新表示、语言建模、采样、条件语言生成、使用 ChatGPT 学习表示、生成与判别混合建模，以及生成模型的分类。

**课件标记：**THEORETICAL CHAPTER。若选此项，代码和实验交付如何适用仍需与老师确认。

<details>
<summary>展开课件英文原文</summary>

Case 61 Ch. 4 — Understanding Generative AI  (THEORETICAL CHAPTER)

Why Generative Models, Difference with Discriminative Models, Probability Density Estimation, Generating New Data, Learning New Data Representations, Language Modeling, Sampling, Conditional Language Generation, Representation Learning with ChatGPT, Hybrid Modeling: Combining Generative and Discriminative Models, Taxonomy of Generative Models

</details>

[返回案例总览](#案例总览)

<a id="case-62"></a>

#### Case 62 · 用于序列建模的深度自回归模型

**Deep Autoregressive Models for Sequence Modeling**

**出处：**[Book 8](#book-8) · 第 5 章 · 理论章节 · [PPT 第 19 页](../../../knowledge/APS1053/documents/APS1053_CaseStudies_Reinforcement_GenerativeAI/index.md#slide-19)

内容包括 logistic regression/FVSN、MADE、因果掩码网络/WaveNet、RNN 和 Transformer（注意力、位置编码、多头注意力、编码器），以及时间序列 Transformer：Chronos、Lag-Llama。

**课件标记：**THEORETICAL CHAPTER。若选此项，代码和实验交付如何适用仍需与老师确认。

<details>
<summary>展开课件英文原文</summary>

Case 62  Ch. 5 — Deep Autoregressive Models for Sequence Modeling (THEORETICAL CHAPTER)

Logistic regression/FVSN, MADE, causal masked networks/WaveNet, RNNs, Transformers (attention, positional encoding, multi-head attention, encoder), time-series transformers (Chronos, Lag-Llama)

</details>

[返回案例总览](#案例总览)

<a id="case-63"></a>

#### Case 63 · 用 LLM 分析交易相关情绪

**Leveraging LLMs for Sentiment Analysis in Trading**

**出处：**[Book 8](#book-8) · 第 9 章 · FINAL PROJECT CASE · [PPT 第 20 页](../../../knowledge/APS1053/documents/APS1053_CaseStudies_Reinforcement_GenerativeAI/index.md#slide-20)

分析美联储新闻发布会讲话中的情绪。案例涵盖视频与市场价格数据、语音转文字、情绪分析和实验结果。课件将它特别标为期末项目案例。

**课件标记：**FINAL PROJECT CASE。不要直接视为普通两次展示中的一个；交付方式需按老师确认执行。

<details>
<summary>展开课件英文原文</summary>

Case 63 Ch. 9 — Leveraging LLMs for Sentiment Analysis in Trading (FINAL PROJECT CASE)

Sentiment Analysis in Fed Press Conference Speeches Using Large Language Models; Data: Video+Market Prices, Speech-to-text Conversion, Sentiment Analysis, Experiment Results

</details>

[返回案例总览](#案例总览)

### 金融研究：检索、知识图谱与代理

<a id="case-64"></a>

#### Case 64 · 金融研究的检索增强生成

**RAG for Financial Research**

**出处：**[Book 9](#book-9) · 第 22 章 · [PPT 第 22 页](../../../knowledge/APS1053/documents/APS1053_CaseStudies_Reinforcement_GenerativeAI/index.md#slide-22)

以 SEC 披露文件为依据构建 RAG，涵盖数据摄入、领域嵌入、混合检索、评估，以及向代理工作流的过渡。

<details>
<summary>展开课件英文原文</summary>

Case 64  Ch. 22 — RAG for Financial Research

Builds retrieval-augmented generation grounded in SEC filings, from ingestion and domain embeddings through hybrid retrieval, evaluation, and the transition to agentic workflows.

</details>

[返回案例总览](#案例总览)

<a id="case-65"></a>

#### Case 65 · 知识图谱

**Knowledge Graphs**

**出处：**[Book 9](#book-9) · 第 23 章 · [PPT 第 23 页](../../../knowledge/APS1053/documents/APS1053_CaseStudies_Reinforcement_GenerativeAI/index.md#slide-23)

从披露文件构建知识图谱；使用 Graph RAG 进行多跳推理；为机器学习构建图特征，并防止时间信息泄漏。

<details>
<summary>展开课件英文原文</summary>

Case 65  Ch. 23 — Knowledge Graphs

Covers KG construction from filings, Graph RAG for multi-hop reasoning, graph features for ML, and temporal-leakage prevention

</details>

[返回案例总览](#案例总览)

<a id="case-66"></a>

#### Case 66 · 自主代理

**Autonomous Agents**

**出处：**[Book 9](#book-9) · 第 24 章 · [PPT 第 24 页](../../../knowledge/APS1053/documents/APS1053_CaseStudies_Reinforcement_GenerativeAI/index.md#slide-24)

介绍代理架构、记忆、工具和工程栈；构建保存状态的股票研究代理，并涉及多代理预测与对抗式辩论。

<details>
<summary>展开课件英文原文</summary>

Case 66  Ch. 24 — Autonomous Agents

 Covers agent architectures, memory and tools, the engineering stack, a stateful equity-research agent, and multi-agent forecasting with adversarial debate.

</details>

[返回案例总览](#案例总览)

### 论文与代码项目

<a id="case-67"></a>

#### Case 67 · 用于股价预测的时间序列专用大语言模型

**StockTime**

**出处：**Wang et al. · 2024（课件标注） · [PPT 第 26 页](../../../knowledge/APS1053/documents/APS1053_CaseStudies_Reinforcement_GenerativeAI/index.md#slide-26)

课件列出的题目为 StockTime: A Time Series Specialized Large Language Model Architecture for Stock Price Prediction。该页的 arXiv 地址只有 https://arxiv.org/abs/2409，链接不完整，暂不据此指定论文。

<details>
<summary>展开课件英文原文</summary>

Case 67 GITHUB: 

StockTime: A Time Series Specialized Large Language Model Architecture for Stock Price Prediction (Wang et al., 2024-- https://arxiv.org/abs/2409

</details>

[返回案例总览](#案例总览)

<a id="case-68"></a>

#### Case 68 · 价格驱动的多代理 LLM 高频交易

**QuantHarness**

**出处：**Xiong et al. · 2025（课件标注） · [PPT 第 27 页](../../../knowledge/APS1053/documents/APS1053_CaseStudies_Reinforcement_GenerativeAI/index.md#slide-27)

课件列出的题目为 QuantHarness: Price-Driven Multi-Agent LLMs for High-Frequency Trading，并附 arXiv 链接。题名、作者和链接对应关系尚未在本次整理中核验。

[课件所列 arXiv 链接](https://arxiv.org/abs/2509.09995)（待核验）。

<details>
<summary>展开课件英文原文</summary>

Case 68 GITHUB: 

QuantHarness: Price-Driven Multi-Agent LLMs for High-Frequency Trading  (Xiong et al., 2025— https://arxiv.org/abs/2509.09995 )

</details>

[返回案例总览](#案例总览)

<a id="case-69"></a>

#### Case 69 · 金融市场语言基础模型

**Kronos**

**出处：**Shi et al. · 2025（课件标注） · [PPT 第 28 页](../../../knowledge/APS1053/documents/APS1053_CaseStudies_Reinforcement_GenerativeAI/index.md#slide-28)

课件将日本蜡烛图形态视为类似“短语”的组成部分，并列出 Kronos 代码仓库和 Investing.com 蜡烛图示例页面。

[课件所列 GitHub 仓库](https://github.com/shiyu-coder/Kronos) · [课件所列蜡烛图示例](https://ca.investing.com/indices/s-p-tsx-composite-candlestick)。

<details>
<summary>展开课件英文原文</summary>

Case 69 GITHUB: 

Kronos: A Foundation Model for the Language of Financial Markets (Shi et al., 2025 — https://github.com/shiyu-coder/Kronos )

Analyzes prices in terms of Japanese candle stick patterns which are “phrase like” components:

e.g. https://ca.investing.com/indices/s-p-tsx-composite-candlestick

</details>

[返回案例总览](#案例总览)

## 书目与阅读入口

Book 编号沿用课件。以下为原页所列访问入口，学校资源可能需要 UofT 登录；本次未验证各链接的可访问性或书目匹配情况。

<a id="book-1"></a>

### Book 1 · Hilpisch — Reinforcement Learning for Finance

对应案例：[Case 1](#case-1) · [Case 2](#case-2) · [Case 3](#case-3) · [Case 4](#case-4) · [Case 5](#case-5) · [Case 6](#case-6) · [Case 7](#case-7) · [Case 8](#case-8) · [Case 9](#case-9)。

- [UofT 图书馆入口](https://librarysearch.library.utoronto.ca/permalink/01UTORONTO_INST/1dl2m71/alma991107425685806196)
- [原课件书目页：第 2 页](../../../knowledge/APS1053/documents/APS1053_CaseStudies_Reinforcement_GenerativeAI/index.md#slide-2)

<a id="book-2"></a>

### Book 2 · Tatsat — Machine Learning Blueprints for Finance

对应案例：[Case 23](#case-23) · [Case 24](#case-24) · [Case 25](#case-25)。

- [UofT 图书馆入口](https://librarysearch.library.utoronto.ca/permalink/01UTORONTO_INST/14bjeso/alma991107061413606196)
- [原课件书目页：第 11 页](../../../knowledge/APS1053/documents/APS1053_CaseStudies_Reinforcement_GenerativeAI/index.md#slide-11)

<a id="book-6"></a>

### Book 6 · Klaas — Machine Learning for Finance

对应案例：[Case 44](#case-44)。

- [UofT 图书馆入口](https://librarysearch.library.utoronto.ca/permalink/01UTORONTO_INST/10oudkq/cdi_walterdegruyter_books_10_0000_9781789134698_001)
- [原课件书目页：第 13 页](../../../knowledge/APS1053/documents/APS1053_CaseStudies_Reinforcement_GenerativeAI/index.md#slide-13)

<a id="book-7"></a>

### Book 7 · Jansen — Machine Learning for Algorithmic Trading, 2nd edition

对应案例：[Case 60](#case-60)。

- [UofT 图书馆入口](https://librarysearch.library.utoronto.ca/permalink/01UTORONTO_INST/1dl2m71/alma991107212149706196)
- [原课件书目页：第 15 页](../../../knowledge/APS1053/documents/APS1053_CaseStudies_Reinforcement_GenerativeAI/index.md#slide-15)

<a id="book-8"></a>

### Book 8 · Generative AI for Trading and Asset Management（课件署名 Jesse Hamlet，2025）

对应案例：[Case 61](#case-61) · [Case 62](#case-62) · [Case 63](#case-63)。

- [UofT 图书馆入口](https://librarysearch.library.utoronto.ca/permalink/01UTORONTO_INST/1dl2m71/alma991107753593906196)
- [原课件书目页：第 17 页](../../../knowledge/APS1053/documents/APS1053_CaseStudies_Reinforcement_GenerativeAI/index.md#slide-17)

<a id="book-9"></a>

### Book 9 · Stefan Jansen — Machine Learning for Trading, 3rd edition（课件标注 2026）

对应案例：[Case 64](#case-64) · [Case 65](#case-65) · [Case 66](#case-66)。

- [O’Reilly 阅读入口（UofT）](https://learning.oreilly.com/library/view/machine-learning-for/9781803246970/?sso_link=yes&sso_link_from=utoronto-edu)
- [UofT 图书馆入口](https://librarysearch.library.utoronto.ca/permalink/01UTORONTO_INST/10oudkq/cdi_walterdegruyter_books_10_0000_9781789342710_001)
- [原课件书目页：第 21 页](../../../knowledge/APS1053/documents/APS1053_CaseStudies_Reinforcement_GenerativeAI/index.md#slide-21)

## 原稿覆盖说明

- 第 1 页为标题；第 25 页为 OTHER (GITHUB) 分类页。
- 第 2、11、13、15、17、21 页为书目页，已汇总到上面的阅读入口。
- 其余页面的全部 23 个案例都在总览和详情中，英文描述保留在各条目的展开区。
- Case 67 的原始论文链接不完整；本版明确保留该问题，没有猜补地址。
- 个人选题建议与后续实验写入各自工作区，不混入教师的案例描述。

整理依据：APS1053_CaseStudies_Reinforcement_GenerativeAI.pptx，2026-09-18 收到的版本。教师材料的署名和权利归原作者，本页为学生阅读整理版。
