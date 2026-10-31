---
name: ascend-model-engineering
description: 统筹模型架构分析、参数/KV估算、仿真、量化及框架实现适配，按交付目标选原方法并核对实际源码。用于模型分析与适配；仿真不替代性能实测，量化工具适配不等于vLLM实现支持。
metadata:
  workbench_role: domain_entry
  workbench_domain: model_engineering
---

# 模型分析与适配领域

遵循[根规则](../../../AGENTS.md)和[分层协作](../../../docs/guides/skill-routing.md)。复用目标/授权与已有材料；按模型结构、参数/KV/状态缓存、并行/量化和实际框架支持检索知识，进入新子目标时补查。

| 交付目标 | 方法与必要判断 |
|---|---|
| 架构报告、版本比较、参数/KV估算 | [模型分析调用说明](references/model-analysis.md)消费model_analysis；配置/实现交叉核对并独立重算，报告不是部署/精度验收 |
| msModeling吞吐仿真/设备画像 | 仅明确要求时评估msagent对应候选；核对仿真器/输入/单位，结果标仿真而非实测 |
| msModelSlim量化、基础适配与验证 | 按quick-quant/model-adapt/adapter-verification阶段选；高级编排/逐层等仅在本轮需求与前提成立时展开 |
| vLLM/vLLM-Ascend模型实现适配 | 以实际注册/模型接口、加载和目标路径为依据，协作工程/算子/部署/精度；不套用量化工具的同名model-adapt |
| Runtime或算子语言迁移 | 明确迁移层次后选语言/Runtime专题；一般新增模型不默认走CUDA Runtime迁移 |

准确资源与条件见[域内选用](references/scenario-selection.md)及[消费声明](references/upstream-usage.json)。源码、模型资料和支持范围分别记录；来源许可未明确不复制打包原代码/模板。个人历史报告不是必需输入，公开方法应可独立使用。

自有适用方法优先；缺口按发现协议核对原skill、相关脚本和工具后补位，不全量安装各量化/仿真生态。执行工具、模型权重与业务代码变更沿具体授权；更换任务目标由主workflow协调。交付已支持/需适配/未知、实际验证和下一步，静态估算/仿真/真实运行分别报告。
