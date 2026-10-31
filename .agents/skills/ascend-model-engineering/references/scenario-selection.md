# 域内场景与来源选择

从本域SKILL按目标进入，只读取相关行及原资源。表中候选未承诺工具就绪；与当前后端/输入不适用时只保留方法范围，不另建运行状态。实际采用记录在upstream-usage.json，原资源路径按lock/本机配置解析。

| 场景与输入 | 本域方法/原资源定位 | 条件与边界 |
|---|---|---|
| F01 模型架构、参数/KVCache估算 | 本领域model-analysis调用说明 → model_analysis原资源；定位：[model_analysis/ascend-model-analysis](../../../../deps/model-analysis/skills/ascend-model-analysis/SKILL.md)（现有方法） | 源码和配置作为事实源，独立重算；原许可未明确；不把估算报告当部署/精度验收 |
| F02 性能仿真与设备画像 | 明确要求仿真时查msagent msModeling专题；定位：[msagent/msmodeling-throughput-optimizer-executor](../../../../deps/msagent/skills/modeling/msmodeling-throughput-optimizer-executor/SKILL.md)（仿真候选） | 仿真器与配置另验；不是C01/C02实测吞吐的替代；当前仅发现候选 |
| F03 msModelSlim快速量化/基础适配 | 按已明确目标选quick-quant或model-adapt方法候选；adapter-verification负责对应验证；定位：[msagent/msmodelslim-quick-quant](../../../../deps/msagent/skills/quantizer/msmodelslim-quick-quant/SKILL.md)（量化用法候选）、[msagent/msmodelslim-model-adapt](../../../../deps/msagent/skills/quantizer/msmodelslim-model-adapt/SKILL.md)（适配候选）、[msagent/msmodelslim-adapter-verification](../../../../deps/msagent/skills/quantizer/msmodelslim-adapter-verification/SKILL.md)（验证候选） | 逐层量化仅在基础适配后且内存不足或明确要求时启用；没有项目运行适配证明；不是vLLM模型实现适配 |
| F04 自动量化调优、DiT或EP扩展 | 只在明确对应目标时评估msagent quantizer系列 | 可借具体配置/量化/评测叶子步骤；不默认采用orchestrator的完整任务/安装循环 |
| F05 模型/Runtime迁移 | 先分模型实现、算子语言或Runtime层；按接口查cannbot/ascend专题；定位：[cannbot/runtime_migration](../../../../deps/cannbot-skills/runtime/runtime_migration/SKILL.md)（Runtime层候选） | CUDA Runtime迁移明确使用cannbot runtime_migration的范围；通用model-migration不是所有vLLM模型新增实现的默认模板 |

方法不足时按[依赖能力发现](../../../../upstream/skill-mapping.md#依赖能力发现入口)查询已登记来源，足够即停。候选选择或上游更新影响本域时核对新增/增强/修复及旧适配，采用后同步消费声明与受影响引用。
