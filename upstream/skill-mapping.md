# 领域入口与能力边界

此映射按 [sources.lock.yaml](sources.lock.yaml) 的固定提交核对；升级后重核受影响入口。表中“入口已核对”仅表示文件存在且用途经阅读确认，不代表脚本、MCP、目标环境或联合流程已运行。

本地`deps/`保存固定版本的上游源码，不直接改写；上游作者可继续更新，采用新版按依赖维护流程验证后切换。满足目标、输入、环境与本轮授权时，直接使用原skill流程和脚本/模板/工具；需要写入时用任务/业务目录或可写执行副本，并保留来源差异。目录存在不等于工具已接入。原skill相对资源从其目录解析，不从工作台根猜测。

## 按任务选用与重叠处理

先按任务对象、输入和阶段选一个主流程，再定位原skill及其资源。主流程可以直接来自上游，项目只补目标组织、必要适配与验收；同一阶段无需并行执行多套完整流程。不同阶段可以衔接不同来源，运行沿用当前已绑定的原工具。

表中“现有方法”表示已有项目引用，不是永久优先级；“候选”表示尚需按目标版本、芯片、输入和工具核对，不是长期只能参考。条件及授权满足即可按原流程使用，无需先新建项目skill。来源路径与资源共同确定身份，未列能力仍按发现入口检索。任务保持当前已确认基线，新增或升级来源的采用结论按下述比较更新。

### 任务与维护

| 场景与输入 | 主入口或方法 | 补充条件与范围 |
|---|---|---|
| A01 目标澄清 | 项目workflow组织事实核对和必要澄清；定位：[ascend-agent-workflow](../.agents/skills/ascend-agent-workflow/SKILL.md)（主入口）、[matt/grilling](../deps/matt-pocock-skills/skills/productivity/grilling/SKILL.md)（方法参考） | matt grilling只提供提问方法；已有目标和授权直接复用；不引入上游setup/问卷系统 |
| A02 计划、依赖与交接 | 项目planning/execution/review分别负责计划、推进与验收；定位：[ascend-task-planning](../.agents/skills/ascend-task-planning/SKILL.md)（计划）、[ascend-task-execution](../.agents/skills/ascend-task-execution/SKILL.md)（执行）、[ascend-task-review](../.agents/skills/ascend-task-review/SKILL.md)（验收）、[matt/to-tickets](../deps/matt-pocock-skills/skills/engineering/to-tickets/SKILL.md)（方法参考）、[matt/handoff](../deps/matt-pocock-skills/skills/productivity/handoff/SKILL.md)（方法参考） | matt to-tickets/handoff仅借拆分和交接方法；不另建外部tracker，不并行启用compound完整工作流 |
| A03 Skill评估与开发 | candidate-review决定是否值得改；development实施已授权范围；定位：[ascend-skill-candidate-review](../.agents/skills/ascend-skill-candidate-review/SKILL.md)（评估入口）、[ascend-skill-development](../.agents/skills/ascend-skill-development/SKILL.md)（实施入口） | 外部skill审查器只在特定检查缺口时评估；不因来源增加再建wrapper；不得把评估变成实施 |
| A04 首次接入、安全同步、固定依赖变化 | init负责首次准备，repository-update负责安全同步，dependencies负责固定来源兼容；定位：[ascend-workbench-init](../.agents/skills/ascend-workbench-init/SKILL.md)（首次接入）、[ascend-repository-update](../.agents/skills/ascend-repository-update/SKILL.md)（安全同步）、[ascend-workbench-dependencies](../.agents/skills/ascend-workbench-dependencies/SKILL.md)（依赖维护）、[workspace/repo-init](../deps/vllm-ascend-workspace/.agents/skills/repo-init/SKILL.md)（条件方法） | workspace repo-init仅在原布局和所选能力适用时使用；三者按目标区分，不互相运行完整流程 |

### 环境与部署

| 场景与输入 | 主入口或方法 | 补充条件与范围 |
|---|---|---|
| B01 运行环境与容器复现记录 | 项目runtime-snapshot；定位：[ascend-runtime-snapshot](../.agents/skills/ascend-runtime-snapshot/SKILL.md)（主入口） | 使用当前工具采集实际容器/进程证据；不采用awesome自带默认env_snapshot假设；不重复采集仍有效字段 |
| B02 机器、会话、代码一致性 | 使用当前实际绑定的原执行工具；workspace方法须匹配原后端；定位：[workspace/machine-management](../deps/vllm-ascend-workspace/.agents/skills/machine-management/SKILL.md)（条件方法）、[workspace/session-management](../deps/vllm-ascend-workspace/.agents/skills/session-management/SKILL.md)（条件方法）、[workspace/remote-code-parity](../deps/vllm-ascend-workspace/.agents/skills/remote-code-parity/SKILL.md)（条件方法） | workspace machine/session/code-parity可作契约参考；awesome server-management、ascend ssh-dev-suite不是默认替换；不建第二份身份/资源表 |
| B03 手工已有容器独立SSH | 项目container-ssh；定位：[ascend-container-ssh](../.agents/skills/ascend-container-ssh/SKILL.md)（主入口） | 已有托管目标仍走原工具；与宿主登录、普通exec及资产管理分开 |
| B04 模型服务部署与PD | 项目workflow的service-deployment reference组织部署；实际执行依当前工具；定位：[workspace/vllm-ascend-serving](../deps/vllm-ascend-workspace/.agents/skills/vllm-ascend-serving/SKILL.md)（条件方法）、[workspace/vllm-ascend-pd-serving](../deps/vllm-ascend-workspace/.agents/skills/vllm-ascend-pd-serving/SKILL.md)（条件方法） | workspace serving/PD仅用于支持的session/binding路径；ascend vllm-ascend-deploy默认cron和其他inventory不整体采用 |

