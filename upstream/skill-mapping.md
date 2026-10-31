# 领域索引与依赖能力发现

索引维护入口、细分目录和原资源的定位，不维护另一套执行优先级。领域SKILL及其按需reference拥有场景选择；消费事实见各模块upstream-usage.json，版本由[sources.lock.yaml](sources.lock.yaml)锁定。

## 领域入口

主入口为[ascend-agent-workflow](../.agents/skills/ascend-agent-workflow/SKILL.md)，也可直接启动领域或具体能力，遵循[分层协作](../docs/guides/skill-routing.md)。

| 领域 | 当前入口 |
|---|---|
| 性能 | [ascend-performance](../.agents/skills/ascend-performance/SKILL.md) |
| 模型精度 | [ascend-model-accuracy](../.agents/skills/ascend-model-accuracy/SKILL.md) |
| 算子 | [ascend-operator](../.agents/skills/ascend-operator/SKILL.md) |
| 部署与运行环境 | [ascend-deployment](../.agents/skills/ascend-deployment/SKILL.md) |
| 模型分析与适配 | [ascend-model-engineering](../.agents/skills/ascend-model-engineering/SKILL.md) |
| 通用工程开发与审查 | [ascend-engineering](../.agents/skills/ascend-engineering/SKILL.md) |
| 知识与报告 | [ascend-knowledge-and-report](../.agents/skills/ascend-knowledge-and-report/SKILL.md) |
| 工作台维护 | [ascend-workbench-maintenance](../.agents/skills/ascend-workbench-maintenance/SKILL.md) |

共用组织/执行/验收与运行快照按需复用，不等于额外业务领域。角色metadata不保证客户端调度，实际发现入口由当前接入验证。

## 细分能力目录

45个盘点场景保留为发现目录，不生成45个skill。具体选用与输入前提只在所属领域维护，原仓子技能仍可发现。

