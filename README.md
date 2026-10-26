# vLLM-Ascend Agent 工作台

`ascend-agent-workbench` 用于需求分析、问题定位、模型性能与精度、算子开发、部署、CI/PR 和工程 skill 开发。它负责组织任务和证据，按需使用已有领域 skill 与执行工具。

工作台采用项目规则、项目级 skill、Markdown 任务记录和固定版本的领域依赖。没有自建 agent 平台、资源调度器或 GUI。

## 快速开始

先准备 Git 和有本私仓读取权限的 GitHub 身份，取得工作台：

```bash
git clone https://github.com/sugm0521/ascend-agent-workbench.git
cd ascend-agent-workbench
```

在 Codex 中打开本仓库作为项目主目录，先读取 [AGENTS.md](AGENTS.md)，再按用途选择接入范围：

| 用途 | 准备范围 | 可直接提出的请求 |
|---|---|---|
| 只读资料、源码分析或规划 | 读取所需 skill、资料和可访问源码；采用轻量初始化，列出尚未准备的开发条件 | “使用 $ascend-workbench-init，只做资料与分析准备。” |
| 本地开发与 PR | 标准初始化核对或准备业务仓库、版本组合、Git 作者、GitHub 认证、remotes 与 PR 条件 | “使用 $ascend-workbench-init，准备本地开发与 PR 条件。” |
| 远程实验或 NPU 验证 | 在所选接入范围上补齐实际执行工具、服务器/容器、软件环境和可用设备；按具体任务验收 | “补齐远程 NPU 接入，复用已有工具与 SSH，先核对环境和占用。” |