### 评测与性能

| 场景与输入 | 主入口或方法 | 补充条件与范围 |
|---|---|---|
| C01 服务吞吐、TTFT、TPOT、prefix压测 | 项目performance-benchmark → aisbench_auto_tools_prefix原工具；定位：[ascend-performance-benchmark](../.agents/skills/ascend-performance-benchmark/SKILL.md)（主入口）、[workspace/vllm-ascend-benchmark](../deps/vllm-ascend-workspace/.agents/skills/vllm-ascend-benchmark/SKILL.md)（条件替代） | workspace benchmark仅在负载不适用AISBench时评估；msagent run-aisbench-evaluation主讲数据集精度，不能替换性能压测 |
| C02 端到端推理调优 | 项目inference-optimization；定位：[ascend-inference-optimization](../.agents/skills/ascend-inference-optimization/SKILL.md)（主入口）、[workspace/vllm-ascend-performance-regression](../deps/vllm-ascend-workspace/.agents/skills/vllm-ascend-performance-regression/SKILL.md)（条件方法） | 基线用C01；证据按profiling/显存/算子场景选；regression消费可比结果；不默认执行上游完整调优循环；不以仿真或单算子收益替代模型实测 |
| C03 正式模型数据集精度评测 | workflow组织实际评测器，correctness负责可比性与判定；定位：[workspace/vllm-ascend-correctness-validation](../deps/vllm-ascend-workspace/.agents/skills/vllm-ascend-correctness-validation/SKILL.md)（现有方法）、[msagent/run-aisbench-evaluation](../deps/msagent/skills/benchmark/run-aisbench-evaluation/SKILL.md)（补充候选） | msagent run-aisbench-evaluation可参考任务名和配置选用；awesome ais-bench-eval仅候选；新评测运行器尚未适配；不引入其默认评测机/hosts/task表 |
| C04 Agent/SWE等任务评测 | workflow按实际runner及SWE记录规范组织 | 先核对runner支持，尚无统一依赖入口；awesome广泛触发描述不代表AISBench对所有agent benchmark有执行支持 |
| C05 已有AISBench结果整理 | 现有AISBench证据报告工具与原生评测器 | 异常输出转模型精度场景；不发新请求，不修改官方评分；不是另一套评测runner |

### 模型正确性

| 场景与输入 | 主入口或方法 | 补充条件与范围 |
|---|---|---|
| D01 乱码、复读、空输出与分数退化 | 项目model-accuracy组织问题；awesome诊断/修复手册按阶段参考；定位：[ascend-model-accuracy](../.agents/skills/ascend-model-accuracy/SKILL.md)（主入口）、[awesome_agent_skills/vllm-ascend-accuracy](../deps/awesome-agent-skills/vllm-ascend-accuracy/SKILL.md)（按阶段取手册）、[msagent/precision-debugger](../deps/msagent/skills/accuracy/precision-debugger/SKILL.md)（仅案例资源候选） | msagent precision-debugger只建议消费其references/summary.md的匹配案例；不加载三个完整修复流程；案例需要版本/源码证据，不能直接认定根因 |
| D02 已指向KVCache/FlashAttention数值分叉 | 沿D01任务，定向参考cannbot model-infer-precision-debug；定位：[cannbot/model-infer-precision-debug](../deps/cannbot-skills/model/model-infer-precision-debug/SKILL.md)（专题补充候选） | 其metadata/packed sequence等假设须与目标实现核对；不是所有模型精度问题的默认完整流程 |
| D03 eager正常、graph/replay异常 | workspace graph-debug方法；定位：[workspace/vllm-ascend-graph-debug](../deps/vllm-ascend-workspace/.agents/skills/vllm-ascend-graph-debug/SKILL.md)（现有专题方法） | 项目精度任务保留原始reference与回归；原后端入口兼容另验，不用调试同步改变复现 |
| D04 rank/并行/跨机相关错误 | workspace distributed-debug方法；定位：[workspace/vllm-ascend-distributed-debug](../deps/vllm-ascend-workspace/.agents/skills/vllm-ascend-distributed-debug/SKILL.md)（现有专题方法） | 算子边界明确后进G04；HCCL打流另进H01；通信trace分析不能代替分布式正确性验收 |
| D05 训练NaN、确定性或梯度尖刺 | 按实际症状查msagent accuracy和cannbot model-train专题；定位：[msagent/nan-overflow-detection](../deps/msagent/skills/accuracy/nan-overflow-detection/SKILL.md)（专题候选）、[msagent/deterministic-calculation-analysis](../deps/msagent/skills/accuracy/deterministic-calculation-analysis/SKILL.md)（专题候选）、[msagent/spike-root-cause-analysis](../deps/msagent/skills/accuracy/spike-root-cause-analysis/SKILL.md)（专题候选） | msagent nan-overflow/deterministic/spike分别为不同输入；当前没有项目训练精度统一适配；保持专题候选，不套D01推理流程 |

### Profiling与显存

