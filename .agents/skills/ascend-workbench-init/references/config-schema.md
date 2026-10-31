# 配置约定（schema_version: 1）

配置是 agent 读取的约定，不是已实现的解析服务。版本来源使用 `upstream/sources.lock.yaml`，本机选择使用 `config/workbench.local.yaml`，实际检查证据使用初始化报告；三者不能相互冒充。

## 路径与缺省值

- 工作台根目录由当前项目的根 `AGENTS.md` 确定。配置的相对文件路径都相对此根目录解析，不相对 config/ 或 shell cwd。
- 除明确说明其他语义的字段（如 `git.push.max_upload_bytes`）外，`null` 表示未绑定或未决定，不能当成空字符串路径，也不能从示例自动推导 fork/身份/授权。缺字段采用示例的流程偏好，但关键绑定必须核对现状后确定。
- 示例能说明默认位置，不能证明 checkout、接口、认证或界面已就绪。未知 schema_version 或字段含义冲突时，暂停受影响配置步骤并说明差异。
- 允许本机配置使用实际外部绝对路径；提交的示例保持相对路径与空选择。远程路径必须随原 provider 的主机/容器上下文引用，不只写一个裸路径。

## 顶层字段

| 字段 | 类型/值 | 含义 |
|---|---|---|
| `schema_version` | `1` | 当前约定版本 |
| `git.push.max_upload_bytes` | 正整数或 null，缺省不限 | 经工作台执行的单次Git推送大小策略；详见下节，不影响其他传输渠道 |
| `paths.sources_lock` | 路径 | 顶层依赖来源与固定提交记录 |
| `paths.init_report` | 路径 | 唯一本机初始化计划、结果与快照 |
| `paths.knowledge_root` | 路径或 null | 可选的外部私有知识目录，由初始化确认并绑定；缺失/null/空值均不启用，不回退公开正文 |
| `feedback.participation` | boolean 或 null | 可选项目改进参与偏好；只在true时主动邀请，缺省/null不邀请，详见下节 |
| `dependencies.<id>.path` | 路径 | 实际领域维护源位置 |
| `dependencies.<id>.enabled` | boolean | 本项目选用该直接依赖；不表示可运行 |
| `business.repositories.<id>` | mapping | 每个业务仓库唯一绑定及已定选择 |
| `init.mode` | `standard` / `lightweight` | 初始化范围；用户本轮明确范围优先 |
| `init.prefer_reuse` | boolean，默认 true | 首次选择时优先复用；不覆盖已选专用 clone |
| `init.github_required` | boolean，默认 true | 标准 PR 准备要求；false 必须报告 PR 缺口 |
| `init.remote_required` | boolean，默认 false | 本轮远程验收是否必需；只影响相关能力 |
| `capabilities.remote_execution` | boolean，默认 false | 是否需要底层远程执行与协调接入 |
| `capabilities.knowledge_tests` | boolean，默认 false | 是否准备相关 conformance 测试依赖 |
| `execution.max_subagents` | 非负整数，默认 3 | 子 agent 同时运行上限；实际工具限额优先 |
| `execution.provider_refs` | mapping | 已有底层 provider/profile/config/id 的引用 |
| `execution.artifact_root` | 路径 | 本机缓存及大型原始产物位置 |

`dependencies` 与 lock 的 `sources` 使用相同 id，以 lock 的键为准；可选来源按本次用途启用，不维护另一份固定来源名单。lock 保存 `{path, url, commit, purpose, declared_dependencies}`，其中 `declared_dependencies` 是父仓原声明的相对文件路径引用。配置 path 可绑定已有外部 checkout；与 lock 记录不同则核对来源和实际 SHA，并报告偏离，不能悄悄改 lock 或切版本。没有配置时使用 lock 路径查询资料现状，不替用户决定业务绑定。

enabled 只表示选择来源，仍须逐个核对其适用初始化。本轮消费方式、下层身份、直接工具/协调/服务器各自状态与用户选择保存于 init_report，原状态与 pin 仍由下层管理。remote_execution=false 不代表 workspace 本机身份/profile 可以默认跳过；也不代表用户已决定本轮所有执行组件的范围。

已有本机配置未声明某个来源或缺少 `enabled` 时，该来源的实施选择为 `pending_decision`，不能继承其他来源的 true/false 或因目录存在认作已启用。可按 lock 路径只读识别资料和能力；确需初始化或启用时，沿用本轮已有决定，并将剩余必要选择纳入 init 的集中确认，不自动改本机配置。显式 false 表示本轮未启用，按需报告相关能力缺口。

lock 的顶层 commit 是上层选择；传递依赖期望版本仍以所选父提交的原声明为准。不把父声明中的 pin 手工复制进本机配置，也不新建平行 pin 表。

