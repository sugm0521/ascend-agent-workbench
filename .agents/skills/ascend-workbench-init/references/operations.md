# 初始化操作、下层步骤与验收

适用于首次接入、特定缺失项修复及失败恢复。先读取 [配置约定](config-schema.md)，按当前所选 workspace 提交查验工具，不假设本文列出的入口永远不变。

## 实施前确认

先只读探测，再形成可审核的本轮方案，并在任何初始化实施操作前集中收齐必需信息：

| 确认项 | 适用条件与需要确定的内容 |
|---|---|
| 范围与能力 | 明确 standard/lightweight 与本轮启用的本地、远程、测试能力；已有明确范围沿用，未启用能力无需追问 |
| 业务位置 | 两仓各自复用/专用 clone/子模块模式及真实路径；冲突路径的处置不能由默认值替代 |
| 来源、拓扑与基线 | 实际 clone URL、community/fork、origin/upstream、vLLM-Ascend 基线与 vLLM 配对策略；必要的 fork 创建、既有分支/remotes 变更纳入方案 |
| 作者与账号 | 缺失或拟调整的 Git name/email、GitHub 账号与认证通道；GitHub 昵称/邮箱只能作为作者候选，不能自动视为已确认作者 |
| 已启用能力的接入 | 仅在本轮需要时确定机器/profile/alias、服务器/容器目标及接入方式；按原流程取得选择，不要求用户在聊天粘贴机密 |

每项必须有明确答复或可核实的既有配置/决定；已定项不重复问。异步多问题可能逐项返回，必须检查整个必需项集合，而不是以任意一条答复触发执行。仅确认仓库路径而作者未答复时，整轮初始化实施保持等待，允许继续只读核对和必要记录；禁止 clone、依赖初始化、版本切换、配置写入以及其他初始化副作用。

用户明确缩小范围可以改变必需项集合，agent 不得自行将未答项视为可选或把标准模式降级。进入实施后新发现的必要取舍先补充确认，再继续；原失败和已完成项保留，不回滚或重复成功步骤。每次实施前按实际状态检查本轮必需项齐备性，已有授权仍有效且条件未变时直接执行。

## 一份本机报告

报告由主 agent 维护，默认 `.workbench-local/init-report.md`。已有报告作为线索，完成状态必须由当前现状支持。

报告记录工作台根目录、配置 schema、检查时间、初始化模式、owner、启用能力、用户已定选择与授权来源，然后维护操作表：

| operation_id | 目标环境/实际路径 | 期望状态 | 单一执行方/入口 | 依赖操作 | 授权范围 | 状态 | 证据/恢复条件 |
|---|---|---|---|---|---|---|---|

操作状态用 `ready`、`missing`、`pending_decision`、`in_progress`、`failed`、`unknown`、`deferred`；未启用能力单列 `not_enabled`。状态不是任务服务接口。`unknown` 不能直接重跑，应核对是否已发生变化。未知/未验证的权限、CI 配对与 provider 不写 ready。

必需项存在 `pending_decision` 时，本轮初始化实施未获齐备选择，不得将其他待办提前标为 `in_progress`。确认前整理的报告/任务记录可以保存事实和候选方案；不会成为写入业务、本机或 provider 配置的授权。

去重键包含主机/容器或本机上下文、真实工作目录与期望变化。认证按主机/服务/账号/认证通道合并；作者/remotes 按每个实际仓库分别保留。共享 common Git dir 的不同 worktree 不合并其工作目录快照。

## 操作归属

| 准备项 | 默认组织者 | 下层条件与边界 |
|---|---|---|
| 入口、配置、顶层依赖、总报告、界面接入 | 上层 | 顶层仅按 lock 和指定 submodule 路径准备 |
| GitHub 登录与认证通道 | 上层安排一次 | 可以委托原工具；另一层只验收，仓库权限分别查 |
| 业务 clone/submodule、作者、remotes、CI 配对 | 每项操作指定上层或下层之一 | 唯一业务路径；已定选择传入下层 |
| workspace 持久身份、machine profile、执行依赖 | 原 workspace 工具 | 启用相关能力且确有缺失时；上层记录原位置引用 |
| conformance kit/特定环境 | 原声明入口 | 相关测试或任务启用后才准备 |

下层完整初始化会准备未选业务仓库时，不能直接调用。下层没有范围参数时选定向 helper；没有可用 helper 则只暂停相关步骤，给出具体适配方案，不复制第二套业务仓、不改下层维护源。

## 只读现状查询

对配置中每个候选 path，先解析真实路径，再查询 `git -C <path> rev-parse --show-toplevel`。返回根目录必须与预期实际仓库一致，且不是上层/workspace 父仓；未初始化子模块往往会回落父仓。随后用 `rev-parse HEAD`、`symbolic-ref --short -q HEAD`、`status --porcelain=v1`、tracking 查询及 `config --show-origin --get user.name/user.email` 查验。路径未存在、非 Git 仓、错误父根目录分别报告。

只查相关仓库，不为了展示 branch 默认 fetch。ahead/behind 标明缓存 refs 与时间；需要最新远端时单列联网查询/获取范围。remotes 和 fetch/pushurl 检查保留额外配置，输出前移除 URL 凭据。

`gh` 可用、`gh auth status`、所用账号、Git HTTPS/SSH 通道和目标仓权限分别查。API 返回的仓库权限只证明该检查范围，未实测 push 的通道限制如实记录；公共读取不证明账号或写权限。缺认证走官方交互登录与安全存储，不要求聊天粘贴 token。