| 场景与输入 | 主入口或方法 | 补充条件与范围 |
|---|---|---|
| E01 数据采集/框架插桩 | 已有服务按workspace collection方法和当前工具；代码插桩参考msagent采集适配；定位：[workspace/ascend-profiling-collection](../deps/vllm-ascend-workspace/.agents/skills/ascend-profiling-collection/SKILL.md)（现有方法）、[msagent/ascend-profiler-collect-adaption](../deps/msagent/skills/profiler/ascend-profiler-collect-adaption/SKILL.md)（插桩补充候选）、[cannbot/model-infer-profiling](../deps/cannbot-skills/model/model-infer-profiling/SKILL.md)（参数补充候选） | cannbot model-infer-profiling只补目标框架/版本采集参数；先查框架内建开关；已有数据不重采；工具版本参数另核 |
| E02 已有数据完整性/可分析性 | msagent profiler-data-validation作为方法候选；定位：[msagent/ascend-profiler-data-validation](../deps/msagent/skills/profiler/ascend-profiler-data-validation/SKILL.md)（方法候选） | 只检查影响当前分析的产物；不因缺可选文件全量重采 |
| E03 整体报告、step/layer与跨rank对齐 | workspace profiling-analysis方法/适用解析入口；定位：[workspace/ascend-profiling-analysis](../deps/vllm-ascend-workspace/.agents/skills/ascend-profiling-analysis/SKILL.md)（现有主方法）、[ascend_agent_skills/ascend-profiling-anomaly](../deps/ascend-agent-skills/skills/ascend-profiling-anomaly/SKILL.md)（专题补充候选）、[msagent/msagent-profiler-breakdown](../deps/msagent/skills/profiler/msagent-profiler-breakdown/SKILL.md)（DB拆解候选） | ascend-profiling-anomaly补空泡、等待锚点或trace结构；msagent breakdown补DB场景拆解；仅补原报告缺口，不同时产出多套互不一致完整报告 |
| E04 DB schema/SQL精确查询 | msagent DB explorer方法候选；定位：[msagent/ascend-profiler-db-explorer](../deps/msagent/skills/profiler/ascend-profiler-db-explorer/SKILL.md)（方法候选） | 须确认schema与安全只读查询通道；其“唯一首先触发”不扩大到所有性能任务；MCP未验不声称可执行 |
| E05 DB集合通信等待/带宽/快慢rank归因 | msagent communication-analysis方法候选；定位：[msagent/ascend-communication-analysis](../deps/msagent/skills/profiler/ascend-communication-analysis/SKILL.md)（方法候选） | 缺少DB时仍可按workspace现有产物方法分析；当前该方法P2P覆盖不完整；仅高耗时不能证明链路瓶颈 |
| E06 计算热点、Host调度与CPU绑核 | 按证据分别选msagent computation、schedule、cpu-binding专题；定位：[msagent/ascend-computation-analysis](../deps/msagent/skills/profiler/ascend-computation-analysis/SKILL.md)（计算专题候选）、[msagent/ascend-schedule-analysis](../deps/msagent/skills/profiler/ascend-schedule-analysis/SKILL.md)（调度专题候选）、[msagent/mindstudio-cpu-binding](../deps/msagent/skills/profiler/mindstudio-cpu-binding/SKILL.md)（绑核专题候选） | 只加载与瓶颈判断有关的专题；不能三个全部跑一遍；优化须回归目标负载 |
| E07 vLLM服务HBM权重/KV/HCCL拆分 | workspace memory-profiling方法；定位：[workspace/ascend-memory-profiling](../deps/vllm-ascend-workspace/.agents/skills/ascend-memory-profiling/SKILL.md)（现有方法） | 按实际服务和当前工具取证；不以训练/GE内存数据替代vLLM组件证据 |
| E08 msMemScope dump、泄漏/OOM | msagent memory-analysis方法候选；定位：[msagent/memory-analysis](../deps/msagent/skills/profiler/memory-analysis/SKILL.md)（方法候选） | 已有dump先解读；无数据时才评估采集；与E07数据契约不同；OOM不是必然使用msMemScope |
| E09 两个集群/Prof数据集对比 | msagent cluster-compare/prof-compare方法候选；定位：[msagent/ascend-cluster-compare](../deps/msagent/skills/profiler/ascend-cluster-compare/SKILL.md)（集群对比候选）、[msagent/ascend-prof-compare](../deps/msagent/skills/profiler/ascend-prof-compare/SKILL.md)（Prof对比候选） | 先对齐工作负载、采样窗口和schema；GPU/NPU或跨版本不等价的窗口不能强行作因果比较 |

### 模型分析与适配

| 场景与输入 | 主入口或方法 | 补充条件与范围 |
|---|---|---|
| F01 模型架构、参数/KVCache估算 | workflow model-analysis reference → model_analysis原资源；定位：[model_analysis/ascend-model-analysis](../deps/model-analysis/skills/ascend-model-analysis/SKILL.md)（现有方法） | 源码和配置作为事实源，独立重算；原许可未明确；不把估算报告当部署/精度验收 |
| F02 性能仿真与设备画像 | 明确要求仿真时查msagent msModeling专题；定位：[msagent/msmodeling-throughput-optimizer-executor](../deps/msagent/skills/modeling/msmodeling-throughput-optimizer-executor/SKILL.md)（仿真候选） | 仿真器与配置另验；不是C01/C02实测吞吐的替代；当前仅发现候选 |
| F03 msModelSlim快速量化/基础适配 | 按已明确目标选quick-quant或model-adapt方法候选；adapter-verification负责对应验证；定位：[msagent/msmodelslim-quick-quant](../deps/msagent/skills/quantizer/msmodelslim-quick-quant/SKILL.md)（量化用法候选）、[msagent/msmodelslim-model-adapt](../deps/msagent/skills/quantizer/msmodelslim-model-adapt/SKILL.md)（适配候选）、[msagent/msmodelslim-adapter-verification](../deps/msagent/skills/quantizer/msmodelslim-adapter-verification/SKILL.md)（验证候选） | 逐层量化仅在基础适配后且内存不足或明确要求时启用；没有项目运行适配证明；不是vLLM模型实现适配 |
| F04 自动量化调优、DiT或EP扩展 | 只在明确对应目标时评估msagent quantizer系列 | 可借具体配置/量化/评测叶子步骤；不默认采用orchestrator的完整任务/安装循环 |
| F05 模型/Runtime迁移 | 先分模型实现、算子语言或Runtime层；按接口查cannbot/ascend专题；定位：[cannbot/runtime_migration](../deps/cannbot-skills/runtime/runtime_migration/SKILL.md)（Runtime层候选） | CUDA Runtime迁移明确使用cannbot runtime_migration的范围；通用model-migration不是所有vLLM模型新增实现的默认模板 |