| 场景 | 归属 | 方法和原资源定位 |
|---|---|---|
| A01 目标澄清 | [ascend-agent-workflow](../.agents/skills/ascend-agent-workflow/SKILL.md) | [域内选用](../.agents/skills/ascend-agent-workflow/references/scenario-selection.md) |
| A02 计划、依赖与交接 | [ascend-agent-workflow](../.agents/skills/ascend-agent-workflow/SKILL.md) | [域内选用](../.agents/skills/ascend-agent-workflow/references/scenario-selection.md) |
| A03 Skill使用反馈、评估与开发 | [ascend-workbench-maintenance](../.agents/skills/ascend-workbench-maintenance/SKILL.md) | [域内选用](../.agents/skills/ascend-workbench-maintenance/references/scenario-selection.md) |
| A04 首次接入、安全同步、固定依赖变化 | [ascend-workbench-maintenance](../.agents/skills/ascend-workbench-maintenance/SKILL.md) | [域内选用](../.agents/skills/ascend-workbench-maintenance/references/scenario-selection.md) |
| B01 运行环境与容器复现记录 | [ascend-deployment](../.agents/skills/ascend-deployment/SKILL.md) | [域内选用](../.agents/skills/ascend-deployment/references/scenario-selection.md) |
| B02 机器、会话、代码一致性 | [ascend-deployment](../.agents/skills/ascend-deployment/SKILL.md) | [域内选用](../.agents/skills/ascend-deployment/references/scenario-selection.md) |
| B03 手工已有容器独立SSH | [ascend-deployment](../.agents/skills/ascend-deployment/SKILL.md) | [域内选用](../.agents/skills/ascend-deployment/references/scenario-selection.md) |
| B04 模型服务部署与PD | [ascend-deployment](../.agents/skills/ascend-deployment/SKILL.md) | [域内选用](../.agents/skills/ascend-deployment/references/scenario-selection.md) |
| C01 服务吞吐、TTFT、TPOT、prefix压测 | [ascend-performance](../.agents/skills/ascend-performance/SKILL.md) | [域内选用](../.agents/skills/ascend-performance/references/scenario-selection.md) |
| C02 端到端推理调优 | [ascend-performance](../.agents/skills/ascend-performance/SKILL.md) | [域内选用](../.agents/skills/ascend-performance/references/scenario-selection.md) |
| C03 正式模型数据集精度评测 | [ascend-model-accuracy](../.agents/skills/ascend-model-accuracy/SKILL.md) | [域内选用](../.agents/skills/ascend-model-accuracy/references/scenario-selection.md) |
| C04 Agent/SWE等任务评测 | [ascend-engineering](../.agents/skills/ascend-engineering/SKILL.md) | [域内选用](../.agents/skills/ascend-engineering/references/scenario-selection.md) |
| C05 已有AISBench结果整理 | [ascend-performance](../.agents/skills/ascend-performance/SKILL.md) | [域内选用](../.agents/skills/ascend-performance/references/scenario-selection.md) |
| D01 乱码、复读、空输出与分数退化 | [ascend-model-accuracy](../.agents/skills/ascend-model-accuracy/SKILL.md) | [域内选用](../.agents/skills/ascend-model-accuracy/references/scenario-selection.md) |
| D02 已指向KVCache/FlashAttention数值分叉 | [ascend-model-accuracy](../.agents/skills/ascend-model-accuracy/SKILL.md) | [域内选用](../.agents/skills/ascend-model-accuracy/references/scenario-selection.md) |
| D03 eager正常、graph/replay异常 | [ascend-model-accuracy](../.agents/skills/ascend-model-accuracy/SKILL.md) | [域内选用](../.agents/skills/ascend-model-accuracy/references/scenario-selection.md) |
| D04 rank/并行/跨机相关错误 | [ascend-model-accuracy](../.agents/skills/ascend-model-accuracy/SKILL.md) | [域内选用](../.agents/skills/ascend-model-accuracy/references/scenario-selection.md) |
| D05 训练NaN、确定性或梯度尖刺 | [ascend-model-accuracy](../.agents/skills/ascend-model-accuracy/SKILL.md) | [域内选用](../.agents/skills/ascend-model-accuracy/references/scenario-selection.md) |
| E01 数据采集/框架插桩 | [ascend-performance](../.agents/skills/ascend-performance/SKILL.md) | [域内选用](../.agents/skills/ascend-performance/references/scenario-selection.md) |
| E02 已有数据完整性/可分析性 | [ascend-performance](../.agents/skills/ascend-performance/SKILL.md) | [域内选用](../.agents/skills/ascend-performance/references/scenario-selection.md) |
| E03 整体报告、step/layer与跨rank对齐 | [ascend-performance](../.agents/skills/ascend-performance/SKILL.md) | [域内选用](../.agents/skills/ascend-performance/references/scenario-selection.md) |
| E04 DB schema/SQL精确查询 | [ascend-performance](../.agents/skills/ascend-performance/SKILL.md) | [域内选用](../.agents/skills/ascend-performance/references/scenario-selection.md) |
| E05 DB集合通信等待/带宽/快慢rank归因 | [ascend-performance](../.agents/skills/ascend-performance/SKILL.md) | [域内选用](../.agents/skills/ascend-performance/references/scenario-selection.md) |
| E06 计算热点、Host调度与CPU绑核 | [ascend-performance](../.agents/skills/ascend-performance/SKILL.md) | [域内选用](../.agents/skills/ascend-performance/references/scenario-selection.md) |
| E07 vLLM服务HBM权重/KV/HCCL拆分 | [ascend-performance](../.agents/skills/ascend-performance/SKILL.md) | [域内选用](../.agents/skills/ascend-performance/references/scenario-selection.md) |
| E08 msMemScope dump、泄漏/OOM | [ascend-performance](../.agents/skills/ascend-performance/SKILL.md) | [域内选用](../.agents/skills/ascend-performance/references/scenario-selection.md) |
| E09 两个集群/Prof数据集对比 | [ascend-performance](../.agents/skills/ascend-performance/SKILL.md) | [域内选用](../.agents/skills/ascend-performance/references/scenario-selection.md) |
| F01 模型架构、参数/KVCache估算 | [ascend-model-engineering](../.agents/skills/ascend-model-engineering/SKILL.md) | [域内选用](../.agents/skills/ascend-model-engineering/references/scenario-selection.md) |
| F02 性能仿真与设备画像 | [ascend-model-engineering](../.agents/skills/ascend-model-engineering/SKILL.md) | [域内选用](../.agents/skills/ascend-model-engineering/references/scenario-selection.md) |
| F03 msModelSlim快速量化/基础适配 | [ascend-model-engineering](../.agents/skills/ascend-model-engineering/SKILL.md) | [域内选用](../.agents/skills/ascend-model-engineering/references/scenario-selection.md) |
| F04 自动量化调优、DiT或EP扩展 | [ascend-model-engineering](../.agents/skills/ascend-model-engineering/SKILL.md) | [域内选用](../.agents/skills/ascend-model-engineering/references/scenario-selection.md) |
| F05 模型/Runtime迁移 | [ascend-model-engineering](../.agents/skills/ascend-model-engineering/SKILL.md) | [域内选用](../.agents/skills/ascend-model-engineering/references/scenario-selection.md) |
| G01 AscendC设计/tiling/实现 | [ascend-operator](../.agents/skills/ascend-operator/SKILL.md) | [域内选用](../.agents/skills/ascend-operator/references/scenario-selection.md) |
| G02 Triton开发/精度/性能 | [ascend-operator](../.agents/skills/ascend-operator/SKILL.md) | [域内选用](../.agents/skills/ascend-operator/references/scenario-selection.md) |
| G03 CATLASS、TileLang、PyPTO、SHMEM实现 | [ascend-operator](../.agents/skills/ascend-operator/SKILL.md) | [域内选用](../.agents/skills/ascend-operator/references/scenario-selection.md) |
| G04 算子数值误差与独立复现 | [ascend-operator](../.agents/skills/ascend-operator/SKILL.md) | [域内选用](../.agents/skills/ascend-operator/references/scenario-selection.md) |
| G05 算子profiling、优化和msOpProf解释 | [ascend-operator](../.agents/skills/ascend-operator/SKILL.md) | [域内选用](../.agents/skills/ascend-operator/references/scenario-selection.md) |
| G06 内存/竞争检测、coredump与软同步 | [ascend-operator](../.agents/skills/ascend-operator/SKILL.md) | [域内选用](../.agents/skills/ascend-operator/references/scenario-selection.md) |
| H01 HCCL打流与环境 | [ascend-performance](../.agents/skills/ascend-performance/SKILL.md) | [域内选用](../.agents/skills/ascend-performance/references/scenario-selection.md) |
| H02 工程知识收录/复查 | [ascend-knowledge-and-report](../.agents/skills/ascend-knowledge-and-report/SKILL.md) | [域内选用](../.agents/skills/ascend-knowledge-and-report/references/scenario-selection.md) |
| H03 CANN API/算子领域知识查询 | [ascend-operator](../.agents/skills/ascend-operator/SKILL.md) | [域内选用](../.agents/skills/ascend-operator/references/scenario-selection.md) |
| I01 代码/CI/PR审查 | [ascend-engineering](../.agents/skills/ascend-engineering/SKILL.md) | [域内选用](../.agents/skills/ascend-engineering/references/scenario-selection.md) |
| I02 文档可用性审查 | [ascend-engineering](../.agents/skills/ascend-engineering/SKILL.md) | [域内选用](../.agents/skills/ascend-engineering/references/scenario-selection.md) |
| I03 周报与周期回顾 | [ascend-knowledge-and-report](../.agents/skills/ascend-knowledge-and-report/SKILL.md) | [域内选用](../.agents/skills/ascend-knowledge-and-report/references/scenario-selection.md) |
| Z01 CV/训练框架迁移、RL/投机训练、K8s、驱动安装等 | [ascend-engineering](../.agents/skills/ascend-engineering/SKILL.md) | [域内选用](../.agents/skills/ascend-engineering/references/scenario-selection.md) |

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


