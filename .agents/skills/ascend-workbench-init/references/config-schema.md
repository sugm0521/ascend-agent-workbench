# 配置约定（schema_version: 1）

配置是 agent 读取的约定，不是已实现的解析服务。版本来源使用 `upstream/sources.lock.yaml`，本机选择使用 `config/workbench.local.yaml`，实际检查证据使用初始化报告；三者不能相互冒充。

## 路径与缺省值

- 工作台根目录由当前项目的根 `AGENTS.md` 确定。配置的相对文件路径都相对此根目录解析，不相对 config/ 或 shell cwd。
- `null` 表示未绑定或未决定，不能当成空字符串路径，也不能从示例自动推导 fork/身份/授权。缺字段采用示例的流程偏好，但关键绑定必须核对现状后确定。
- 示例能说明默认位置，不能证明 checkout、接口、认证或界面已就绪。未知 schema_version 或字段含义冲突时，暂停受影响配置步骤并说明差异。
- 允许本机配置使用实际外部绝对路径；提交的示例保持相对路径与空选择。远程路径必须随原 provider 的主机/容器上下文引用，不只写一个裸路径。

## 顶层字段

| 字段 | 类型/值 | 含义 |
|---|---|---|
| `schema_version` | `1` | 当前约定版本 |
| `paths.sources_lock` | 路径 | 顶层依赖来源与固定提交记录 |
| `paths.init_report` | 路径 | 唯一本机初始化计划、结果与快照 |
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

lock 的顶层 commit 是上层选择；传递依赖期望版本仍以所选父提交的原声明为准。不把父声明中的 pin 手工复制进本机配置，也不新建平行 pin 表。

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
