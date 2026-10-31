# 域内场景与来源选择

从本域SKILL按目标进入，只读取相关行及原资源。表中候选未承诺工具就绪；与当前后端/输入不适用时只保留方法范围，不另建运行状态。实际采用记录在upstream-usage.json，原资源路径按lock/本机配置解析。

| 场景与输入 | 本域方法/原资源定位 | 条件与边界 |
|---|---|---|
| G01 AscendC设计/tiling/实现 | cannbot tiling/实现方法；按实际接口开发；定位：[cannbot/ascendc-tiling-design](../../../../deps/cannbot-skills/ops/ascendc-tiling-design/SKILL.md)（现有方法）、[cannbot/torch-ascendc-op-extension](../../../../deps/cannbot-skills/ops/torch-ascendc-op-extension/SKILL.md)（现有集成方法） | ascend_agent_skills设计/代码生成在现有方法缺口时评估；不并行加载多个完整operator-dev流程 |
| G02 Triton开发/精度/性能 | 先按现有workspace Triton流程与目标环境适用性选择；定位：[workspace/ascend-triton-workflow](../../../../deps/vllm-ascend-workspace/.agents/skills/ascend-triton-workflow/SKILL.md)（条件方法）、[cannbot/triton-op-designer](../../../../deps/cannbot-skills/ops/triton-op-designer/SKILL.md)（设计补充候选） | cannbot sketch/优化及ascend Triton系列作为特定缺口的候选；原工具后端不匹配时仅借方法，不新建另一套运行状态 |
| G03 CATLASS、TileLang、PyPTO、SHMEM实现 | 按实际语言分别参考cannbot对应方法；定位：[cannbot/catlass-op-design](../../../../deps/cannbot-skills/ops/catlass-op-design/SKILL.md)（CATLASS候选）、[cannbot/tilelang-op-develop](../../../../deps/cannbot-skills/ops/tilelang-op-develop/SKILL.md)（TileLang候选）、[cannbot/pypto-op-develop](../../../../deps/cannbot-skills/ops/pypto-op-develop/SKILL.md)（PyPTO候选）、[cannbot/shmem-ops-design](../../../../deps/cannbot-skills/plugins-community/shmem-ops-generator/skills/shmem-ops-design/SKILL.md)（SHMEM设计候选） | ascend_agent_skills同语言系列作条件候选，msagent提供跨语言profiling专题；语言/芯片/阶段不匹配不得混用；SHMEM编排器只取明确选中的叶子步骤 |
| G04 算子数值误差与独立复现 | workspace operator-debug组织独立reference，AscendC用cannbot precision-debug；定位：[workspace/ascend-operator-debug](../../../../deps/vllm-ascend-workspace/.agents/skills/ascend-operator-debug/SKILL.md)（现有方法）、[cannbot/ascendc-precision-debug](../../../../deps/cannbot-skills/ops/ascendc-precision-debug/SKILL.md)（现有方法） | 其他语言按对应精度方法发现；不套模型输出质量流程；不自行放宽reference阈值 |
| G05 算子profiling、优化和msOpProf解释 | 一般AscendC优化用cannbot perf-optimize；明确msOpProf数据读msagent专题；定位：[cannbot/ascendc-perf-optimize](../../../../deps/cannbot-skills/ops/ascendc-perf-optimize/SKILL.md)（现有方法）、[msagent/msot-msopprof-operator-profiler](../../../../deps/msagent/skills/operator/msot-msopprof-operator-profiler/SKILL.md)（工具专题候选） | msagent ops-performance-tuning完整循环仅作条件候选；device/simulator和目标SoC先分清；编译/工具前提另验 |
| G06 内存/竞争检测、coredump与软同步 | msagent mssanitizer/msdebug专题为方法候选；定位：[msagent/mssanitizer-basic-usage](../../../../deps/msagent/skills/operator/mssanitizer-basic-usage/SKILL.md)（检测候选）、[msagent/msdebug-basic-usage](../../../../deps/msagent/skills/operator/msdebug-basic-usage/SKILL.md)（调试候选） | ascendc-mssanitizer及cannbot crash工具按具体芯片/产物发现；工具安装/插桩不是读取skill的自动副作用 |
| H03 CANN API/算子领域知识查询 | cannbot knowledge-query及原领域知识源；定位：[cannbot/knowledge-query](../../../../deps/cannbot-skills/plugins-community/cannbot-knowledge/skills/knowledge-query/SKILL.md)（领域查询候选） | 与H02工程经验库互补；只取本次问题相关字段；原工具/API可调用性另验 |

方法不足时按[依赖能力发现](../../../../upstream/skill-mapping.md#依赖能力发现入口)查询已登记来源，足够即停。候选选择或上游更新影响本域时核对新增/增强/修复及旧适配，采用后同步消费声明与受影响引用。
