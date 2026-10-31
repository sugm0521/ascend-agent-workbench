---
name: ascend-performance
description: 统筹Ascend推理压测、性能调优、profiling、显存和HCCL通信打流，按目标与已有输入选择自有或上游能力。用于性能与通信目标；模型评分、算子实现和重新部署分别交对应领域。
metadata:
  workbench_role: domain_entry
  workbench_domain: performance
---

# 性能领域

遵循[根规则](../../../AGENTS.md)和[分层协作](../../../docs/guides/skill-routing.md)。可直接启动；复用任务、授权、工具绑定与有效知识查询，不先跑完整主流程。

先按本轮目标和已有材料分类。首次/新分支检索负载身份、PD角色、prefix/正式窗口、profiling输入或HBM；新错误/条件变化按共用触发补查。

| 目标/输入 | 选用与停止条件 |
|---|---|
| 吞吐、TTFT/TPOT、并发、prefix负载或既有结果补录 | [benchmark](../ascend-performance-benchmark/SKILL.md)；原生结果够用即交付，不自动变为完整调优 |
| 性能目标、退化归因、配置/代码候选及可比回归 | [inference-optimization](../ascend-inference-optimization/SKILL.md)；保留基线、假设和精度边界 |
| 已有trace/DB、整体或通信/计算/调度专题 | [分析输入与方法](references/analysis-selection.md)；先识别产物/schema和窗口，已有数据够用不重采 |
| 显存/OOM | 同上区分服务HBM组件和msMemScope dump；OOM不必然需要新采集 |
| 明确alltoallvc打流/故障验证 | [HCCL能力](../ascend-hccl-traffic-test/SKILL.md)；核对操作、节点/规模和两种模式，不用trace代替正确性 |
| AllReduce/AllGather等其他集合操作 | 查本域专题表的hccl-test候选，验证前提后选用；不能硬套alltoallvc |

专题、来源及已知前提见[域内选用](references/scenario-selection.md)，准确的消费关系见[来源声明](references/upstream-usage.json)。整体trace/服务HBM优先workspace方法，匹配DB/SQL及msMemScope专题按msagent输入契约；方法可读和工具可调用分开验证。

选中的自有能力适用且验证范围满足时优先；不足则定向核对原skill及必要reference/工具后补位，仍无覆盖按共用发现协议查已登记来源。记录任务所用版本、理由和结果，值得吸收的改进交维护流程评估，不为每个专题造包装。

重新部署交[部署域](../ascend-deployment/SKILL.md)，模型输出/评分交[精度域](../ascend-model-accuracy/SKILL.md)，已隔离算子实现交[算子域](../ascend-operator/SKILL.md)。目标/资源扩大时由主workflow协调，不重复问已知信息。

交付原生指标/分析证据、方法与实际工具、capture/rank/step或负载范围、失败/未验项及资源状态。端到端收益需要可比测量；静态、离线分析、采集和NPU测量分开。
