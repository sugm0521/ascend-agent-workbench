# 领域入口与能力边界

此映射按 [sources.lock.yaml](sources.lock.yaml) 的三个固定提交核对；升级后重核受影响入口。表中“入口已核对”仅表示文件存在且用途经阅读确认，不代表脚本、MCP、目标环境或联合流程已运行。

领域来源保持只读。先明确业务路径与启用能力，再读取相关 SKILL；目录存在不等于已安装插件或获得远程执行能力。直接引用的 skill 使用其本身相对资源，不能从工作台根目录猜脚本工作目录。

## 本项目补充能力

| 需求 | 入口 | 接入条件与边界 |
|---|---|---|
| HCCL alltoallvc 单机/多机打流 | [ascend-hccl-traffic-test](../.agents/skills/ascend-hccl-traffic-test/SKILL.md) | 复用原运行工具与 MPI/CANN；支持本地 fork、有限诊断及已明确授权的宿主直接路径，不携带大二进制；日志摘要不代替规模/rank 覆盖 |

## workspace：流程与执行

| 需求 | 已核对入口 | 接入条件与边界 |
|---|---|---|
| workspace 布局初始化 | [repo-init](../deps/vllm-ascend-workspace/.agents/skills/repo-init/SKILL.md) | 只在实际布局与计划范围适用时使用；probe 会写持久身份，不能用作纯只读查询 |
| 独立业务版本配对 | [CI pin resolver](../deps/vllm-ascend-workspace/.agents/skills/repo-init/scripts/resolve_vllm_ci_pin.py) | 支持 --vllm-ascend-dir；核实来源与真实 ref，文本解析成功不证明配对通过 |
| 指定业务仓拓扑 | [repo_topology](../deps/vllm-ascend-workspace/.agents/skills/repo-init/scripts/repo_topology.py) | 支持 --repo；configure 会写 remotes，仅用明确的新配置范围；配对后不调用 ensure-main 改回分支 |
| 机器接入与修复 | [machine-management](../deps/vllm-ascend-workspace/.agents/skills/machine-management/SKILL.md) | 目标与既有 provider 明确后按其原 profile/检查入口接入 |
| 隔离会话与代码一致性 | [session-management](../deps/vllm-ascend-workspace/.agents/skills/session-management/SKILL.md)、[remote-code-parity](../deps/vllm-ascend-workspace/.agents/skills/remote-code-parity/SKILL.md) | 复用底层身份与资源，确认实际代码路径；不复制另一套锁或状态 |
| 单机服务 / P-D | [serving](../deps/vllm-ascend-workspace/.agents/skills/vllm-ascend-serving/SKILL.md)、[pd-serving](../deps/vllm-ascend-workspace/.agents/skills/vllm-ascend-pd-serving/SKILL.md) | 管理目标与模型条件满足后执行，真实请求另验收 |
| 模型基准与性能回归 | [benchmark](../deps/vllm-ascend-workspace/.agents/skills/vllm-ascend-benchmark/SKILL.md)、[performance-regression](../deps/vllm-ascend-workspace/.agents/skills/vllm-ascend-performance-regression/SKILL.md) | 可比工作负载、基线与实际环境；算子收益不能替代端到端指标 |
| profiling / memory | [collection](../deps/vllm-ascend-workspace/.agents/skills/ascend-profiling-collection/SKILL.md)、[analysis](../deps/vllm-ascend-workspace/.agents/skills/ascend-profiling-analysis/SKILL.md)、[memory](../deps/vllm-ascend-workspace/.agents/skills/ascend-memory-profiling/SKILL.md) | 按数据和阶段选用；采集要真实环境，分析需可访问 trace/manifest |
| 图模式 / 分布式定位 | [graph-debug](../deps/vllm-ascend-workspace/.agents/skills/vllm-ascend-graph-debug/SKILL.md)、[distributed-debug](../deps/vllm-ascend-workspace/.agents/skills/vllm-ascend-distributed-debug/SKILL.md) | 根据复现和 rank/执行模式证据路由，不泛化为算子问题 |
| 精度与变更验证 | [correctness-validation](../deps/vllm-ascend-workspace/.agents/skills/vllm-ascend-correctness-validation/SKILL.md)、[change-validation](../deps/vllm-ascend-workspace/.agents/skills/vllm-ascend-change-validation/SKILL.md) | reference/标准、真实代码状态和覆盖；静态检查不冒充推理通过 |
| 算子复现 | [operator-debug](../deps/vllm-ascend-workspace/.agents/skills/ascend-operator-debug/SKILL.md) | 已定位算子边界或有明确 reproducer；NPU 用例不在 Mac 本地伪跑 |

外部依赖约束来自 workspace 的 [remote-dev](../deps/vllm-ascend-workspace/.agents/deps/remote-dev.json)、[coordinator](../deps/vllm-ascend-workspace/.agents/deps/coordinator.json) 和 [knowledge kit](../deps/vllm-ascend-workspace/.agents/deps/vaws-knowledge.json) 原声明。remote-dev 是私有运行依赖，coordinator 是执行协议依赖，knowledge kit 是测试依赖；本轮仅核对声明，没有下载或 bootstrap 这些外部提供者。

部分领域工具具有 workspace/session 或固定代码布局前提。对独立 repos/ 不承诺所有工具已适配；若实际入口不能绑定所选代码路径，记录能力缺口并提出最小适配方案，不初始化第二套业务代码。相关 `.agents/knowledge/` 只按任务查询，不全量加载。

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

## 已有个人能力

若当前环境提供 `ascend-source-walkthrough` 或 `ascend-service-deploy`，按实际可读 SKILL 路径复用。它们不是本项目的强制安装依赖，其他主机缺失时不宣称可用；先用已接入来源或说明缺口。CI 工作读取实际业务仓库的 workflow/head/run，不存在能替代当前 CI 证据的静态通用结论。