### 算子与编译

| 场景与输入 | 主入口或方法 | 补充条件与范围 |
|---|---|---|
| G01 AscendC设计/tiling/实现 | cannbot tiling/实现方法；按实际接口开发；定位：[cannbot/ascendc-tiling-design](../deps/cannbot-skills/ops/ascendc-tiling-design/SKILL.md)（现有方法）、[cannbot/torch-ascendc-op-extension](../deps/cannbot-skills/ops/torch-ascendc-op-extension/SKILL.md)（现有集成方法） | ascend_agent_skills设计/代码生成在现有方法缺口时评估；不并行加载多个完整operator-dev流程 |
| G02 Triton开发/精度/性能 | 先按现有workspace Triton流程与目标环境适用性选择；定位：[workspace/ascend-triton-workflow](../deps/vllm-ascend-workspace/.agents/skills/ascend-triton-workflow/SKILL.md)（条件方法）、[cannbot/triton-op-designer](../deps/cannbot-skills/ops/triton-op-designer/SKILL.md)（设计补充候选） | cannbot sketch/优化及ascend Triton系列作为特定缺口的候选；原工具后端不匹配时仅借方法，不新建另一套运行状态 |
| G03 CATLASS、TileLang、PyPTO、SHMEM实现 | 按实际语言分别参考cannbot对应方法；定位：[cannbot/catlass-op-design](../deps/cannbot-skills/ops/catlass-op-design/SKILL.md)（CATLASS候选）、[cannbot/tilelang-op-develop](../deps/cannbot-skills/ops/tilelang-op-develop/SKILL.md)（TileLang候选）、[cannbot/pypto-op-develop](../deps/cannbot-skills/ops/pypto-op-develop/SKILL.md)（PyPTO候选）、[cannbot/shmem-ops-design](../deps/cannbot-skills/plugins-community/shmem-ops-generator/skills/shmem-ops-design/SKILL.md)（SHMEM设计候选） | ascend_agent_skills同语言系列作条件候选，msagent提供跨语言profiling专题；语言/芯片/阶段不匹配不得混用；SHMEM编排器只取明确选中的叶子步骤 |
| G04 算子数值误差与独立复现 | workspace operator-debug组织独立reference，AscendC用cannbot precision-debug；定位：[workspace/ascend-operator-debug](../deps/vllm-ascend-workspace/.agents/skills/ascend-operator-debug/SKILL.md)（现有方法）、[cannbot/ascendc-precision-debug](../deps/cannbot-skills/ops/ascendc-precision-debug/SKILL.md)（现有方法） | 其他语言按对应精度方法发现；不套模型输出质量流程；不自行放宽reference阈值 |
| G05 算子profiling、优化和msOpProf解释 | 一般AscendC优化用cannbot perf-optimize；明确msOpProf数据读msagent专题；定位：[cannbot/ascendc-perf-optimize](../deps/cannbot-skills/ops/ascendc-perf-optimize/SKILL.md)（现有方法）、[msagent/msot-msopprof-operator-profiler](../deps/msagent/skills/operator/msot-msopprof-operator-profiler/SKILL.md)（工具专题候选） | msagent ops-performance-tuning完整循环仅作条件候选；device/simulator和目标SoC先分清；编译/工具前提另验 |
| G06 内存/竞争检测、coredump与软同步 | msagent mssanitizer/msdebug专题为方法候选；定位：[msagent/mssanitizer-basic-usage](../deps/msagent/skills/operator/mssanitizer-basic-usage/SKILL.md)（检测候选）、[msagent/msdebug-basic-usage](../deps/msagent/skills/operator/msdebug-basic-usage/SKILL.md)（调试候选） | ascendc-mssanitizer及cannbot crash工具按具体芯片/产物发现；工具安装/插桩不是读取skill的自动副作用 |

### 通信与知识

| 场景与输入 | 主入口或方法 | 补充条件与范围 |
|---|---|---|
| H01 HCCL打流与环境 | 项目alltoallvc打流入口；其他集合操作查ascend hccl-test；定位：[ascend-hccl-traffic-test](../.agents/skills/ascend-hccl-traffic-test/SKILL.md)（主入口）、[ascend_agent_skills/hccl-test](../deps/ascend-agent-skills/skills/hccl-test/SKILL.md)（其他集合操作候选）、[cannbot/hccl-env-check](../deps/cannbot-skills/communication/hccl-env-check/SKILL.md)（环境补充候选） | cannbot hccl-env用于环境专题；alltoallvc与AllReduce/AllGather不是相同测试覆盖，msagent通信trace不是打流验收 |
| H02 工程知识收录/复查 | 项目knowledge-curation负责当前私有库和证据流程；定位：[ascend-knowledge-curation](../.agents/skills/ascend-knowledge-curation/SKILL.md)（主入口）、[compound_engineering/ce-compound](../deps/compound-engineering/skills/ce-compound/SKILL.md)（现有方法参考）、[compound_engineering/ce-compound-refresh](../deps/compound-engineering/skills/ce-compound-refresh/SKILL.md)（现有方法参考） | compound ce-compound/refresh仅提供归纳方法；不引入workspace正式知识库或CE docs_root作第二份正文 |
| H03 CANN API/算子领域知识查询 | cannbot knowledge-query及原领域知识源；定位：[cannbot/knowledge-query](../deps/cannbot-skills/plugins-community/cannbot-knowledge/skills/knowledge-query/SKILL.md)（现有领域查询方法） | 与H02工程经验库互补；只取本次问题相关字段；原工具/API可调用性另验 |

