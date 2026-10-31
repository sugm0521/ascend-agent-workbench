# 推理性能调优

## 启动与领域归属

本能力由[性能领域](../ascend-performance/SKILL.md)维护；可直接指定，也可由主/领域调用，按[共用约定](../../../docs/guides/skill-routing.md)复用任务和知识查询。具体输入输出、脚本与原验收边界见[SKILL](SKILL.md)。


`ascend-inference-optimization` 的使用说明，面向提出任务的使用者；详细执行规则以 [SKILL.md](SKILL.md) 为准。

## 能做什么

把AISBench基线、profiling、瓶颈判断、配置或代码候选以及性能/精度回归连接起来，推进可比较的优化实验。

## 什么时候用

有吞吐、TTFT、TPOT、PD每卡吞吐或性能退化目标时使用；单次压测或单份profiling解读无需完整调优流程。

相邻入口：[ascend-performance-benchmark](../ascend-performance-benchmark/README.md)、[ascend-model-accuracy](../ascend-model-accuracy/README.md)。

## 怎么调用

- 使用 $ascend-inference-optimization，分析现有服务吞吐下降的原因，先核对基线和瓶颈，不重启服务。
- 使用 $ascend-inference-optimization，在已确认负载下优化TPOT，只允许调整列明的参数，保留精度回归要求。

## 需要提供什么

目标指标、服务/模型、负载与资源范围，以及允许调整的配置或代码、预算和精度要求。

agent 会先查：实际源码/运行环境、已有性能和profiling证据；缺少可比条件时先说明。

## 会产出什么

可比基线、瓶颈证据、候选及逐轮实验结论，说明收益、退化、精度与剩余缺口。

已有trace、Profiler DB或msMemScope数据时，先按材料和证据窗口选分析方法，保留工具/采集缺口；不会为了调优默认重采或同时展开多套分析。方法选择见[分析输入说明](../ascend-performance/references/analysis-selection.md#分析输入与方法)。

## 操作边界

分析不自动改代码；候选执行按具体授权。运行实验可能使用NPU或服务资源，不影响他人服务，不用性能收益抵消精度失败，不自动提交推送。

返回[项目功能索引](../../../README.md)。提交、推送和发布统一遵循[项目规则](../../../AGENTS.md)及本轮具体授权。