初始化会先检查上层与各启用下层的要求，汇总必需信息后集中确认，再只补缺失项；已有选择和可用配置直接复用。业务代码默认优先绑定已有 checkout，也可明确选择在 `repos/` 下独立克隆；新准备的版本按目标 vLLM-Ascend 的 CI 声明配对。执行工具与服务器接入单独确定，不要求所有使用者准备 NPU。具体步骤见 [init 操作约定](.agents/skills/ascend-workbench-init/references/operations.md#下层初始化清单)。

克隆只带来工作台规则、skill、工具与依赖指针。业务 checkout、个人身份、客户端接入和运行环境由每位使用者按需准备；缺少远程环境时仍可推进就绪的本地工作。

技能维护在 `.agents/skills/`。若客户端未自动发现，显式读取下表对应的 `SKILL.md`，项目不自动安装全局副本。首次接入后直接描述目标即可，日常任务不重复运行完整初始化。

## 按任务选择入口

例如“定位这个问题单的根因”“优化现有服务的吞吐”“核查模型输出复读”或“实现算子替换”。不确定入口时使用 workflow，明确的小任务可直接使用领域 skill，无需完整采访或多个 agent。

| 类别 | 入口 | 用途 |
|---|---|---|
| 接入与维护 | [init](.agents/skills/ascend-workbench-init/SKILL.md) | 首次接入、补齐缺失配置及初始化报告 |
| 接入与维护 | [dependencies](.agents/skills/ascend-workbench-dependencies/SKILL.md) | 版本核对、相关传递依赖、升级与组合验证 |
| 接入与维护 | [repository-update](.agents/skills/ascend-repository-update/SKILL.md) | 安全同步业务代码，分流工作台与固定依赖升级，保留现有工作 |
| 任务推进 | [workflow](.agents/skills/ascend-agent-workflow/SKILL.md) | 查证目标与事实、必要澄清、领域路由与整体推进 |
| 任务推进 | [planning](.agents/skills/ascend-task-planning/SKILL.md) | 子任务、依赖、写入归属与资源边界 |
| 任务推进 | [execution](.agents/skills/ascend-task-execution/SKILL.md) | 在授权范围内调查、实验、实现与验证 |
| 任务推进 | [review](.agents/skills/ascend-task-review/SKILL.md) | 复核结论与覆盖，组织交付、交接与回顾 |
| 模型与环境 | [inference-optimization](.agents/skills/ascend-inference-optimization/SKILL.md) | 串联性能基线、profiling、优化候选及性能与精度回归 |
| 模型与环境 | [performance-benchmark](.agents/skills/ascend-performance-benchmark/SKILL.md) | 用 AISBench 核验现有服务吞吐、时延、并发与公共前缀负载 |
| 模型与环境 | [model-accuracy](.agents/skills/ascend-model-accuracy/SKILL.md) | 模型乱码、复读、异常空输出和精度下降的诊断、修复与回归 |
| 模型与环境 | [runtime-snapshot](.agents/skills/ascend-runtime-snapshot/SKILL.md) | 只读采集指定环境的 CANN、代码、PR、依赖与启动条件 |
| 模型与环境 | [container-ssh](.agents/skills/ascend-container-ssh/SKILL.md) | 给手工部署的已有容器建立或恢复独立 SSH，并验证登录 |
| 模型与环境 | [HCCL 打流](.agents/skills/ascend-hccl-traffic-test/SKILL.md) | 复用 MPI/CANN 验证单机或多机 alltoallvc 双模式通信 |
| 知识与总结 | [knowledge-curation](.agents/skills/ascend-knowledge-curation/SKILL.md) | 检索、核实、归纳和复查知识，保留历史与适用边界 |
| 知识与总结 | [weekly-report](.agents/skills/ascend-weekly-report/SKILL.md) | 生成个人工作及项目/知识改进两份周报，交付 Markdown 和 HTML |
| Skill 建设 | [skill-candidate-review](.agents/skills/ascend-skill-candidate-review/SKILL.md) | 评估价值、已有覆盖与维护成本，给出最小修改或不改的结论 |
| Skill 建设 | [skill-development](.agents/skills/ascend-skill-development/SKILL.md) | 创建或优化已确认范围的项目自有 skill，验证入口与代表行为 |

算子、模型适配、部署、profiling、CI/PR 和源码学习由 workflow 按[领域映射](upstream/skill-mapping.md)选用已有流程，不要求每个领域都另建一个项目 skill。

定位/分析默认交付证据与建议；明确要求修复/优化/实现才推进业务修改。提交、推送和发布按本次授权处理，未授权时提供可审核结果。数值语义、支持范围和必需验收的变化由用户决定。

涉及产物搬迁/安装来源或原生扩展兼容问题时，可按需使用 [通用运行探针与产物核对](docs/runtime-tools.md)。两个 Python 标准库工具独立运行，复用原远程执行能力；普通业务任务不默认增加导入、NPU 或 PD 检查。


生成式AISBench评测的指标、有效回答与输出审计可使用[证据报告工具](docs/aisbench-evidence.md)，消费已有明确run，分别给出逐组和总体报告；官方分数与格式异常不混为一个通过结论。

## 按用途准备领域来源

初始化按已选能力准备来源；手工准备时，在工作台根对下表选定路径执行：

```bash
git -c submodule.recurse=false submodule update --init -- <来源路径>
```

`<来源路径>` 替换为下表路径，可在同一命令中指定多个所需路径。仅使用自有文档或本地合成测试时，无需全量准备这些来源。目标版本由父仓库 gitlink 和 [sources.lock.yaml](upstream/sources.lock.yaml) 固定；升级走 dependencies，避免直接跟随远端最新提交。

| 来源路径 | 启用条件与边界 |
|---|---|
| `deps/vllm-ascend-workspace` | 使用其领域流程或执行工具；按用途准备身份、工具与服务器，不重复克隆已绑定业务代码 |
| `deps/cannbot-skills` | 使用 AscendC 等领域方法；资料引用不要求安装整套插件 |
| `deps/matt-pocock-skills` | 使用澄清、拆分、实现与交接的方法来源 |
| `deps/model-analysis` | 模型架构报告、版本比较或参数/KVCache 估算，按[调用说明](.agents/skills/ascend-agent-workflow/references/model-analysis.md)使用；原仓许可尚未明确、内部 gitlink 声明缺口保留，仅作资料引用，再分发前需核实许可 |
| `deps/aisbench-auto-tools-prefix` | 服务性能压测工具源码；AISBench、tokenizer 等依赖在请求发起端按需准备，不要求全部服务节点安装 |
| `deps/awesome-agent-skills` | 模型精度诊断只读手册，不安装同仓其他 skill 或执行其服务器管理、快照、迁移脚本 |
| `deps/compound-engineering` | 知识归纳与复查的只读方法，不安装整套插件；项目适配由 knowledge-curation 维护 |

不要对整个依赖树无条件递归初始化，以免连带克隆 workspace 内的业务代码。取得来源不代表工具可调用、客户端已接入或远程运行就绪。

## 环境要求与验收边界

| 使用或验证内容 | 前提与能证明的范围 |
|---|---|
| 阅读文档、行为走查、规划 | 仓库及所需来源可读；能检查入口和决策边界，不能证明真实运行成功 |
| 工作台本地统一回归 | Python 3.10+、Git、Node.js 22.12+ 及锁定的渲染依赖；覆盖根测试、周报真实渲染和 HCCL helper 合成测试，不连接服务器或占用 NPU |
| 本地开发与 PR | 实际业务代码、版本组合、作者/DCO、认证及目标仓库权限就绪；以本机初始化报告和当前 Git 状态核对 |
| 远程 NPU、模型、服务或 CI 验收 | 所需工具和实际环境就绪；按任务记录代码、设备、输入及原生结果，分别验收正确性、性能和覆盖范围 |

本地回归在工作台根运行：

```bash
npm ci --ignore-scripts
python scripts/validate_workbench.py
```

依赖缺口和条件跳过须明确报告；平台权限或 POSIX 分支跳过不能算作已实测。可选 skill 格式校验器、引用检查和最终候选树的复用验收见[本地验证说明](docs/validation.md)。

工作台建设与维护状态见[开发计划](docs/开发计划.md)和[开发记录](docs/开发记录.md)；每台机器的接入状态保存在本机 `.workbench-local/init-report.md`。具体工程验收以对应任务的当前代码、环境和证据为准，有限设备或单一场景的结果不推广为所有模型、芯片、拓扑或部署方式均已通过。

## 文档与记录

性能压测的服务地址、模型路径和负载参数放在任务可写副本，固定工具源码保持只读；发起压测不自动重启既有服务。精度评测、算子打流和纯 profiling 按各自入口执行。

- [AGENTS.md](AGENTS.md)：所有会话共享的行为规则与导航。
- [项目框架](docs/项目框架.md)：架构、职责、init 去重与建设标准。
- [开发计划](docs/开发计划.md)：工作台自身待办和完成状态。
- [开发记录](docs/开发记录.md)：实际变化、验证和决定。
- [归档与知识维护](docs/daily-sync.md)：个人任务归档和调度配置留本机，仅按授权发布skill与知识维护内容；实际推送后逐项反馈变化、验证和保留项。
- [任务与台账规范](docs/task-records.md)：任务材料、算子进度与完整日志、服务器快照、容器及性能/精度/SWE 三类正式测试表。
- [领域映射](upstream/skill-mapping.md)：锁定版本中的真实入口和能力边界。
- [配置示例](config/workbench.example.yaml)：本机配置的参考结构，`null` 不是默认授权。
- [流程演练](docs/项目框架.md#15-第一轮流程演练)：明确标记的模拟场景，真实工程验收另行完成。

新任务按[统一材料规范](docs/task-records.md)组织：每日事项独立分目录，长期命名任务及模型分析使用相应独立入口。每个事项从任务说明查找脚本、配置、日志和结果；服务器、容器和分类测试台账按统一规范生成在本机 `records/`，通过任务材料串起环境与测试。tasks、records、`.workbench-local/` 和本机配置均不提交；历史任务保持原位。`repos/` 下业务仓库各自维护 Git 历史，父项目只记录定位和证据。
