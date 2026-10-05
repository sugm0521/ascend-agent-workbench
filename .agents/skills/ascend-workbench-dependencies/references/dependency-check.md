# 依赖图、候选版本与验收

## 事实源与记录

上层 `sources.lock.yaml` 的 `sources.workspace/cannbot/matt` 保存顶层 `{path, url, commit, purpose, declared_dependencies}`；本机配置的对应 `dependencies.<id>.path` 可以复用已有外部维护源。先查真实源和 SHA，报告差异，不仅以目录名认来源。

`declared_dependencies` 是下层原文件引用，必须从本次所选父提交读取；它不是一个可以独立更新的上层 pin 列表。候选父新增声明时主动识别相关入口，不能只检查旧 lock 已列文件。下层 pin 保持原文件权威，上层保存检查快照与引用即可。

受影响图与验证可记在本次任务 results/，或无业务任务时记在 `docs/开发记录.md` 并引用 `upstream/skill-mapping.md`；不要另造状态数据库。节点行至少包括：

| 节点/类别 | 父节点/父 SHA | 声明文件/接口 | 用途/启用条件 | 期望约束 | 实际路径/版本 | 拟用版本 | 结果/验证引用 |
|---|---|---|---|---|---|---|---|

实际结果使用 verified / drift / missing / inaccessible / conflict / not_enabled，并说明验证层级；单一 `ok` 无法证明全链路。

## 递归范围与冲突

从启用能力及本次 diff 出发查相关声明，不扫描/下载所有生态仓。解析依赖声明不等于准备 checkout。先核对每项是 runtime、execution/protocol、optional-test、business 或 environment，再决定哪些是本轮必需。

以规范来源身份与实际环境/路径去重，路径别名不能重复准备同一 checkout。两个父声明对同一 shared provider 要求不兼容版本时记录两条边，不能取后读到的值覆盖。需要隔离版本但原工具不支持时报告缺口，不重建平行资源管理。递归栈遇到已在栈节点报告循环并停止该链，其他独立能力继续。

私仓或目标提交声明不可访问时标记具体来源/父 SHA；缺相关必需声明不能宣称兼容。可选未启用节点只记录，不 bootstrap。已有本机目录不是自动纳入本轮升级的理由。

## workspace 的当前声明入口

以下为已核对过的入口提示，执行前仍读所选父提交；不把当前字段或 pin 固化为永恒要求：

| 声明/入口 | 范围 | 应核验的内容 |
|---|---|---|
| `.agents/deps/remote-dev.json`、`docs/remote-dev-consumption.md` | 启用远程能力时 | URL/commit、定位环境变量、bootstrap/status、resolver/result 接口、所需运行文件 |
| `.agents/deps/coordinator.json`、`docs/coordinator-consumption.md` | 使用协调/session 接口时 | URL/commit/tree、入口文件、provider/env、声明的 mirror/blob 检查与兼容约束 |
| `.agents/deps/vaws-knowledge.json`、相关 tests/CI | 仅知识 conformance 测试 | 父版本测试声明和所需 kit commit；不是 runtime 依赖 |
| `.gitmodules` 与实际 gitlink | 仅绑定 workspace 业务子模块时 | 所选 commit、真实业务 HEAD、任务基线；branch=main 不授权更新 |
| 实际业务 vLLM-Ascend 的 CI 声明 | 业务组合核对 | 从实际/明确候选父 SHA 读取 vLLM pin，解析并核对完整双 SHA |

原 `remote_dev.py status` / `vaws.py status` 可报告定位、真实 checkout 与 pin 偏离，但仍要按任务核对所需接口。bootstrap 使用其父仓当前声明；`--track-ref` 会跟随分支，不作为满足固定 pin 的默认方式。保持父声明的 scope，不把 coordinator 变化误当 remote-dev pin 变化。

provider 安装是配置变更，需要原预览与本轮授权；保留用户维护的同名 command/args/type/env 与未知字段。原协调工具记录 task/session/run/execution，上层仅引用，不能另起 manager 或写第二套 registry。

## 候选父提交的读取与切换

当候选对象已在本地，使用 `git show <candidate-sha>:<声明文件>` / `git ls-tree` 读取，不为看声明先切当前 branch。若缺对象，明确来源与本轮联网范围后定向获取。绑定目标父完整 SHA，移动 ref 的名称只做来源说明。

顺序是候选父约束 → 必需下层准备 → 组合验证 → 最终切换。可以用隔离的候选目录读取/调用目标父入口，但先确认 helper 的共享根、状态目录和 env，避免它自动触碰在用 provider。目标约束与旧父 pin 不同的情况下，旧 helper 的成功不证明目标组合；使用候选父原入口或提出具体适配方案。

切换前留旧父/下层 SHA、原路径/定位方式、dirty 与活跃实验引用。处理本机复用 checkout 时，不把其分支/dirty 当工作台所有，未经相应授权不移动。最终顶层 gitlink、lock commit 与实际 checkout 一致；init 使用既定版本，后续升级不漂移成“最新”。

若无法隔离共享运行状态或必需验证不可执行，保留原组合，输出候选方案与缺口；不静默降低验收标准。回退也先核对当前实际状态和授权，不能重置用户改动。

## 验证不是文本 status

- 来源：真实 remote 身份、独立 Git 根目录、完整 SHA、声明来自准确父版本。
- 方法/skill：代表请求的路由、适用边界与行为；静态格式检查不证明实际行为。
- 脚本/协议：检查所需命令参数、必需文件、结果字段与版本兼容；按影响做可执行测试，不只匹配文件文字。
- runtime/远程：原 provider 状态与所需实际调用/目标环境验收分别报告，bootstrapped 不等于端到端可用。
- 业务：保留实际开发 branch 与任务基线，核对 CI pin/双 SHA 不触发 checkout；静态配对不证明精度或性能。
- 可选测试：只在相关测试/CI 启用时核对 kit 并运行适用测试，未启用保持 not_enabled。

日常核对不默认联网更新；正式性能/精度实验记录固定基线，升级单独形成记录。最终结论限定检查范围，不能因三个顶层 HEAD 正确声称所有传递依赖或 NPU 能力已验收。
