---
name: ascend-model-accuracy
description: 复现、定位和按授权修复 vLLM Ascend 模型的乱码、复读、异常空输出、参考结果不一致或评测精度下降，并组织目标场景回归。用于模型精度与输出质量问题；普通启动报错、纯性能压测和已隔离的算子误差走原领域入口。
---

# 模型精度诊断与验证

遵循[项目规则](../../../AGENTS.md)。本 skill 独立维护模型精度流程；workflow 只负责路由，也可直接调用本 skill。定位请求交付证据与建议，修复请求在已明确范围内修改和验证；测试容器本身不代表允许安装、改源码或重启。

## 从问题到证据

1. 明确异常、原始触发条件、正常基线和验收标准。复用已有目标与授权，只询问无法查证且影响判断的信息。尚无量化标准时可先定位，正式通过标准按用户目标确认。
2. 通过 [runtime-snapshot](../ascend-runtime-snapshot/SKILL.md) 记录实际代码、模型/tokenizer、依赖、启动参数与拓扑；已有证据仍适用时复用。远程运行使用本会话真实绑定与已有执行工具，不按工作目录猜资源或另建机器清单。
3. 在原配置保留 bad case、请求与响应证据，再按[症状诊断](references/diagnosis.md)选择最小对照。对齐输入 token IDs、模板、采样、停止条件和评测器；先排除输入、解析和评分差异。
4. 根据首个差异与触发条件选择下表能力；只改变假设对应的变量。概率问题记录请求数、失败数、seed、负载、超时和停止条件；特性交互有证据时再扩大消融。
5. 获授权修复时保存变更前状态和回滚点，实施最小改动。候选有效后用 A/B/A、版本回切或等价证据建立因果关系，再验证原 bad case 与必需目标场景。
6. 精度与性能分别验收。回归覆盖用户要求和变更影响的上下文、并发、PD/TP/DP/EP 与特性；性能测量按用户要求或受影响优化选择工作负载，不默认展开全组合测试。

## 复用已有能力

| 当前判断 | 入口与职责 |
|---|---|
| baseline/candidate、eager/graph、离线/在线或任务分数比较 | [correctness-validation](../../../deps/vllm-ascend-workspace/.agents/skills/vllm-ascend-correctness-validation/SKILL.md)：可比性、运行证据、阈值和结果分类 |
| eager 正常，graph 异常或 replay 首个分叉 | [graph-debug](../../../deps/vllm-ascend-workspace/.agents/skills/vllm-ascend-graph-debug/SKILL.md)：阶段、metadata 与图内安全取证 |
| 故障依赖 rank、DP/EP、跨机或通信 | [distributed-debug](../../../deps/vllm-ascend-workspace/.agents/skills/vllm-ascend-distributed-debug/SKILL.md)：拓扑与各 rank 证据 |
| 已缩到具体算子边界 | [operator-debug](../../../deps/vllm-ascend-workspace/.agents/skills/ascend-operator-debug/SKILL.md)：独立 reference 和输入矩阵；AscendC 实现再用 [precision-debug](../../../deps/cannbot-skills/ops/ascendc-precision-debug/SKILL.md) |
| 已有 AISBench 结果需要逐组指标、答案与输出审计 | [证据报告](../../../docs/tools/aisbench-evidence.md)：离线整理；任务分数和通过判定仍由原 correctness 流程负责 |
| 修复影响吞吐/时延或用户要求性能回归 | [performance-benchmark](../ascend-performance-benchmark/SKILL.md)：目标负载测量；可比回归按原 performance-regression 入口组织 |

上游手册的读取时机、原工具的替代关系和许可见[来源与接入](references/source-and-tools.md)。按当前分支读取，不把原 skill 的默认副作用、执行工具或所有生态依赖一起启用。

## 结论与交付

- 仅观察到现象消失：候选结果；原拓扑或必需负载尚未复验时继续保留缺口。
- 关闭功能、回退版本或确定性模式才能通过：规避；不能据此宣称错误实现已修复。是否接受规避沿用用户的明确决定。
- 定位到致因、实施修复、具备因果证据且必需回归通过：可报告已修复。
- 未复现、证据不足或缺少执行条件：说明结论范围与继续条件；不把未测写成通过。

以上是精度结论，主任务状态仍遵循项目规则。只授权定位的任务可在证据与建议完成后交付，不自动继续业务修复。输出异常率、有效答案比例与任务分数分别呈现；两个空答案、格式匹配或 HTTP 成功不能证明精度通过。

本 skill 内部诊断、消融、回归的原生测试结果、服务日志、plog 和张量保留在该精度任务的远程服务器目录；“原位置”明确指远端。本机任务只保存必要分析摘要、关键结论、回归/回滚说明和远端结果定位，分析通过原执行工具就地读取必要信息。采用[材料规范中的精度例外](../../../docs/guides/task-records.md#日志采集与分析)，不自动下载原件。

内部测试沿用精度任务自己的实验编号，即使用 AISBench 也不登记正式测试总表。用户要求的正式精度评测按[精度测试表规范](../../../docs/guides/task-records.md#三类正式测试总表)登记官方指标、数据集和评测器身份、样本及执行失败数；接手手动启动的正式评测且无表项时先补登记，再关联分析。SWE 数据集上的 agent 评测使用独立 SWE 表及实际 runner，不与模型精度混用。上述内部测试的逐题结果归该远端任务，正式评测按本次采集约定保存；额外说明集中在分析摘要中，不按每个样本新建本机文档。提交、推送及公开 issue 按具体授权处理。
