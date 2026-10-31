---
name: ascend-operator
description: 统筹Ascend算子的设计、实现、编译、数值定位、性能优化与框架集成，按语言、芯片和阶段选原专项方法。用于明确算子目标；模型输出质量、整模型吞吐与部署分别交相应领域。
metadata:
  workbench_role: domain_entry
  workbench_domain: operator
---

# 算子领域

遵循[根规则](../../../AGENTS.md)和[分层协作](../../../docs/guides/skill-routing.md)。复用任务及有效知识；按语言/芯片、shape/dtype、编译/派发/数值或性能阶段检索，首次具体错误或条件变化再补查。

先确认接口、原语义、reference、生产输入和目标执行路径，再按阶段选择：

| 目标 | 首选及条件专题 |
|---|---|
| AscendC设计、tiling与实现 | cannbot tiling/extension方法；结合实际工程接口，不同时加载多个完整开发流程 |
| 独立数值误差/复现 | workspace operator-debug组织reference；AscendC再选cannbot precision-debug，不擅自放宽阈值 |
| AscendC性能/同步/审查 | cannbot perf-optimize/code-review等对应专题；端到端模型收益交性能领域验证 |
| Triton开发、验证与优化 | workspace Triton流程，原工具/后端适用另核；设计缺口再查cannbot或Ascend专项候选 |
| CATLASS/TileLang/PyPTO/SHMEM | 按实际语言选专题，不能套AscendC或Triton假设 |
| 编译异常、msOpProf、检测/调试工具 | 按已有产物与目标SoC选ascend_agent_skills或msagent对应专题；读取方法不自动安装/插桩 |

原资源及前提见[域内选用](references/scenario-selection.md)和[消费声明](references/upstream-usage.json)。使用原skill时按本轮阶段取必要reference/脚本；工具可用与方法可读分别验证。需要的个人skill不存在时查已登记替代，不将个人安装当公共依赖。

代码实现按用户范围推进，使用原执行/资源机制。保留编译、实际加载/派发、独立reference、功能/图模式和必要性能的分层证据；源码路径存在或静态检查不代表NPU正确。候选无收益/失败按本任务恢复，保留原失败。

支持且验证范围满足的自有能力优先；缺口由本域按发现协议查固定来源，实际适用后补位。模型首差未隔离到算子边界交[精度域](../ascend-model-accuracy/SKILL.md)，服务瓶颈交[性能域](../ascend-performance/SKILL.md)，跨域目标变化交主workflow协调。