### 审查与交付

| 场景与输入 | 主入口或方法 | 补充条件与范围 |
|---|---|---|
| I01 代码/CI/PR审查 | 项目review和实际diff/workflow/check证据组织验收；定位：[cannbot/ascendc-code-review](../deps/cannbot-skills/ops/ascendc-code-review/SKILL.md)（现有语言方法）、[matt/code-review](../deps/matt-pocock-skills/skills/engineering/code-review/SKILL.md)（审查候选）、[compound_engineering/ce-code-review](../deps/compound-engineering/skills/ce-code-review/SKILL.md)（审查候选） | 按语言选择cannbot代码审查，matt code-review/compound ce-code-review只作条件方法；不因选审查方法自动启用commit/push/PR文案写回 |
| I02 文档可用性审查 | msagent document-ux-review仅在明确文档体验任务时评估；定位：[msagent/document-ux-review](../deps/msagent/skills/minos/document-ux-review/SKILL.md)（方法候选） | 与代码缺陷review区分；跟文档运行命令仍按本轮执行范围；不默认部署 |
| I03 周报与周期回顾 | 项目weekly-report；定位：[ascend-weekly-report](../.agents/skills/ascend-weekly-report/SKILL.md)（主入口） | 工程知识写入与业务验收仍分开；不引入上游日报或任务状态表 |

### 其他专门能力

| 场景与输入 | 主入口或方法 | 补充条件与范围 |
|---|---|---|
| Z01 CV/训练框架迁移、RL/投机训练、K8s、驱动安装等 | 来源库存保留可发现能力，尚无本项目固定采用关系 | 用户实际目标落入该范围时，核对对应候选正文、平台、接口和副作用后选择；不因依赖已下载就自动纳入vLLM业务流程，也不无依据删除这些能力 |

日常任务找到适用入口就停止扩大检索；依赖升级审查则同时比较已有能力的增强和修复，即使旧方法还能工作也评估归因质量、输入覆盖、报告、步骤成本或实测效果。输入/阶段相同表示重叠，不足以证明冗余。验证支持改进时可直接采用上游或替换主方法，并清理已被覆盖的本地适配；未验证则保留基线和具体缺口，不因名字或版本更新自动切换。方法、脚本接口与当前后端分别核实，不把缺工具误报成原能力不可用。

上游宽泛触发词、“必须首先/唯一使用”、自动安装、外部tracker、默认机器/cron、提交与日志流程不覆盖本项目选定范围。只引用案例、schema或某阶段方法时，不带入上游整套编排和状态。后面的来源表用于定位与约束，不另定义竞争的默认优先级。

## 依赖能力发现入口

映射只列常用、已核对的调用入口，不是依赖能力白名单。先检索工程知识与已有领域入口；映射未命中、覆盖不足，或新报错、反复失败、调查转向暴露能力缺口时，按下表查相关来源。相关来源无命中再扩大到其他已登记来源，找到适用方案即停止；已有检索在相同版本与问题范围内仍适用时复用。

实际路径先按本机 `dependencies.<id>.path` 定位，缺省按 lock；显式禁用、未准备或不可读的来源报告缺口，不自动安装、启用或升级。未决定启用的现有资料可只读识别，遵循配置约定。

| lock id | 优先检索的原仓目录或清单 | 主要检索范围 |
|---|---|---|
| workspace | [README](../deps/vllm-ascend-workspace/README.md)、`.agents/skills/` | vLLM-Ascend 服务、图、分布式、精度、profiling 与执行协议 |
| cannbot | [功能清单](../deps/cannbot-skills/docs/feature-list.md)，再按原清单定位 `ops/`、`model/`、`runtime/`、`communication/` 等目录 | AscendC、优化、精度、同步及领域知识 |
| matt | [README](../deps/matt-pocock-skills/README.md)、`skills/` | 澄清、拆分、实现、交接等工程方法 |
| model_analysis | [README](../deps/model-analysis/README.md)、`skills/` | 模型架构、参数与缓存估算；许可边界仍适用 |
| aisbench_auto_tools_prefix | [README](../deps/aisbench-auto-tools-prefix/README.md)，再查原脚本帮助与接口 | 性能压测与公共前缀工具；无 SKILL 的来源也按接口检索 |
| awesome_agent_skills | [README](../deps/awesome-agent-skills/README.md)、各主题 `SKILL.md` | 精度诊断及其他候选能力；项目精度适配已明确，原工具按版本和任务核对前提，其余保持可发现 |
| compound_engineering | [README](../deps/compound-engineering/README.md)、`skills/` | 知识归纳、复查及其他工程方法；已有知识调用边界不变 |
| ascend_agent_skills | [README 能力索引](../deps/ascend-agent-skills/README.md)、`skills/` | AscendC、Catlass、Triton、迁移、profiling、环境、推理、测试与ATB；按专题选用原Skill，工具与执行前提未全仓验收 |
| msagent | [README](../deps/msagent/README.md)、[Skill 清单](../deps/msagent/skills/README.md)、`skills/`、[外部接入指南](../deps/msagent/docs/zh/user_guide/integration-guide.md) | profiling、通信/计算/显存、精度、量化与算子调优；已核对资料与入口，原脚本/MCP按任务核对依赖、输入与平台 |

