# 依赖图、候选版本与验收

## 事实源与记录

按[共享配置约定](../../ascend-workbench-init/references/config-schema.md#路径与缺省值)读取实际来源锁和报告。sources.<id>保存顶层{path, url, commit, purpose, declared_dependencies}；本机dependencies.<id>.path可绑定外部维护源。先核对真实源与SHA，不仅以目录名判断。

`declared_dependencies` 是下层原文件引用，必须从本次所选父提交读取；它不是一个可以独立更新的上层 pin 列表。候选父新增声明时主动识别相关入口，不能只检查旧 lock 已列文件。下层 pin 保持原文件权威，上层保存检查快照与引用即可。

完整受影响图与验证保存在本次维护任务results；无业务任务时建立维护任务。实际路径、环境和本机原件引用不进入公开开发记录；公开记录仅保存通用方法、公开来源版本、采用决定与验证层级。不另造状态数据库。本机节点行至少包括：

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

## 能力发现入口维护

新增或升级来源时核对[统一检索入口](../../../../upstream/skill-mapping.md#依赖能力发现入口)，并对照[现有场景关系](../../../../upstream/skill-mapping.md#细分能力目录)区分新能力、已有能力增强/修复、接口变化和删改/弃用。输入、阶段、产物相同只表明重叠，还需评估分析准确性、覆盖、报告、步骤成本或实测效果；旧入口仍可工作不能替代这项比较。新版本中未采用的无关能力不触发全量业务回归。

沿实际消费链追踪原SKILL、references、scripts、声明及测试到项目调用方、本地patch和旧版限制。复核放在现有reference或本次升级记录，不另造pin或状态库：

| 应记录的关系 | 判断与行动 |
|---|---|
| 上游资源与项目消费方 | 哪个流程/脚本/模板被调用，输入输出和实际工具是否变化；新版可直接满足时不重写一套实现 |
| 本地适配及原理由 | 是项目授权/记录要求、环境差异，还是上游旧缺陷的临时规避；区分仍需保留与可能退役的部分 |
| 原事实和重新核验条件 | 固定版本仍以lock为准；相关源码/接口/依赖变化时重跑能检出原问题的代表输入或行为走查 |
| 采用与清理结果 | 明确继续旧版、直接采用新版或保留薄适配的理由；验证覆盖的旧patch/例外删除或改引用，未解决的具体差异保留 |

实际能力使用不要求先封装为自有skill。复用上游流程和工具时只适配明确不兼容处，并按已有任务授权执行；本地源码副本不承载任务输出和临时修改。采用变更时同步受影响映射和直接reference，覆盖正常输入、不适用输入、缺工具及原缺陷的复验；被替代的说明合并，不维护第二套优先级。

方法增强用同一问题/证据核对结论与覆盖，脚本修复检查实际输入输出及失败路径，执行接口变化核验真实接口，性能/精度收益需适用环境测量。只有源码差异时报告源码判断或待验，不宣称效果提升。切换与回退按前节执行，不能在活跃业务实验中无声更换基线。

## 验证不是文本 status

- 来源：真实 remote 身份、独立 Git 根目录、完整 SHA、声明来自准确父版本。
- 方法/skill：代表请求的路由、适用边界与行为；静态格式检查不证明实际行为。
- 脚本/协议：检查所需命令参数、必需文件、结果字段与版本兼容；按影响做可执行测试，不只匹配文件文字。
- runtime/远程：原 provider 状态与所需实际调用/目标环境验收分别报告，bootstrapped 不等于端到端可用。
- 业务：保留实际开发 branch 与任务基线，核对 CI pin/双 SHA 不触发 checkout；静态配对不证明精度或性能。
- 可选测试：只在相关测试/CI 启用时核对 kit 并运行适用测试，未启用保持 not_enabled。

日常核对不默认联网更新；正式性能/精度实验记录固定基线，升级单独形成记录。最终结论限定检查范围，不能因顶层 HEAD 正确声称所有传递依赖或 NPU 能力已验收。