## 运行体系与执行入口

仅在调用实际执行入口或复用已有结果时区分下列契约；按当前工具发现、实际绑定及固定版本说明判断，不把某台机器的接入方式当作其他机器的默认配置。资料可读、JSON可生成不代表执行后端兼容。

| 当前目标 | 可用路径与范围 | 不满足时如何处理 |
|---|---|---|
| 已有可达HTTP服务，只做性能压测 | `ascend-performance-benchmark`在请求端运行AISBench，记录实际服务与运行身份；不要求为压测另建旧session | 服务或客户端缺项按原职责补齐，不自行重启服务 |
| 已有合法VAWS ready session | 在该版本支持范围内使用原serving、benchmark、profiling等session入口，保留原代码一致性及资源机制 | 缺session或前置条件时报告缺口，不能拿其他体系的绑定值代替 |
| MindIE或prepared-runtime的task/binding/execution | 生命周期与执行沿用当前已接入原工具。serving原文已把pool binding与legacy wrapper分开；是否有兼容的profiling、基准或精度执行入口需按实际工具接口确认 | 当前映射中的部分benchmark/profiling脚本仍只解析旧session；未有兼容入口时标待适配，可引用方法，不直接运行旧wrapper或重复分配资源 |
| 已有测量、trace或诊断事件，只需离线处理 | 仅复用输入契约确实满足的解析、比较或计算部分。AISBench与回归按[交接约定](../.agents/skills/ascend-performance-benchmark/references/aisbench-auto-tools.md#与性能回归工具交接)处理；纯方法参考不承诺所有子命令都可离线运行 | 工具仍要求session解析或实测观测而材料不满足时，保留分析范围或缺口，不伪造session/观测，也不为离线分析申请资源 |

旧 `vllm-ascend-benchmark`、profiling collection/analysis 的session解析不能由新binding透明替代；performance-regression的执行流程仍调用该benchmark。新体系可通过其原执行工具消费适用方法，但本映射没有实现这些旧wrapper的MindIE适配。精度/graph/distributed的证据处理同样先核对输入契约，原始运行与采集仍归当前工具。缺口只阻塞相关调用，不触发整套初始化、依赖升级、裸SSH绕行或第二套状态系统。


## 来源与许可

原来源身份、版本和许可见[来源与许可](来源与许可.md)。目录存在或方法可读不代表工具已适配。上游维护源只读，当前任务的可写副本和产物按原规则处理。
