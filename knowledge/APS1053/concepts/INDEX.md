# 概念与问题导航

以下分类与问题是个人整理，不是作者已经证明的结论。

| 概念 | 当前材料 | 可以继续问什么 |
|---|---|---|
| 对象层与过程层 | [Prompt Architecture 草稿](../documents/PrologPromptArchitecture/index.md) | 哪些是领域事实，哪些是执行权限和过程约束？ |
| 最小代理权限／Least Agency | [同一草稿](../documents/PrologPromptArchitecture/index.md) | 哪些工作由 LLM 提议，哪些由确定性程序执行和检查？ |
| 来源与关系完整性 | [五阶段流程讲义](../documents/ProgrammableLLM_With_Prompt_(MAIN)/index.md) | 来源存在、关系合法与语义正确分别由谁判断？ |
| Prolog 与提示词 | [短讲义](../documents/Prompting_Claude_A_Logic_Programmers_Guide/index.md) · [长文](../documents/PrologAndPrompts/index.md) | 类比的适用边界在哪里，怎样转成可检验的命题？ |
| 强化学习与案例复现 | [案例目录](../documents/APS1053_CaseStudies_Reinforcement_GenerativeAI/index.md) | 状态、动作、奖励、预算和评价基线分别是什么？ |
| 全局不变量 | 与 leanSwap 的潜在联系 | 资金守恒、预算限制、授权与禁止重复结算如何表达？ |

## 一个可执行的整理单位

每个知识条目记录：定义；出处及页码/节号；例子；假设与适用边界；尚未解决的问题；相关实验/代码链接。

例如，`来源 ID 存在` 和 `该来源支持这一结论` 必须是不同的检查项。把它们分开后，才能讨论哪些能自动验证，哪些需要人工标注或其他证据。
