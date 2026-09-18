# 提示词配套包：阅读与验证切入点

检查日期：2026-09-18。已经取得、解压并按 SHA-256 校验 640 个文件；三份 Python 主脚本通过静态语法解析。没有导入或运行教师脚本，没有使用包中的凭据，没有调用付费 API，也没有复现样例结果。

## 先读什么

1. `prompt_reorganized.md`：较完整的自然语言任务与约束。
2. `prompt_prolog_version.txt`：Prolog 风格表示；须逐条判断哪些可执行、哪些只是说明。
3. `compendium_StructuralDescription_relationshiptypes.txt`：实体与关系结构。
4. `StructuralAndIntegrityRules_reference.txt`、`PipelineAndIntermediateOutputs_reference.txt`：规则和中间结果说明。后者自述只是参考，并非另一份实际管道输入。
5. 主程序、评估器、核查程序；最后看 `output/` 中已有结果。样例输出和当前代码的对应版本尚未验证。

完整文件链接见 [总目录](COURSE_CATALOG.md)，函数位置见 [源码地图](python-source-map.json)。原始文件在 `materials/APS1053/07_Prompt_Pipeline/DeepSeek_revised2_by_chatgpt/`。

## 包内组成

共 640 个文件，其中 410 JSON、107 TXT、100 Markdown、3 Python、7 PDF、2 DOCX、1 PPTX；其余为环境配置、日志、网页图、EPUB 等。`output/` 占 511 个文件，`transcripts/` 有 100 个文件。收到的原始目录还含 `.env`，原始凭据仅保留本地；公开包以 `.env.example` 替代，不含密钥。

| 程序 | 行数 | 用途 |
|---|---:|---|
| deepseek_speech_processing_program1_notree_revised2.py | 4780 | 字幕提取、汇总、分类、确定性重映射、汇编的五阶段流程 |
| standalone_evaluation_script_notree_revised2.py | 4673 | 结构、来源、版本与语义指标评估 |
| deepseek_program2_verify_claims_revised.py | 1379 | 模型判断与可选搜索，再修改匹配条目的状态标记 |

Word/PPT 是讲义和论文交流载体；执行材料已包含 MD/TXT、Python、JSON、YAML。仅凭文件格式不能断定方法过时。可以改进的是材料分层、明确运行入口、环境可复现、自动检查和版本对应关系。没有找到 `test_` 命名的测试文件，但已有独立评估器，不能据此说完全没有验证。

## 已看到的实现与边界

- 主程序 Phase 4 从 `copy.deepcopy(source_record)` 开始添加映射信息（约第 3048 行），这是研究数据保留性质的具体入口；是否所有分支保持哪些字段不变，仍需逐项检查。
- 主程序约第 4590–4638 行先写汇编文件，再运行并写入完整性检查结果。失败会记日志、将 manifest 标为不完整，`main` 约第 4765 行返回退出码 3。但失败后的文件仍可能存在，所以“有输出文件”不等于“获准使用的输出”。发布前必须检查状态，或另设验收通过后才发布的步骤。
- Phase 5 会记录并跳过合成失败的 bucket，随后用成功的子集生成 pair table。需要单独核对原始预期集合与失败集合；不能只看剩余子集的自洽性判断全体输入已覆盖。
- 评估器第 125 行默认指向 `speech_processing_program_notree_revised.py`，与收到的实际主程序文件名不同。复现时应明确传入正确路径，不直接依赖默认值。
- 第二个程序第 954–1019 行定义状态替换和保留性检查；第 1030–1040 行先检查再写结果。这给出了一个更小、更明确的形式化对象。
- 模型记忆或搜索产生的核查结论不是形式证明；保持来源 ID 与正文不变，也不能证明原始金融论断真实或合成文字忠实。

## 适合先做的 Lean 实验

建议先形式化状态替换，而不是整套语言模型流程：定义文档、允许编辑的位置和合法状态。证明替换只影响指定位置的状态字段，并保留所有其他字段/文本。随后再研究 Phase 4 的字段保留、引用完整性和预算约束。

Lean 中的模型证明不会自动覆盖现有 Python 实现。要么证明实现与模型的对应关系，要么让 Python 调用经过证明的检查器，并保证接受后使用的是同一份数据。正则解析、序列化、文件写入及错误处理都需要明确边界。

这个包研究的是受约束的 LLM 信息处理流程，没有据此发现强化学习训练或多智能体强化学习验证的实现。它可以作为你研究“模型提议—确定性检查—接受状态”的小型试验场，但向 RL 群体控制的推广仍是研究问题。
