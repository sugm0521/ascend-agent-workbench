# 域内场景与来源选择

从本域SKILL按目标进入，只读取相关行及原资源。表中候选未承诺工具就绪；与当前后端/输入不适用时只保留方法范围，不另建运行状态。实际采用记录在upstream-usage.json，原资源路径按lock/本机配置解析。

| 场景与输入 | 本域方法/原资源定位 | 条件与边界 |
|---|---|---|
| C03 正式模型数据集精度评测 | 本领域组织实际评测器，correctness负责可比性与判定；定位：[workspace/vllm-ascend-correctness-validation](../../../../deps/vllm-ascend-workspace/.agents/skills/vllm-ascend-correctness-validation/SKILL.md)（现有方法）、[msagent/run-aisbench-evaluation](../../../../deps/msagent/skills/benchmark/run-aisbench-evaluation/SKILL.md)（补充候选） | msagent run-aisbench-evaluation可参考任务名和配置选用；awesome ais-bench-eval仅候选；新评测运行器尚未适配；不引入其默认评测机/hosts/task表 |
| D01 乱码、复读、空输出与分数退化 | 项目model-accuracy组织问题；awesome诊断/修复手册按阶段参考；定位：[ascend-model-accuracy](../SKILL.md)（主入口）、[awesome_agent_skills/vllm-ascend-accuracy](../../../../deps/awesome-agent-skills/vllm-ascend-accuracy/SKILL.md)（按阶段取手册）、[msagent/precision-debugger](../../../../deps/msagent/skills/accuracy/precision-debugger/SKILL.md)（仅案例资源候选） | msagent precision-debugger只建议消费其references/summary.md的匹配案例；不加载三个完整修复流程；案例需要版本/源码证据，不能直接认定根因 |
| D02 已指向KVCache/FlashAttention数值分叉 | 沿D01任务，定向参考cannbot model-infer-precision-debug；定位：[cannbot/model-infer-precision-debug](../../../../deps/cannbot-skills/model/model-infer-precision-debug/SKILL.md)（专题补充候选） | 其metadata/packed sequence等假设须与目标实现核对；不是所有模型精度问题的默认完整流程 |
| D03 eager正常、graph/replay异常 | workspace graph-debug方法；定位：[workspace/vllm-ascend-graph-debug](../../../../deps/vllm-ascend-workspace/.agents/skills/vllm-ascend-graph-debug/SKILL.md)（现有专题方法） | 项目精度任务保留原始reference与回归；原后端入口兼容另验，不用调试同步改变复现 |
| D04 rank/并行/跨机相关错误 | workspace distributed-debug方法；定位：[workspace/vllm-ascend-distributed-debug](../../../../deps/vllm-ascend-workspace/.agents/skills/vllm-ascend-distributed-debug/SKILL.md)（现有专题方法） | 算子边界明确后进G04；HCCL打流另进H01；通信trace分析不能代替分布式正确性验收 |
| D05 训练NaN、确定性或梯度尖刺 | 按实际症状查msagent accuracy和cannbot model-train专题；定位：[msagent/nan-overflow-detection](../../../../deps/msagent/skills/accuracy/nan-overflow-detection/SKILL.md)（专题候选）、[msagent/deterministic-calculation-analysis](../../../../deps/msagent/skills/accuracy/deterministic-calculation-analysis/SKILL.md)（专题候选）、[msagent/spike-root-cause-analysis](../../../../deps/msagent/skills/accuracy/spike-root-cause-analysis/SKILL.md)（专题候选） | msagent nan-overflow/deterministic/spike分别为不同输入；当前没有项目训练精度统一适配；保持专题候选，不套D01推理流程 |

方法不足时按[依赖能力发现](../../../../upstream/skill-mapping.md#依赖能力发现入口)查询已登记来源，足够即停。候选选择或上游更新影响本域时核对新增/增强/修复及旧适配，采用后同步消费声明与受影响引用。
