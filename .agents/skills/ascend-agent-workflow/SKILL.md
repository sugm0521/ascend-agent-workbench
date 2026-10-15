---
name: ascend-agent-workflow
description: 在 ascend-agent-workbench 中把工程目标转为可推进的任务，采用项目特化的 grill-me 查证事实、澄清必要取舍并路由到计划、执行或验收。用于问题定位、模型适配、性能/精度、部署、CI/PR 与源码学习；简单问答不强制建立任务或完整流程。
---

# 工程任务入口

先读 [根规则](../../../AGENTS.md)。设计或规则冲突时定点读 [项目框架](../../../docs/项目框架.md) 对应章节，不全量加载历史与领域 skill。本入口负责目标与推进，领域工具负责实际诊断、运行和验证。

## 确定当前工作

1. 识别用户目标、排除项与已有授权。定位/分析/审查交付证据和建议；修复/解决/优化/实现可在确定范围内修改和验证。不要把定位自动升级为业务修复。
2. 新任务或目标、范围、验收条件发生实质变化时，先复用已确认的信息与授权，再查证代码、日志和环境中可获取的事实；仅对影响目标、方案、授权或验收的未决取舍，按项目特化的 `grill-me` 分轮集中提问并给出推荐。用户明确要求 `grill-me` / `grilling` 时也从本入口执行。已有答复不重问；目标、范围、约束与验收充分时结束澄清并继续。
3. 简单问答直接回答。涉及代码、实验、验证、CI、委派或交接时，用 `docs/templates/` 的适用模板建立或恢复 `tasks/<任务>/`；显式完全只读时不写记录。`任务说明.md` 是唯一状态入口，主 agent 是唯一整合负责人。
4. 恢复先读任务说明与最新交接，核对 owner、`plan_revision`、实际 repo/worktree、SHA、dirty 内容以及底层运行/资源状态。保留原失败；旧证据只能在条件仍一致时复用，不重复未知服务或运行。

任务说明记录稳定 `task_id`、`status`、`owner`、`plan_revision` 和带时区的 `updated_at`，以及目标、授权、验收、基线、阻塞和下一步。目标/计划改变时递增 revision 并写原因。状态定义遵循根规则；缺环境仅阻塞依赖它的步骤。

## 按目标选择能力

先通过 [能力映射](../../../upstream/skill-mapping.md) 和锁定来源找到实际 skill/工具，检查可读、可调用、环境适用后按需加载。映射是常用入口索引；**映射未命中或已有入口覆盖不足时，必须检索已接入依赖仓**；已有入口足够时直接复用。

1. 依据 [source lock](../../../upstream/sources.lock.yaml) 与存在的本机配置定位相关来源的真实路径，先查原仓能力目录/清单，用 `rg` 按任务关键词检索 `SKILL.md` 的 `name`、`description` 及技能目录名，包含 `.agents/` 等隐藏目录。只读取候选摘要，不全量加载所有正文；明确未启用、路径缺失或来源不可读时记录范围与缺口，不自动初始化、安装或升级。
2. 阅读相关候选正文和必要引用，核对任务目标、目标代码/框架、适用范围及工具/环境前提；名称命中不等于适用。沿用项目调用边界和原执行/资源工具，资料可读与可运行分别判断。
3. 找到足以覆盖当前目标的入口后停止扩大检索，在当前任务记录（简单问答在回复中）简记实际检索来源、选用入口与理由；无适用项则报告已查范围和缺口，不把映射未列出当成仓内不存在。

| 目标 | 需要发现的能力 | 交付依据 |
|---|---|---|
| 问题单定位 | 复现、日志、源码与适用 graph/distributed/operator 诊断 | 触发条件、影响范围、根因证据与未确认项 |
| 模型架构报告、版本比较或参数/KVCache 估算 | 按[模型分析调用说明](references/model-analysis.md)读取 model_analysis 的原 skill 与模板 | 固定输入版本、独立计算、对照实际实现；报告与待适配清单不代替运行验证 |
| 模型适配或功能实现 | 实际接口、注册/执行路径、当前测试与运行工具 | 功能、兼容范围及所需集成证据 |
| 服务性能压测、吞吐/延迟、prefix cache 测试 | [ascend-performance-benchmark](../ascend-performance-benchmark/SKILL.md) | 实际请求结果、工作负载、指标与日志；保留既有服务 |
| 其他模型性能分析、profiling 或性能回归 | profiling、memory 与 regression 工具；需要服务负载时使用上述压测入口 | 可比工作负载下端到端指标和资源变化 |
| 模型精度、乱码或复读 | [ascend-model-accuracy](../ascend-model-accuracy/SKILL.md) | 可复现偏差、根因/规避边界与目标场景回归 |
| 手工已有容器独立SSH登录入口 | [ascend-container-ssh](../ascend-container-ssh/SKILL.md) | 实际端口、认证和容器归属及用户访问端的登录结果；托管目标按原契约交接 |
| 算子开发/替换 | 原语义、适用 AscendC 方法与框架运行验证 | 接口/支持范围、正确性、生产场景与集成 |
| 部署 | 按[部署说明](references/service-deployment.md)选择运行方式、准备容器与环境，再调用适用serving/PD或已核对执行入口 | 启动前版本清单与当前目标路径的真实请求 |
| 指定环境复现清单 | [ascend-runtime-snapshot](../ascend-runtime-snapshot/SKILL.md)只读整理当前/历史环境，区分选用与实际加载 | 实际版本/代码/PR/依赖替换、来源和未知项；不自动部署或升级 |
| CI/PR | 当前仓库 workflow、失败 job、提交与 review | 当前 head SHA 的实际终态 |
| 源码学习 | 实际源码；可用时使用 `ascend-source-walkthrough` | 连续调用链、版本与事实/推断边界 |

跨环境部署能力可包括 `ascend-service-deploy`。这两个个人 skill 在其他主机可能不存在：查找可用入口并报告缺口，不把个人绝对路径当作依赖、不假装已加载。找不到能力时可查证源码/现有工具，缺设备或远程入口不编造实测。首次接入或升级分别路由到 init/dependencies，不在业务任务中顺带完整初始化或升级。

明确要求 HCCL alltoallvc 打流或验证打流故障时，使用 [HCCL 轻量通信测试](../ascend-hccl-traffic-test/SKILL.md)。一般分布式问题仍按各 rank 证据诊断，模型吞吐仍按端到端基准验收。

## 推进与反馈

- 需要可独立交付的拆分时用 [planning](../ascend-task-planning/SKILL.md)；明确小任务直接执行，不为了分工固定团队。
- 按授权用 [execution](../ascend-task-execution/SKILL.md) 推进调查/实现/实验；用 [review](../ascend-task-review/SKILL.md) 核查结果与交接。明确评估 skill 候选时用 [skill-candidate-review](../ascend-skill-candidate-review/SKILL.md)，创建/优化用 [skill-development](../ascend-skill-development/SKILL.md)复用评估。
- 关键判断反馈可查证的证据、当前假设、方案理由、风险/替代项和下一步验证；不公开内部逐步思维链。假设推翻、路线改变、精度失败、退化或 CI 归因变化及时说明。
- 默认在确定范围内连续工作，提交、推送、发布前提供可审核结果；沿用已获得的具体授权，不重复确认。改变语义、支持范围、必需验收或扩大授权时准备证据与选项，等待用户决定。

交付前由主 agent 整合证据并更新状态，明确完整完成或阶段结果。完成/中断后的简短回顾只提出有证据的候选，不自动创建公共工具或新 skill。
