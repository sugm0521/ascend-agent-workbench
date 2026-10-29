# vLLM-Ascend Agent 工作台

`ascend-agent-workbench` 用于需求分析、问题定位、模型性能与精度、算子开发、部署、CI/PR 和工程 skill 开发。它负责组织任务和证据，按需使用已有领域 skill 与执行工具。

工作台采用项目规则、项目级 skill、Markdown 任务记录和固定版本的领域依赖。没有自建 agent 平台、资源调度器或 GUI。

> 本项目正在持续开发与优化，功能、工作流程和使用文档会不断完善。欢迎 **Star 收藏本项目**，方便后续查阅并关注更新。

首次使用从[快速开始](#快速开始)进入；接入后按[任务入口](#按任务选择入口)工作。修改业务代码前请了解[CI 预检](#代码修改与-ci-预检)。知识库与定时维护见[可选知识接入](#可选知识库与定时维护)，维护者验证见[验证说明](docs/maintenance/validation.md)。

## 快速开始

### 1. 获取并打开工作台

准备 Git，克隆本公开仓库：

```bash
git clone https://github.com/sugm0521/ascend-agent-workbench.git
cd ascend-agent-workbench
```

在 Codex 中把克隆得到的 `ascend-agent-workbench` 目录打开为项目主目录，让 agent 先读根 [AGENTS.md](AGENTS.md)。Python、Node.js、GitHub 认证及远程环境按实际用途准备，由初始化检查并提示缺项；克隆公开仓库不要求先准备 PR 权限。

### 2. 发送第一条初始化请求

可以直接复制到对话中：

```text
请使用 $ascend-workbench-init 帮我完成首次接入。
请先确认我的使用目标，再确定本轮需要准备的代码、工具和运行环境。
先检查已有配置、业务代码与工具，优先复用现有环境。
请集中确认我的使用范围、必需信息，以及是否接入私有知识库、远程同步和定时维护，确认后再实施。
```

按你的目标选择准备范围；不确定时先让 agent 说明差异：

| 你要做什么 | 初始化准备什么 |
|---|---|
| 阅读资料、源码分析或规划 | 轻量准备所需 skill、资料和可读源码，列出开发条件缺口 |
| 本地开发与 PR | 核对或准备业务仓库、版本组合、Git 作者、认证、remotes 与目标权限 |
| 远程实验或 NPU 验证 | 在已选范围上补齐实际工具、服务器/容器、环境与可用设备，按任务验收 |

初始化会汇总上下层必需信息后集中确认，只补已选择的缺失项。业务代码优先复用已有 checkout，也可选择在 `repos/` 下独立克隆；新版本组合按目标 vLLM-Ascend 的 CI 声明配对。远程 NPU、知识库和调度分别选用，不要求每个人全部接入。首次使用无需先手填整份 YAML，[配置示例](config/workbench.example.yaml)供确认字段时参考。

已接入的使用者更新工作台后，可说：“使用 $ascend-workbench-init，检查已启用能力的新接入要求，先给差异，不修改。”确认后只补差异，不重复首次初始化；详见[增量检查与补齐](.agents/skills/ascend-workbench-init/references/operations.md#增量检查与补齐)。

如果客户端没有自动发现 skill，显式让它读取 [.agents/skills/ascend-workbench-init/SKILL.md](.agents/skills/ascend-workbench-init/SKILL.md) 再执行；维护源仍是本项目 `.agents/skills/`。

### 3. 查看接入结果

初始化结束时，agent 会先说明现在可使用的能力、仍阻塞的目标和一条适合当前条件的下一步请求，再提供本机 `.workbench-local/init-report.md`。完整报告中核对：

- 实际使用哪些业务目录与版本，哪些已有配置被复用。
- 所选能力哪些已就绪、哪些缺失或待处理，以及它们阻塞什么。
- 若接入知识库，实际目录、远端、定时任务和首次同步分别处于什么状态。

克隆完成不等于环境接入完成；本地就绪也不代表远程服务、NPU 或 CI 已通过。未选能力不必补齐，缺少远程环境不阻塞独立的本地工作。

### 4. 开始第一个任务

接入后直接描述目标、现有材料与本轮范围，例如：

```text
请帮我定位下面这个报错。先检索相关知识并核对实际代码，给出证据、结论和下一步建议。
报错与相关材料：<粘贴报错或提供可读取的文件位置>
```

没有业务材料时，可先体验[无服务器报错排查案例](docs/guides/first-task/README.md)：只读分析 vLLM-Ascend 的合成启动参数与 KV Cache 容量报错，不需要业务仓、私有知识库、Python 或服务器。初始化会在适合时推荐该入口，不自动开始。

不确定领域入口时使用 `$ascend-agent-workflow`；已明确的小任务可直接用对应 skill，日常工作不重复初始化。agent 会按[任务材料规范](docs/guides/task-records.md)保存必要记录，阶段交付时说明实际验证和未完成项。

#### 任务工作目录与命名

涉及代码、实验、验证或交接时，agent 按[任务目录规范](docs/guides/task-records.md#任务目录与唯一入口)建立或恢复工作目录。下列路径均相对工作台根；简单问答不强制建目录。

| 任务类型 | 目录约定 | 示例 |
|---|---|---|
| 普通事项 | `tasks/YYYY-MM-DD/<事项名>/`，日期用北京时间 | `tasks/2026-10-27/启动报错定位/` |
| 用户明确命名的长期任务 | `tasks/<指定任务名>/` | `tasks/推理吞吐优化/` |
| 模型架构分析 | `tasks/<模型名>-模型分析/<YYYYMMDD>-<分析序号>/` | `tasks/示例模型-模型分析/20261027-1/` |

事项名建议用“对象＋目标/问题”的简短描述，例如 `容器SSH接入`、`启动报错定位`，也可用短横线英文名。目录跟任务走：同一任务跨天、恢复或交接时沿用原目录；新的独立目标再建目录。模型的新一轮独立分析在同一模型父目录下递增序号，恢复同一轮则沿用该轮目录。

```text
tasks/2026-10-27/启动报错定位/
├── 任务说明.md   # 目标、当前状态、结论、下一步和材料入口
├── scripts/      # 任务专用脚本
├── configs/      # 该轮实际配置
├── logs/         # 采集或运行日志
└── results/      # 分析、验证、交付及回顾
```

以 `任务说明.md` 为唯一状态入口，其他目录和材料按需创建。已有目录保留，不为采用示例而改名或搬迁；`tasks/` 是本机任务材料，不随公开工作台提交。详细分组和运行编号见[材料规范](docs/guides/task-records.md#编号用途与材料分组)。

## 可选知识库与定时维护

工程知识保存在每位开发者选择的外部私有目录，公开工作台只保存接入方法和通用 skill。初始化会集中确认下列选项，已有明确选择直接复用：

| 选择 | 可选方式 |
|---|---|
| 是否启用知识库 | 不启用 / 启用；启用后确认本机目录与项目子目录，可复用已有笔记库 |
| 布局与维护规范 | 新库确认默认或自定义布局；已有库复用规范与分类，仅补齐已授权缺项 |
| 远端同步 | 不使用远端 / 复用已有私有仓库 / 新建私有仓库 |
| 定时维护 | 不启用 / 复用已有任务 / 新建任务；确认频率、时间、时区与范围 |
| 同步策略 | 手动提交推送 / 明确授权范围内自动同步 |

这些选项独立：仅本地也可以定时整理，有远端也可以手动维护。定时维护不自动批准新的知识候选或整库推送。实际路径、私有地址和调度选择只留本机；知识目录由 `paths.knowledge_root` 统一定位。普通任务缺少绑定时报告覆盖缺口，不向公开仓库写知识正文。

只想接入知识库，可直接说：“使用 $ascend-workbench-init，只接入我的私有知识库，并确认远端与定时维护方式。”详细流程见[初始化接入约定](.agents/skills/ascend-workbench-init/references/operations.md#私有知识目录接入)，字段见[配置约定](.agents/skills/ascend-workbench-init/references/config-schema.md#私有知识库的远端与维护选择)。

## 更新已接入的工作台

更新代码使用[repository-update](.agents/skills/ascend-repository-update/README.md)，接入条件的差异检查使用 init。可复制：

```text
请使用 $ascend-repository-update 更新当前工作台。
先核对实际仓根、分支、跟踪远端、未提交/已暂存修改及正在使用该代码的任务，保留我的现有工作。
确认目标后仅安全快进；目标不明、无法快进或会影响现有工作时，先给具体差异和处理方案。
不要自动更新全部依赖、业务仓或运行环境，也不要提交推送。
更新成功后使用 $ascend-workbench-init，只检查已启用能力的新接入要求，给出差异，不实施补齐。
```

已就绪的接入不因更新重新初始化；需补齐的差异按确认范围处理。安全同步及保留工作的具体规则由 repository-update 维护，来源声明/gitlink 变化的兼容评估交 dependencies，不把工作台更新等同于全部子模块升级。

## 常见上手问题

| 遇到的情况 | 下一步 |
|---|---|
| 找不到 `$ascend-workbench-init` | 确认打开的是本仓库主目录，并显式读取上面的 SKILL.md |
| 缺少领域资料或工具 | 让初始化核对所选依赖与原入口；手工准备见下方[领域来源](#按用途准备领域来源)，无需递归安装全部依赖 |
| 没有服务器或 NPU | 先做可完成的资料分析、本地准备与验证，远程能力保留具体缺口 |
| 知识库或调度尚未配置 | 通过初始化定向补齐；不需要因此重做业务仓与远程接入 |

## 按任务选择入口

例如“定位这个问题单的根因”“优化现有服务的吞吐”“核查模型输出复读”或“实现算子替换”。不确定入口时使用 workflow，明确的小任务可直接使用领域 skill，无需完整采访或多个 agent。

表中使用简称，实际调用名称和示例见各 skill 使用说明，例如 `init` 对应 `$ascend-workbench-init`。

下表链接到各skill的使用说明（README）：可查看功能、适用场景、调用示例、输入输出和操作边界；详细执行规范仍由对应 `SKILL.md` 维护。功能或边界变化时同步核对两者，说明中不保存本机运行状态或实验回执。

| 类别 | 入口 | 用途 |
|---|---|---|
| 接入与维护 | [init](.agents/skills/ascend-workbench-init/README.md) | 首次接入、增量接入检查、定向补齐及初始化报告 |
| 接入与维护 | [dependencies](.agents/skills/ascend-workbench-dependencies/README.md) | 版本核对、相关传递依赖、升级与组合验证 |
| 接入与维护 | [repository-update](.agents/skills/ascend-repository-update/README.md) | 安全同步业务代码，分流工作台与固定依赖升级，保留现有工作 |
| 任务推进 | [workflow](.agents/skills/ascend-agent-workflow/README.md) | 查证目标与事实、必要澄清、领域路由与整体推进 |
| 任务推进 | [planning](.agents/skills/ascend-task-planning/README.md) | 子任务、依赖、写入归属与资源边界 |
| 任务推进 | [execution](.agents/skills/ascend-task-execution/README.md) | 在授权范围内调查、实验、实现与验证 |
| 任务推进 | [review](.agents/skills/ascend-task-review/README.md) | 复核结论与覆盖，组织交付、交接与回顾 |
| 模型与环境 | [inference-optimization](.agents/skills/ascend-inference-optimization/README.md) | 串联性能基线、profiling、优化候选及性能与精度回归 |
| 模型与环境 | [performance-benchmark](.agents/skills/ascend-performance-benchmark/README.md) | 用 AISBench 核验现有服务吞吐、时延、并发与公共前缀负载 |
| 模型与环境 | [model-accuracy](.agents/skills/ascend-model-accuracy/README.md) | 模型乱码、复读、异常空输出和精度下降的诊断、修复与回归 |
| 模型与环境 | [runtime-snapshot](.agents/skills/ascend-runtime-snapshot/README.md) | 只读采集指定环境的 CANN、代码、PR、依赖与启动条件 |
| 模型与环境 | [container-ssh](.agents/skills/ascend-container-ssh/README.md) | 给手工部署的已有容器建立或恢复独立 SSH，并验证登录 |
| 模型与环境 | [HCCL 打流](.agents/skills/ascend-hccl-traffic-test/README.md) | 复用 MPI/CANN 验证单机或多机 alltoallvc 双模式通信 |
| 知识与总结 | [knowledge-curation](.agents/skills/ascend-knowledge-curation/README.md) | 检索、核实、归纳和复查知识，保留历史与适用边界 |
| 知识与总结 | [weekly-report](.agents/skills/ascend-weekly-report/README.md) | 生成个人工作及项目/知识改进两份周报，交付 Markdown 和 HTML |
| Skill 建设 | [skill-candidate-review](.agents/skills/ascend-skill-candidate-review/README.md) | 评估价值、已有覆盖与维护成本，给出最小修改或不改的结论 |
| Skill 建设 | [skill-development](.agents/skills/ascend-skill-development/README.md) | 创建或优化已确认范围的项目自有 skill，验证入口与代表行为 |

算子、模型适配、部署、profiling、CI/PR 和源码学习由 workflow 按[领域映射](upstream/skill-mapping.md)选用已有流程，不要求每个领域都另建一个项目 skill。

定位/分析默认交付证据与建议；明确要求修复/优化/实现才推进业务修改。提交、推送和发布按本次授权处理，未授权时提供可审核结果。数值语义、支持范围和必需验收的变化由用户决定。

涉及产物搬迁/安装来源或原生扩展兼容问题时，可按需使用 [通用运行探针与产物核对](docs/tools/runtime-tools.md)。两个 Python 标准库工具独立运行，复用原远程执行能力；普通业务任务不默认增加导入、NPU 或 PD 检查。

生成式AISBench评测的指标、有效回答与输出审计可使用[证据报告工具](docs/tools/aisbench-evidence.md)，消费已有明确run，分别给出逐组和总体报告；官方分数与格式异常不混为一个通过结论。

## 代码修改与 CI 预检

工作台为 vLLM、vLLM-Ascend 业务代码改动组织推送前预检：由 execution 执行、review 核对，读取目标版本的 CI 与仓库规则，按改动选择检查并报告证据。

- **格式与静态检查**：复用目标仓库固定的工具、配置和适用阶段；需要全量检查时保留其范围。
- **相关 CPU 用例**：按代码影响选择，不要求每次提交全量运行；可复用兼容环境或已登记旧容器，在任务隔离目录执行，不影响原有服务。
- **失败与未执行项**：保留实际结果，在授权内处理和复验；带未解决的本地问题推送，须说明影响并取得用户针对这些问题的明确同意。
- **验证边界**：预检不自动运行 NPU 用例；独立 CPU 回归不等于完整 CI 通过。提交推送按本轮具体授权执行，推送后核对远端 SHA 及其 CI。

这是 **agent 执行的预检流程**，目前没有自动 Git hook 强制拦截；不能仅凭本地预检通过宣称远端 CI 全部通过。执行细则、环境复用和例外处理见[业务仓预检说明](docs/guides/business-ci-preflight.md)。

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
| `deps/ascend-agent-skills` | 昇腾领域能力索引与只读参考，按[统一发现入口](upstream/skill-mapping.md#依赖能力发现入口)检索；暂不安装上游 skill 或运行其工具 |
| `deps/compound-engineering` | 知识归纳与复查的只读方法，不安装整套插件；项目适配由 knowledge-curation 维护 |

不要对整个依赖树无条件递归初始化，以免连带克隆 workspace 内的业务代码。取得来源不代表工具可调用、客户端已接入或远程运行就绪。

## 文档与记录

完整说明按用途分为使用规范、工具说明、项目维护和记录模板，见[文档总导航](docs/README.md)。评估过程留本机任务，工程经验按知识流程维护。

性能压测的服务地址、模型路径和负载参数放在任务可写副本，固定工具源码保持只读；发起压测不自动重启既有服务。精度评测、算子打流和纯 profiling 按各自入口执行。

- [AGENTS.md](AGENTS.md)：所有会话共享的行为规则与导航；文件归位和目录分工见[项目目录职责](AGENTS.md#2-目录职责与事实源)。
- [维护者验证说明](docs/maintenance/validation.md)：工作台自身的运行时与依赖要求、自测命令及检查范围；业务代码检查见[CI 预检](#代码修改与-ci-预检)。
- [项目框架](docs/maintenance/项目框架.md)：架构、职责、init 去重与建设标准。
- [开发计划](docs/maintenance/开发计划.md)：工作台自身待办和完成状态。
- [开发记录](docs/maintenance/开发记录.md)：实际变化、验证和决定。
- [归档与知识维护](docs/guides/daily-sync.md)：个人任务归档和调度配置留本机，工程知识写入初始化绑定的外部私有目录，公开仓库仅按授权发布skill及通用方法；实际推送后逐项反馈变化、验证和保留项。
- [任务与台账规范](docs/guides/task-records.md)：任务材料、算子进度与完整日志、服务器快照、容器及性能/精度/SWE 三类正式测试表。
- [领域映射](upstream/skill-mapping.md)：锁定版本中的真实入口和能力边界。
- [配置示例](config/workbench.example.yaml)：本机配置的参考结构，`null` 不是默认授权。
- [流程演练](docs/maintenance/项目框架.md#15-第一轮流程演练)：明确标记的模拟场景，真实工程验收另行完成。

新任务按[统一材料规范](docs/guides/task-records.md)组织：每日事项独立分目录，长期命名任务及模型分析使用相应独立入口。每个事项从任务说明查找脚本、配置、日志和结果；服务器、容器和分类测试台账按统一规范生成在本机 `records/`，通过任务材料串起环境与测试。tasks、records、`.workbench-local/` 和本机配置均不提交；历史任务保持原位。`repos/` 下业务仓库各自维护 Git 历史，父项目只记录定位和证据。

## 许可

除另有声明外，本项目自有代码、skill、模板和文档采用 [Apache License 2.0](LICENSE)。

第三方依赖及引用、改编的第三方内容继续适用各自许可，保留原有版权和许可声明；顶层 `LICENSE` 不替代或扩张第三方授权。来源与固定版本见[来源与许可记录](upstream/来源与许可.md)。其中 `cannbot-skills` 适用 CANN 2.0 的用途及分发条件；`model_analysis` 的全仓许可尚未明确，来源链接或本机只读接入不代表已获得原代码、模板的使用、改编或再分发授权。