## 项目改进参与偏好

此字段保存在忽略提交的 `config/workbench.local.yaml`，不更改schema_version；由agent按当前配置读取。它只控制项目改进的主动邀请，不限制正常错误报告、验收、业务交付或使用者主动反馈。

| 值 | 含义与行为 |
|---|---|
| `true` | 使用者明确参加；有实质反馈价值时可在合适收尾点邀请一次，仍需本次整理许可及每次发布前的最终资料审核 |
| `false` | 已明确不参加；不主动邀请，也不反复询问偏好 |
| 缺字段 / `null` | 尚未选择；不主动邀请，不在普通业务中补问；显式初始化或调整偏好时再集中提供选择 |

首次初始化将“是否参加项目改进”作为可选项一并询问，既有true/false决定复用；未答复保留未选择，不写成true或false，且不阻塞其他必需项已齐备的初始化。字段缺失不是旧用户必须迁移的接入缺陷。字符串、整数或其他类型不作为同意，停用主动邀请；显式配置检查时报告该字段错误，不自动改值或在普通任务中追问。

用户明确要求本次反馈时可直接进入，不自动改变长期偏好。长期开启/关闭由[初始化定向步骤](operations.md#项目改进参与选择)仅修改本字段并保留其他配置；参加不是运行、资料收集、上传、Issue/PR创建或后续补充的许可。反馈执行及当次审核见[专项流程](../../ascend-workbench-maintenance/references/skill-feedback.md)。

## Git 推送策略

`git.push.max_upload_bytes` 的类型、严格小于边界、计量与失败处理统一遵循[发布配置约定](../../../../docs/maintenance/validation.md#git-推送大小配置)，此处不维护另一套阈值。

- 首次初始化必须将“Git上传内容大小：不限制，还是设置字节上限？”纳入集中提问；用户选择限额时必须收齐正整数字节数。已有可核实的用户明确决定直接沿用，不重复询问。未答复则标为 `pending_decision`，按实施前确认门槛等待，不能从示例、字段缺失、null、沉默或预选项推断已经选择不限。运行时缺省不限的语义不替代首次初始化确认。
- 补齐、恢复及重复初始化保留已有明确选择，不用示例覆盖。已有配置中的合法null或正整数可按既有配置复用；首次初始化的示例副本不算用户决定。旧配置缺字段时补问该项，不擅自写null；已有值非法时报告配置错误，不自动降为不限。用户选择不限后写null，选择限额后写已确认数值。
- 初始化报告记录有效值、来源（既有配置或用户明确选择）与含义；只验证配置读取和语义，不运行push、安装hook或测量尚不存在的推送载荷。此项不证明推送前大小检查已执行，不影响其他渠道的独立限制。

## 每个业务仓库的字段

id 为 `vllm` 与 `vllm-ascend`，各自可选不同模式。

| 字段 | 类型/值 | 使用规则 |
|---|---|---|
| `mode` | `reuse` / `dedicated-clone` / `workspace-submodule` | 工作目录准备方式；默认 reuse 是偏好 |
| `path` | 路径或 null | 已绑定实际独立 Git 根目录；null 时先探测并确认 |
| `clone_path` | 路径 | 专用 clone 的建议目的地；不自动启用 clone |
| `topology` | `community` / `fork` / null | 已确认拓扑；null 保留已有 remotes，未定项再确认 |
| `source_url` | URL 或 null | 已确认的克隆来源；不从账号名称拼出个人 fork |
| `origin_url` | URL 或 null | 已确认 origin 目标；保留既有 pushurl/额外配置 |
| `upstream_url` | URL 或 null | 已确认社区 upstream；community 模式按实际选择 |
| `requested_ref` | Git ref 或 null | 明确的新基线；不是切换既有分支的授权 |

`dedicated-clone` 准备后 path 绑定实际 clone_path；重复执行核对登记和实际根目录，已成功目录不重新 clone。`workspace-submodule` 的 path 必须指向所选 workspace 中已核实的对应业务子模块，不能只靠 mode 推断目录。`reuse` 可以绑定外部仓库或已有专用 clone，但与仓库报告一致才沿用。

新 vLLM-Ascend 的目标基线先确定，再从该提交读取 CI pin。vllm.requested_ref 留空时采用已核实 CI pin；用户明确的其他版本选择记录偏离与检查。该字段不建立永久跟随 main 的策略。

## provider 与机密

provider_refs 的已知键为 `remote_dev`、`coordinator`，值为底层已有入口或配置的引用；null 表示未接入。它不是服务器清单，也不是自动生成 MCP 配置的授权。相关任务再读取原 provider 的状态与规则。

不保存 token、密码、私钥、带凭据的 URL；不复制底层服务器、模型、镜像、租约或资源状态。作者、账号与认证选择通过原安全工具核对；本机报告只保存必要的非机密身份结果与授权引用。

`remote_required: true` 而 remote_execution 未启用时先澄清或核对相关任务授权，不能偷偷启用。知识测试未启用时记录为 not_enabled；不下载 conformance kit 来使所有条目变绿。

## 私有知识目录

`paths.knowledge_root` 是工程知识正文、主题索引和历史的唯一根目录。使用本机绝对路径，或相对工作台根解析的外部路径；解析真实路径后必须在工作台之外。路径只保存在忽略的本机配置和报告；提交示例保持 null，不写开发者用户名、笔记软件布局或实际仓库 URL。该字段不表示 Git 仓根、托管可见性、写权限或推送授权。

首次初始化集中确认是否接入；选中才收集目录。已有配置复用，明确不接入保留 null 并在报告记 not_enabled；没有决定仍为 pending_decision，不能由默认值替用户选择。普通任务缺少配置时报告知识覆盖缺口并继续不依赖它的工作，不运行完整初始化。`capabilities.knowledge_tests` 仍只控制 conformance 测试依赖，与工程知识目录无关。

## 私有知识库的远端与维护选择

这些可选字段仅记录初始化已确认的本机选择，由 agent 按约定读取，不增加 YAML 解析器或调度服务。本机目录只有 `paths.knowledge_root` 一个绑定；是否接入的明确决定另在初始化报告保留。知识未启用不要求下表信息；示例中的 null/空列表不代表不使用、不启用或操作授权。

| 字段 | 类型/值 | 含义 |
|---|---|---|
| `knowledge.remote.mode` | `none` / `reuse` / `create` / null | 不使用远端、复用私有仓或本轮新建私有仓；null 未决定，创建完成核实后改记 reuse |
| `knowledge.remote.url` | Git URL 或 null | 已确认远端地址，不含凭据；实际 Git 配置另行核对，不能代替本机目录 |
| `knowledge.remote.branch` | 分支或 null | 已确认知识同步目标；不预设分支，不授权切换已有开发分支 |
| `knowledge.sync.mode` | `manual` / `automatic` / null | 有远端时手动或按具体授权自动同步；缺字段/null 不自动推送 |
| `knowledge.maintenance.enabled` | boolean 或 null | 是否启用知识相关定时维护；已有明确选择沿用，未决定保持 pending_decision |
| `knowledge.maintenance.jobs` | list，默认空 | 已确认任务；每项单独复用或创建，支持日/周等不同用途，空列表不推断已有任务已停用 |
| `knowledge.maintenance.jobs[].mode` | `reuse` / `create` | 此项复用已有任务或本轮创建；成功创建并回读后改记 reuse |
| `knowledge.maintenance.jobs[].automation_id` | string 或 null | 原调度入口返回的真实任务 ID；reuse 先读取匹配，create 成功后保存，不编造 ID |
| `knowledge.maintenance.jobs[].purpose` | string | 实际维护用途，如归档与知识维护、周报；用于识别范围而非仅按名称去重 |
| `knowledge.maintenance.jobs[].timezone` | 时区 | 用户确认的时区，不继承开发者个人时区 |
| `knowledge.maintenance.jobs[].schedule` | string | 人可读的频率/时间；由实际调度入口转换并回读核对，不假设所有客户端使用相同调度语法 |
| `knowledge.maintenance.jobs[].scope` | list of string | 本项实际取材/维护范围；自动推送与候选收录仍需各自具体授权 |

jobs 条目结构示意（所有取值需由本机实际选择补齐，不复制 ID 或时间）：

```yaml
knowledge:
  maintenance:
    enabled: null
    jobs:
      - mode: null
        automation_id: null
        purpose: null
        timezone: null
        schedule: null
        scope: []
```

`remote.mode: none` 时不要求 URL/分支、Git 登录或同步策略，不操作现有 remote；仍可启用本地定时维护。`manual` 时定时任务只整理和列待同步项，用户本次单独授权的同步按其范围执行。`automatic` 仅表达选择，实际自动提交推送须有可核对的目标/子树/操作授权，并在维护提示和报告中明确，不能用一个配置值批准候选、整库同步或扩大发布范围。新建远端的账号/名称、首次同步及实际调度操作的完整方案和授权引用留初始化报告。

旧本机配置只有有效 `paths.knowledge_root` 时继续复用知识读写；不因缺少本节字段而中断既有本地能力、清空配置、停用任务或自动开同步。可核实的已有远端/调度及用户决定复用，仅对本轮确需实施的未知项集中确认。记录的 URL/ID 不取代实际 Git 与调度系统状态；字段冲突或结果不明先只读核对。实际路径、私有地址、ID、调度配置与回执不上公开仓。
