# 上游消费、吸收与更新

来源身份/版本只有[来源锁](../../upstream/sources.lock.yaml)及gitlink这一套；实际路径/选择来自本机配置，父版本的下层约束从原声明读取。已发现、已采用、已验证和已吸收分开，不因新提交或名称重叠自动换源。

## 消费声明

实际消费方在references/upstream-usage.json保存schema_version=1、consumer和uses数组。consumer等于本模块目录名；每个use包含source_id、仓内相对resources、relationship、when/purpose、upstream_basis_revision及local_adaptation/recheck_on。

| relationship | 含义 |
|---|---|
| skill_call | 在when条件下进入原/本仓子流程，需核对其工具前提和本项目授权 |
| tool_call | 调用原脚本/工具；接口、实际解析路径与版本另核 |
| rule_reference | 读取领域/共用规则，不是递归执行子流程 |
| method_reference | 选择性参考/融合方法或输入/输出契约，不表示已执行原工具 |
| template_reference | 按需参考模板，保留原许可和项目输出位置 |
| provenance | 历史溯源，不自动成为当前运行依赖 |

workbench是本仓相对资源，不新增自依赖或复制工作台pin；外部id必须来自lock。resources不可绝对或越出所属源。只有实际采用的关系进uses；候选和普通导航在领域reference/发现目录，初始化/检查对象不写成skill_call。provenance指历史出处，不要求旧资源在新候选提交中继续存在，也不据此增加运行影响；历史依据本身仍按可读性单列检查。

upstream_basis_revision是已核对的参考/吸收历史依据，不是第二套运行pin。未知为null，不能把当前pin补成虚构历史；新引用的固定版本也只支持声明的reviewed_scope。当前声明的“方法/契约范围”不等于所有源变化已吸收或工具/NPU通过。适用/验证描述给公开可复验方法，实际机器就绪和私有证据留本机任务。

Markdown解释理由与边界，来源/资源机械事实只在JSON维护。引用规则与执行边分开；条件交接可能形成图中回边，不能仅凭普通链接或rule_reference判执行循环。子依赖的真实循环/冲突仍须报告。

## 检查、比较和采用

日常任务只核对本轮实际前提；用户要求检查、发布准备、来源/声明变化或相关能力缺口时按范围检查。周期检查需另有调度授权，不在实验中自动追新。

同时比较：①已采用版本到候选；②各消费方历史依据到当前/候选。远端无新提交仍可能有待吸收项。方法增强、修复、脚本/接口变化与新增能力均检查；SKILL未变也要看使用的reference、脚本、模板及下层声明。

1. 保护dirty/staged、正在运行的实验和实际工具绑定；读取候选父版本声明，先定相关约束。
2. 对照旧上游、新上游和本仓方法，检查实际受影响消费方；未采用候选不形成全生态回归门禁。
3. 方法用同一问题/证据评审，工具验证真实输入输出和失败路径，必要运行效果在适用环境验证；静态/离线/模拟/NPU分开。
4. 决定保留旧版、直接受益、选择性融合、补缺、暂缓或不采用，并记录理由和知识适用性变化。纯方法增强可待吸收，但不得宣称完成全部融合。
5. 切换前解决受影响已采用能力的必需接口/正确性冲突，同步gitlink/lock、资源路径和必要适配；验证后才退役对应旧patch/例外，项目授权/证据要求仍保留。
6. 失败保留旧组合及证据。若实际升级执行环境，优先隔离候选并保留原环境/入口/绑定，使用原工具的恢复方式和必要smoke；纯方法/引用变更不追加环境升级/恢复系统。

临时新版本补位必须能真实绑定候选而不破坏共享provider，记录任务实际版本与路径；复制目录不证明运行隔离。提交/推送与正式接入按具体已有授权，业务vLLM/Ascend配对仍按自身CI pin，不随skill升级切分支。

## 只读检查辅助工具

脚本[inspect_upstream.py](../../scripts/inspect_upstream.py)直接读取权威YAML及消费JSON，不要求agent转抄另一份配置。需要Git和可用PyYAML解析器，单独声明在[可选工具依赖](../../scripts/requirements-upstream.txt)；不自动安装，不修改现有MCP/执行环境。缺解析器明确退出，不能用浅字符串提取冒充配置验证。

```sh
python scripts/inspect_upstream.py --source workspace --output <本次任务结果目录>
python scripts/inspect_upstream.py --source msagent --candidate msagent=<本地候选ref>
python scripts/inspect_upstream.py --all --check-remote --output <本次任务结果目录>
```

--source或--all明确范围；默认仅本地，--check-remote才查询远端HEAD元数据，不fetch/checkout/安装/执行上游。--root明确工作台，--config可指定本轮本机配置；显式指定的文件缺失/不可读时报配置错误，只有未指定时默认本机配置缺失才按未配置处理。已跟踪消费声明在工作树缺失、或声明所属skill缺失同样报错，不能静默构造不完整消费图。报告只写指定任务目录并保留历史。

源的changed/no_source_delta仅描述版本差量。JSON、终端和Markdown另给inspection_status：complete表示本次事实检查无未完成项，review_required表示有变化/待吸收或未知历史依据，incomplete表示有来源/网络/已知历史提交不可读等缺口。退出0只表示事实收集完整，仍可能需语义复核；退出1表示不完整，退出2表示配置/输入/前置错误。未知依据null保持待复核，不自动失败或补造历史；已知依据缺对象则为needs_fetch并使检查不完整。所有状态均不代表工具/NPU或升级采用通过。

needs_fetch、unknown_basis、pending_decision、not_enabled、missing_resource、identity_mismatch与网络/解析错误分别呈现；不能统一写up_to_date。source内容变化而间接引用不明确时，保守标需复核，不报无影响。即使采用版本没有新增候选，历史依据到评估版本的差量也进入消费方影响复核；未知依据仍单列缺口，不能据空影响列表宣称吸收完成。helper只收集事实、不挑最好skill、不改正文/pin，最终吸收和验证决策由维护流程负责。