## 条件使用 workspace helper

当前选择的 workspace 为工具根；执行前查看其真实文件、参数和副作用，任何相对路径都按该入口要求解析。

- `.agents/skills/repo-init/scripts/resolve_vllm_ci_pin.py --vllm-ascend-dir <实际路径>` 支持外部 vLLM-Ascend。它先读 `.github/vllm-main-verified.commit`，旧版本按 workflow/docs 回退，并报告来源。调用前确认该来源属于计划中的 vLLM-Ascend HEAD。
- `repo_topology.py configure --repo <实际路径>` 是有副作用的定向入口，适用明确的新配置；已用 fetch/pushurl/额外 remotes 迁移先检查适用性，不能为便利强行改写。
- `repo_topology.py ensure-main` 会 fetch/准备 tracking 并可能切 branch；它不能作为普通分支查询或 CI 配对后的无条件步骤。`compare-main` 在当前实现会 `ls-remote`，纯本地快照使用原生只读 Git 查询。
- `repo_init_probe.py` 会确保存储持久身份，也可能查询 GitHub；`repo_init_profile.py plan/apply/apply-alias` 也可能确保身份。仅相关能力需要时纳入已授权操作，不为分支总览触发。
- 远程能力按父仓原声明与 `remote_dev.py` / `vaws.py` 的 status/bootstrap 入口核对；provider 接入先用原预览入口，保留用户维护的同名 provider/env/未知字段。不得因缺一个 provider 跑业务完整 repo-init，也不能把 bootstrap 成功当 NPU 运行完成。

下层 skill 的通用 checkpoint 若包含本次已确认选择，传入这些选择并只补真缺口；其未相关的完整流程不加载、不执行。下层必要规则与上层范围无法协调时报告冲突。

## 业务代码与 CI 配对

复用：保留实际 branch、dirty、remotes 和认证，只修本轮授权缺失项。多候选冲突先确认绑定，不能重置旧仓来“统一”。

专用 clone：先查目标目录归属；登记一致的既有 clone 作为重跑成功项，其他占用不得覆盖/删除。使用普通独立 git clone，从已确认 URL 到已确认目标，不迁移旧 dirty，不默认 `--shared`、`--reference` 或 symlink。fork 模式先核对真实个人仓与社区 upstream；fork 不存在时集中确认创建，不能拼 URL 后假定存在/可写。拓扑设置与 tracking 分开记录，后者不能覆盖版本配对。

workspace-submodule：先核对所选 workspace 的 gitlink、业务目标路径与已定基线，再按它的适用定向流程准备该仓。两个业务仓库采用混合模式时，不能跑会创建未选另一副本的整套递归流程。顶层 `deps/` 初始化默认仅指定选定路径；必要递归须证明范围，不使用整个树来图方便。

新仓库配对的完成证据：

1. vLLM-Ascend 实际完整 SHA 等于已确认目标基线；声明文件从该基线读取，记录路径/父 SHA/解析来源。
2. 将解析出的 ref 验证为 Git commit（例如 `rev-parse --verify '<ref>^{commit}'`）；必要获取只按已确认来源与范围执行。tag/branch 解析后固定实际 SHA，不能只保留可移动文本。
3. 正确的实际 vLLM 仓存在该 commit，已授权的新仓 checkout 后 HEAD 等于解析 commit；再次查验两仓 HEAD、branch/detached、dirty 与 tracking，记录完整双 SHA。
4. 声明解析失败、ref 不可获取或实际 HEAD 不符时保留缺口；不能静默改为最新 main。旧开发分支偏离只报告，不为了使表格 ready 自动 checkout。

CI-pinned 配对证明源码组合，不能证明构建、NPU、精度或性能。后续任务按其验证要求单独验收。

## 最终验收与快照

分别报告资料可读、skill 可发现/读取、脚本或 provider 可调用、目标环境适用；不要把文件存在串成全部就绪。

| 能力 | 最低证据 |
|---|---|
| 资料/skill | 实际来源/完整 SHA、路径、所需入口可读，发现/显式读取方式 |
| 代码 | 两个独立 Git 根目录、绑定模式、实际双 SHA、CI 声明核对与偏离 |
| Git 作者 | 两仓有效 name/email 及配置来源；需要修改时为仓库级已授权配置 |
| GitHub/PR | 实际账号、认证通道、真实拓扑及各仓权限检查范围；缺口明确 |
| 远程能力 | 原身份/profile/provider 引用、所需接口状态、实际目标环境验证范围 |

仓库分支总览列仓库、实际 Git 根目录、Codex 主/附加目录、branch/detached、完整 SHA（展示可用 short）、dirty 概况、tracking、查询时间与 refs 新鲜度；依赖另列期望版本/实际偏离。解析根后去重，不把 uninitialized 当业务仓。

工作台保持主目录；业务路径可由用户或可用原生入口附加到项目，报告界面接入是否实际完成。未有能力自动登记时给出两个已绑定具体目录与添加步骤，不能宣称已附加。后续业务 Git/PR/worktree 明确所选 repo，规则和 skill 按任务显式读取。

失败恢复保留已完成项、原失败与具体恢复条件；不从头再跑、不删多余既有副本、不修改 sources.lock 以掩盖偏离。若用户明确将业务/身份初始化留给另一个窗口，只完成本窗口授权的资料或项目构建，并把标准初始化写为未执行。