先用 `rg --files --hidden -g '!**/.git/**'` 确认候选目录与 `SKILL.md`，再按组件、报错、症状及中英文近义词检索名称/description，命中后才读正文及必要 references；若标题摘要不足，再定向查相关 references、文档或脚本接口。不要全量加载所有正文，也不默认联网搜索未登记生态仓。

发现未映射能力后，核对固定提交、芯片、框架、输入和工具前提，简记检索来源、关键词、选用理由及缺口。只读方法引用不等于工具已兼容；安装、执行、运行体系适配和依赖版本升级分别按实际任务授权处理。确有重复使用价值时再评估新增映射或项目 skill，不自动复制或安装上游 skill，不引入第二套任务与资源状态。

### 未适配能力的接入提醒

实际任务发现有价值的未适配能力时，在任务反馈或交付中主动说明来源及具体 skill/工具、能解决的当前问题、目前可只读参考还是已有适用执行入口。需要适配才能执行时，同时给出具体缺口、最小接入范围和验证方案，请用户决定是否实施；这不阻止继续完成已授权且不依赖该适配的工作，不因名称命中就提出接入。

同一能力多次实际使用时，在任务回顾中评估是否值得加入常用映射或封装项目 skill，并说明重复使用的依据及维护成本。只读参考本身不自动要求新增 skill 或升级版本。

提醒、候选评估与用户决定留在当前本机任务；已确认需要实施的工作台/skill接入纳入开发计划，实际改动和原因进入开发记录，工程经验按知识流程处理，不单建公开候选目录或工程知识待办。提出建议前按来源和能力查阅已有相关记录及决定；同一缺口、证据和用户决定未变化时不重复提醒，已拒绝或暂缓的候选仅在出现实质新证据或条件变化时重新提出，并说明变化。未找到跨任务记录时说明已查范围，不声称已全局去重。不新增定时提醒、候选数据库或自动安装流程。

## 项目记录与辅助入口

业务主入口按前表选用；以下仅定位记录与辅助工具。

