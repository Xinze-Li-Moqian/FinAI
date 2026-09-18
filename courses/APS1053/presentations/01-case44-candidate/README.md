# 展示一候选：Case 44 — Reinforcement Learning for Financial Markets

当前阶段：候选／预习。没有宣称已获教师分配、已复现金融交易案例或已完成课程展示。

## 从这里开始

1. 打开 [表格 Q-learning 预习 Notebook](warmup/00_tabular_q_learning.ipynb)，逐步理解状态、动作、奖励、Q 表和更新。
2. 看 [实验结果与限制](warmup/RESULTS.md)。这是 Catch 玩具环境，不是金融绩效。
3. 对照 [出版社原始代码说明](UPSTREAM_REVIEW.md) 和 [原始 Notebook](upstream/)。
4. 按 [正式案例复现计划](REPRODUCTION_PLAN.md) 继续，准备数据与 A2C 交易实现。
5. 用 [展示结构模板](../PRESENTATION_TEMPLATE.md) 写自己的说明。

## 当前文件

- `upstream/`：出版社三个原始 Notebook，固定提交与 SHA-256，保留 MIT 许可。文件未执行、未修改。
- `warmup/`：无神经网络的简化学习实验，Python 标准库即可运行，附生成数据、指标与轨迹。
- `REPRODUCTION_PLAN.md`：正式复现与扩展的待办。
- `talk-notes.md`：需要自己讲明白的问题。

## 运行预习实验

从此目录运行：

```sh
python3 warmup/tabular_catch.py
```

输出到 `warmup/results/`。无需 GPU、API 密钥或付费调用。Notebook 使用相同模块；用 Jupyter 时先切换到 `warmup/`。这次逐个代码单元已通过 Python 执行并保存输出，但尚未在 Jupyter 前端做交互测试。