| 需求 | 入口 | 接入条件与边界 |
|---|---|---|
| 已保存及已登记服务器的可达性快照 | [init 保存目标发现](../.agents/skills/ascend-workbench-init/references/operations.md#保存目标与-npu-接入)、[服务器总表](../docs/guides/task-records.md#服务器可达性总表) | 有界只读查询；旧/新管理来源分别读取，不创建另一套注册/租约，不从 SSH 成功推断设备可用 |
| 正式性能、精度及 SWE 数据集评测登记 | [三类测试表](../docs/guides/task-records.md#三类正式测试总表)、[手动测试接手](../docs/guides/task-records.md#接手手动测试) | 三类字段独立，实际工具/runner决定原生指标；正式手动测试缺项先补登记，调参排障留任务，不声明 AISBench 覆盖 SWE 执行 |
| 算子开发进度和完整运行日志 | [共用记录规范](../docs/guides/task-records.md#算子开发进度与运行日志) | 原领域方法/工具执行，上层关联进度与逐轮完整日志；不自动建第二状态源或委派 |

## workspace：流程与执行

| 需求 | 已核对入口 | 接入条件与边界 |
|---|---|---|
| workspace 布局初始化 | [repo-init](../deps/vllm-ascend-workspace/.agents/skills/repo-init/SKILL.md) | 只在实际布局与计划范围适用时使用；probe 会写持久身份，不能用作纯只读查询 |
| 独立业务版本配对 | [CI pin resolver](../deps/vllm-ascend-workspace/.agents/skills/repo-init/scripts/resolve_vllm_ci_pin.py) | 支持 --vllm-ascend-dir；核实来源与真实 ref，文本解析成功不证明配对通过 |
| 指定业务仓拓扑 | [repo_topology](../deps/vllm-ascend-workspace/.agents/skills/repo-init/scripts/repo_topology.py) | 支持 --repo；configure 会写 remotes，仅用明确的新配置范围；配对后不调用 ensure-main 改回分支 |
| 机器接入与修复 | [machine-management](../deps/vllm-ascend-workspace/.agents/skills/machine-management/SKILL.md) | 目标与既有 provider 明确后按其原 profile/检查入口接入 |
| 隔离会话与代码一致性 | [session-management](../deps/vllm-ascend-workspace/.agents/skills/session-management/SKILL.md)、[remote-code-parity](../deps/vllm-ascend-workspace/.agents/skills/remote-code-parity/SKILL.md) | 复用底层身份与资源，确认实际代码路径；不复制另一套锁或状态 |
| 单机服务 / P-D | [serving](../deps/vllm-ascend-workspace/.agents/skills/vllm-ascend-serving/SKILL.md)、[pd-serving](../deps/vllm-ascend-workspace/.agents/skills/vllm-ascend-pd-serving/SKILL.md) | 管理目标与模型条件满足后执行，真实请求另验收 |
| 模型基准与性能回归 | [benchmark](../deps/vllm-ascend-workspace/.agents/skills/vllm-ascend-benchmark/SKILL.md)、[performance-regression](../deps/vllm-ascend-workspace/.agents/skills/vllm-ascend-performance-regression/SKILL.md) | 服务压测先走上述AISBench工具；原benchmark用于不适用的工作负载，regression负责可比对照；算子收益不能替代端到端指标 |
| profiling / memory | [collection](../deps/vllm-ascend-workspace/.agents/skills/ascend-profiling-collection/SKILL.md)、[analysis](../deps/vllm-ascend-workspace/.agents/skills/ascend-profiling-analysis/SKILL.md)、[memory](../deps/vllm-ascend-workspace/.agents/skills/ascend-memory-profiling/SKILL.md) | 按数据和阶段选用；采集要真实环境，分析需可访问 trace/manifest |
| 图模式 / 分布式定位 | [graph-debug](../deps/vllm-ascend-workspace/.agents/skills/vllm-ascend-graph-debug/SKILL.md)、[distributed-debug](../deps/vllm-ascend-workspace/.agents/skills/vllm-ascend-distributed-debug/SKILL.md) | 根据复现和 rank/执行模式证据路由，不泛化为算子问题 |
| 精度与变更验证 | [correctness-validation](../deps/vllm-ascend-workspace/.agents/skills/vllm-ascend-correctness-validation/SKILL.md)、[change-validation](../deps/vllm-ascend-workspace/.agents/skills/vllm-ascend-change-validation/SKILL.md) | reference/标准、真实代码状态和覆盖；静态检查不冒充推理通过 |
| 算子复现 | [operator-debug](../deps/vllm-ascend-workspace/.agents/skills/ascend-operator-debug/SKILL.md) | 已定位算子边界或有明确 reproducer；NPU 用例不在 Mac 本地伪跑 |

外部依赖约束来自 workspace 的 [remote-dev](../deps/vllm-ascend-workspace/.agents/deps/remote-dev.json)、[coordinator](../deps/vllm-ascend-workspace/.agents/deps/coordinator.json) 和 [knowledge kit](../deps/vllm-ascend-workspace/.agents/deps/vaws-knowledge.json) 原声明。remote-dev 是私有运行依赖，coordinator 是执行协议依赖，knowledge kit 是测试依赖；本轮仅核对声明，没有下载或 bootstrap 这些外部提供者。

部分领域工具具有 workspace/session 或固定代码布局前提。对独立 repos/ 不承诺所有工具已适配；若实际入口不能绑定所选代码路径，记录能力缺口并提出最小适配方案，不初始化第二套业务代码。相关 `.agents/knowledge/` 只按任务查询，不全量加载。

## 运行体系与执行入口

仅在调用实际执行入口或复用已有结果时区分下列契约；按当前工具发现、实际绑定及固定版本说明判断，不把某台机器的接入方式当作其他机器的默认配置。资料可读、JSON可生成不代表执行后端兼容。

| 当前目标 | 可用路径与范围 | 不满足时如何处理 |
|---|---|---|
| 已有可达HTTP服务，只做性能压测 | `ascend-performance-benchmark`在请求端运行AISBench，记录实际服务与运行身份；不要求为压测另建旧session | 服务或客户端缺项按原职责补齐，不自行重启服务 |
| 已有合法VAWS ready session | 在该版本支持范围内使用原serving、benchmark、profiling等session入口，保留原代码一致性及资源机制 | 缺session或前置条件时报告缺口，不能拿其他体系的绑定值代替 |
| MindIE或prepared-runtime的task/binding/execution | 生命周期与执行沿用当前已接入原工具。serving原文已把pool binding与legacy wrapper分开；是否有兼容的profiling、基准或精度执行入口需按实际工具接口确认 | 当前映射中的部分benchmark/profiling脚本仍只解析旧session；未有兼容入口时标待适配，可引用方法，不直接运行旧wrapper或重复分配资源 |
| 已有测量、trace或诊断事件，只需离线处理 | 仅复用输入契约确实满足的解析、比较或计算部分。AISBench与回归按[交接约定](../.agents/skills/ascend-performance-benchmark/references/aisbench-auto-tools.md#与性能回归工具交接)处理；纯方法参考不承诺所有子命令都可离线运行 | 工具仍要求session解析或实测观测而材料不满足时，保留分析范围或缺口，不伪造session/观测，也不为离线分析申请资源 |

旧 `vllm-ascend-benchmark`、profiling collection/analysis 的session解析不能由新binding透明替代；performance-regression的执行流程仍调用该benchmark。新体系可通过其原执行工具消费适用方法，但本映射没有实现这些旧wrapper的MindIE适配。精度/graph/distributed的证据处理同样先核对输入契约，原始运行与采集仍归当前工具。缺口只阻塞相关调用，不触发整套初始化、依赖升级、裸SSH绕行或第二套状态系统。

## cannbot：AscendC 方法与工具

| 需求 | 已核对入口 | 边界 |
|---|---|---|
| Tiling 与实现设计 | [tiling-design](../deps/cannbot-skills/ops/ascendc-tiling-design/SKILL.md) | 结合原接口、芯片与形状；设计结果不等于已编译运行 |
| profiling / 空泡优化 | [perf-optimize](../deps/cannbot-skills/ops/ascendc-perf-optimize/SKILL.md) | 使用实际数据与适用的卡间/核间/核内阶段，不把流水空白直接当根因 |
| 精度问题 | [precision-debug](../deps/cannbot-skills/ops/ascendc-precision-debug/SKILL.md) | reference、误差与输入先明确，不放宽阈值掩盖问题 |
| 同步与代码复核 | [sync-audit](../deps/cannbot-skills/ops/ascendc-sync-audit/SKILL.md)、[code-review](../deps/cannbot-skills/ops/ascendc-code-review/SKILL.md) | 审查结论需证据；额外测试来源按实际需求准备 |
| UT 与 PTA 集成 | [ut-develop](../deps/cannbot-skills/ops/ascendc-ut-develop/SKILL.md)、[torch-extension](../deps/cannbot-skills/ops/torch-ascendc-op-extension/SKILL.md) | UT 与集成各自验收；PTA 入口以可构建运行的算子工程为前提 |

更多入口从其 [功能清单](../deps/cannbot-skills/docs/feature-list.md) 按实际任务查找。完整插件安装可能引入外部仓库、Node 或其他工具；不运行全量安装器作为读取 SKILL 的前提，也不把读取资料称作插件已安装。

当前 [子模块声明](../deps/cannbot-skills/.gitmodules) 中 sync-audit tests 是针对性测试来源，保持未初始化，相关测试才接入。其他脚本/skill 的隐式工具与环境依赖也需在实际使用时检查；本映射不是全生态兼容验证。

## Matt Pocock：按需提炼方法

| 方法 | 来源 | 上层采用方式 |
|---|---|---|
| 需求澄清 | [grill-me](../deps/matt-pocock-skills/skills/productivity/grill-me/SKILL.md) → [grilling](../deps/matt-pocock-skills/skills/productivity/grilling/SKILL.md) | 查事实、分轮处理有影响的未知决策；不强制无限采访，已有明确授权即可推进 |
| 任务拆分 | [to-tickets](../deps/matt-pocock-skills/skills/engineering/to-tickets/SKILL.md) | 采用可验证产物与依赖关系；用本地任务/assignment，不自动创建远端 issue 或 tracker |
| 从说明到实现 | [implement-spec](../deps/matt-pocock-skills/skills/engineering/implement-spec/SKILL.md) | 结合任务范围和验证标准，不强制每任务 TDD、容器或固定团队 |
| 中断与交接 | [handoff](../deps/matt-pocock-skills/skills/productivity/handoff/SKILL.md) | 简洁记录现状、证据和下一步，以任务文件为权威状态 |

上层 skill 独立编写，仅提炼这些方法，按本项目授权/工具/记录格式适配。来源里的 Skill 工具语法和安装前提不能直接假定在当前会话可用；也不复制其广泛触发范围。

## model_analysis：模型架构与报告方法（可选）

| 需求 | 已核对入口 | 接入条件与边界 |
|---|---|---|
| 新模型架构报告、版本比较、参数/KVCache 及量化并行权重估算 | [ascend-model-analysis](../deps/model-analysis/skills/ascend-model-analysis/SKILL.md)、[报告模板](../deps/model-analysis/skills/ascend-model-analysis/references/css-template.md) | 通过[项目调用说明](../.agents/skills/ascend-agent-workflow/references/model-analysis.md)读取；固定输入，独立重算，对照实际实现，产物进任务目录 |

本来源按本机 `dependencies.model_analysis.enabled` 选用，资料/方法消费不要求全量插件或模型源码导入。原仓无 `.gitmodules` 的两个 gitlink 保持未初始化；全仓许可尚未明确，当前接入为用户授权的本机方法引用，不宣称再分发许可已核实。报告给出分析与待验证项，部署、精度和性能继续走原领域入口。

## awesome-agent-skills：模型精度诊断手册（可选）

| 需求 | 已核对入口 | 接入条件与边界 |
|---|---|---|
| 乱码、复读、空输出与精度分数异常的模型层诊断 | [原精度 skill](../deps/awesome-agent-skills/vllm-ascend-accuracy/SKILL.md)、[诊断手册](../deps/awesome-agent-skills/vllm-ascend-accuracy/references/diagnostic-playbook.md)、[修复手册](../deps/awesome-agent-skills/vllm-ascend-accuracy/references/remediation-playbook.md) | 通过独立项目 skill 的[来源与接入](../.agents/skills/ascend-model-accuracy/references/source-and-tools.md)按需读取；MIT 来源只读，快照/比较/资源与任务状态沿用项目工具，不安装同仓其他 skill 或自动执行原脚本 |

## 已有个人能力

若当前环境提供 `ascend-source-walkthrough` 或 `ascend-service-deploy`，按实际可读 SKILL 路径复用。它们不是本项目的强制安装依赖，其他主机缺失时不宣称可用；先用已接入来源或说明缺口。CI 工作读取实际业务仓库的 workflow/head/run，不存在能替代当前 CI 证据的静态通用结论。

## 工程知识维护：独立入口与只读方法

| 需求 | 入口 | 接入条件与边界 |
|---|---|---|
| 检索、核实、去重、写入或复查任务知识 | [ascend-knowledge-curation](../.agents/skills/ascend-knowledge-curation/SKILL.md) | 知识维护在knowledge/；过期内容保存完整历史与原因；仅检索请求不自动写入，Git发布由每日流程或具体授权统一处理 |
| 已验证问题的长期经验与旧知识复查方法 | [ce-compound](../deps/compound-engineering/skills/ce-compound/SKILL.md)、[ce-compound-refresh](../deps/compound-engineering/skills/ce-compound-refresh/SKILL.md) | EveryInc来源按lock固定；原skill只读参考，项目适配不运行其自动提交、删除、CONCEPTS或整套多agent流程 |

日常Ascend/CANN算子资料查询仍可按现有cannbot knowledge-query/ingest/lint消费领域知识；其OKF、图谱和算子卡片规范不整套迁入任务知识库。每日任务按[同步说明](../docs/guides/daily-sync.md)调用独立入口，不扩写workflow正文。
