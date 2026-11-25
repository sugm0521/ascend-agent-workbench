# npu-top 接入与局部定制

保留上游界面，服务器卡片显示中文错误摘要，详情页可展开完整 SSH 错误。默认隐藏已停用机器，页面上方的“显示已停用服务器”开关可随时打开；总览、左侧列表、服务器管理、历史选择与磁盘提醒一致生效，启用但离线的机器仍显示。切换仅改变展示，不修改机器启停状态，刷新页面恢复默认隐藏。原始错误、后端采集、认证和服务器状态仍由原 npu-top / remote-dev 实现管理。

左侧按“全部服务器”、各标签及“未打标签”折叠分组。点击分组标题框（含组名和数量）选择范围并切换展开/收起，点击箭头只展开/收起；收起列表仍保留当前筛选范围，键盘 Enter/空格也可切换，折叠状态继续记忆。一台机器可属于多个标签，“全部服务器”和组内汇总不会重复计数。总览卡片、在线数、NPU/HBM等指标、提醒、管理列表与历史选择跟随当前分组及停用开关；统计沿用上游按在线快照计算的含义，后端接口不改。窄屏可在页面上方的“服务器分组”下拉框切换，选择后展开对应侧栏分组。

在服务器管理页切换标签、“全部服务器”或“未打标签”时，保留管理页面并筛选表格，不跳转总览；切换范围后仍清空批量勾选。其他入口保持原有进入分组总览的行为。

左侧每台机器旁的“标签”按钮和管理页“编辑标签”复用原编辑入口，支持多个标签；保存后分组自动更新，删除当前分组的最后一个标签时回到全部服务器。系统“低优先级”标签仍按原规则保留。不会自动猜测或改写真实机器标签。

当前选中的分组及各组展开/收起状态保存在当前浏览器的本站点存储中，刷新或同一浏览器上下文新开页面时恢复；首次没有记录时从全部服务器展开开始。只有清单成功加载后才校验并保存，防止加载慢或失败时覆盖原记录；失效分组回到全部，并清理已不存在的折叠项。损坏或不可用存储不阻塞页面使用，停用显示开关和批量勾选仍不记忆。清理浏览器站点数据会清除这些偏好；它们不写服务器清单或工作台Git。

在“服务器管理”页勾选多台机器，或全选当前列表，即可批量操作标签。“添加标签”输入新标签，多个用竖线或逗号分隔；“移除标签”自动列出所选机器的已有标签及覆盖台数，勾选要移除的项，标签栏汇总当前选择。尚未勾选机器时先展示当前列表的标签，系统标签灰显不可选。标签包含逗号/竖线时也按完整标签移除；添加时去重，移除时保留其他标签及启停状态。

选择只针对当前分组和显示范围；显式切换分组或停用开关会清空选择，变更所选机器也会清理不再适用的标签选择。未确认回执的标签即使当前已不存在，仍可保留零覆盖候选进行无重复写入的核对重试。

批量应用前重新读取当前标签，按台保存并展示已保存、无需变更或未确认结果；已完成项保留，未确认的可见项保留勾选供核对后重试。处理中防止重复提交，更新不是跨机器事务。每台最多20个标签，每个最多60个字符；超限目标单独说明，不截断既有标签；系统“低优先级”不可批量移除。批量功能沿用原标签更新接口，不建立第二套服务器状态或批处理服务。

服务器管理页的同一组选框也支持“批量启用”和“批量停用”，只调整所选机器的监控采集状态。操作前读取最新清单，已处于目标状态的机器无需更新；逐台展示已启用/已停用、无需变更或未确认，失败不阻断其他机器，可核对后重试。停用后机器按默认显示规则隐藏；重新启用时先打开“显示已停用服务器”再勾选。标签和其他机器配置保持，处理期间禁止重复提交或变更勾选范围。

来源和三个运行包的唯一版本锁为 [npu-top.lock.json](../../upstream/npu-top.lock.json)。[manifest.json](manifest.json) 引用它，并校验定制补丁、编译资源和服务入口。[看板补丁](patches/dashboard.patch) 是全部定制源码；[frontend.zip](assets/frontend.zip) 是随 Git 分发的确定性编译资源，含构建标识和第三方许可。换机不需要重新手改代码。

## 普通安装和启停

需要 Python 3.11+（含 venv/pip）；实际监控 Linux 服务器还需要系统 SSH、原工具认可的服务器清单和本机登录授权。安装不需要 Node 或 Git 构建依赖。以下命令均在工作台根运行，`python` 应指向满足条件的解释器：

```powershell
python integrations/npu-top/manage.py install --port 8788
python integrations/npu-top/manage.py start
python integrations/npu-top/manage.py status
python integrations/npu-top/manage.py check
python integrations/npu-top/manage.py stop
```

默认运行目录为 `.workbench-local/npu-top-managed/`，仅绑定 `127.0.0.1`。访问 `http://127.0.0.1:8788`；已有端口被占用时拒绝启动，不停止占用进程。首次默认空清单，不自动探测已有服务器或重新启用失败目标，也不设置开机自启。安装会校验三份官方 wheel、隔离创建环境并执行 `pip check`；安装失败保留旧版本指针和现场。

已有生产看板不会被自动接管。先查明并停止其原入口，再选择复用原数据库与清单；需要迁移数据库时在停机状态备份，包括相关 SQLite WAL 文件。运行目录、数据库、清单和密钥继续留本机。已有数据库中的启用服务器可能在启动后继续采集，复用前应核对清单与停用状态。

自定义本机路径和接入清单时，先停止当前受管实例。`--runtime-root` 是全局参数，必须放在子命令前：

```powershell
python integrations/npu-top/manage.py --runtime-root "./.workbench-local/my monitor" install --port 8790 --state-dir "./.workbench-local/my monitor/state" --inventory "./config/machines.local.json"
python integrations/npu-top/manage.py --runtime-root "./.workbench-local/my monitor" start
python integrations/npu-top/manage.py --runtime-root "./.workbench-local/my monitor" stop
```

清单须为原工具的 `{"machines": [...]}` 格式，可重复传入 `--inventory`；不复制另一套账号或凭据。安装不连接服务器，启动后由原监控按已配置清单工作。重复安装复用校验通过的版本；重复启动返回现有受管实例。运行中拒绝改端口、数据库或清单，停止通过实例令牌请求原服务正常退出，不凭端口杀进程。

## 在线准备、离线部署与换机

在线安装只下载版本锁列出的三个官方 wheel，并验证 SHA256；网络代理使用 Python 的系统配置，不写固定代理。离线包只含官方 wheel、编译资源及校验元数据，不包含个人状态：

```powershell
python integrations/npu-top/manage.py bundle --output .workbench-local/npu-top-offline.zip
```

将同一版本的工作台和离线包带到新路径或新机器，在目标工作台根执行：

```powershell
python integrations/npu-top/manage.py install --offline --bundle .workbench-local/npu-top-offline.zip --port 8788
python integrations/npu-top/manage.py start
```

`--offline` 不访问包索引；缓存缺失或哈希不符立即失败。离线包也必须匹配当前版本锁和前端哈希。新机器单独准备 Python、SSH 和实际服务器访问条件；私有清单、数据库与凭据按使用者明确选择迁移，不进入 Git。虚拟环境总是在最终路径重新创建，不能复制或移动旧 venv。

每次成功安装保留旧受管 release；停止服务后 `rollback` 可切回上一个完整性检查通过、后端包版本相同的 UI 定制。不会自动回滚数据库，也不会跨后端版本回退；后端升级应另定数据库兼容与迁移方案。

## 维护与验证

受管服务启动时，会对锁定版本的采集脚本应用组件内适配：保留服务器已有 `LD_LIBRARY_PATH` 顺序，随后补充系统库路径，再追加驱动库目录，防止驱动目录抢占系统库优先级而使 `npu-smi` 卡住。设置只作用于单次远端探查，不修改服务器全局环境或驱动；主探查失败保留原输出，并补充退出码，124明确显示超时。原命令超时预算、成功采样与可选采样的降级规则不变。

该适配由受 manifest 哈希校验的 `service.py` 维护，在原采集器初始化前生效，不手改安装包。固定上游脚本的预期位置变化时拒绝启动，升级后需重新审查适配，不能静默跳过。组件测试用合成命令检查库顺序、失败输出与退出码、可选 usages 失败不污染主探查，以及重复应用和上游漂移；这些 shell 检查需要 Bash（Windows 可用 Git Bash），普通安装不需要它。

控制JSON原子写入对Windows临时读锁做有界重试；心跳写入失败仍继续监听实例令牌停止请求，避免一次文件占用使控制线程永久退出。过期心跳的停止仍只写对应令牌，不按端口或PID终止进程。组件测试包含瞬时/持续写入失败及停止路径。

开发者重建使用 Python 3.12+、Git、Node（版本要求见上游 package.json）和 npm；普通安装仍只需 Python 3.11+。构建从固定官方源码包开始，校验哈希、重放补丁、`npm ci`，依次执行上游与定制测试、lint、TypeScript 检查及 Vite 构建。包内固定时间戳，不包含构建路径或服务器数据：

```powershell
python integrations/npu-top/build.py
python integrations/npu-top/build.py --check
python -m unittest discover -s integrations/npu-top/tests -p test_*.py -v
```

首次构建更新资源与 manifest；`--check` 在另一个干净源码目录重建并比较哈希。仅修改服务入口时，更新 manifest 的 service SHA256，执行组件检查与干净目录离线实装；前端补丁变化时重新构建资源及校验元数据。版本更新只修改权威锁，检查上游变化后再更新补丁、制品和验证结果，不自动跟踪 latest。

离线实装检查要求全新运行目录和可用空闲端口。脚本移除 Node/Git 所在 PATH，使用空服务器数据库，验证重复安装/启动、端口冲突、HTTP 资源、运行中配置拒绝、损坏制品拒绝及正常停止：

```powershell
python integrations/npu-top/tests/deploy_smoke.py --bundle .workbench-local/npu-top-offline.zip --runtime-root .workbench-local/npu-top-smoke-new
```

换路径验收应从拟交付 Git 文件导出全新工作台，在新路径执行同一脚本，不能引用原任务目录或原虚拟环境。此入口验证本机安装与运行；真实第二台机器、远程 SSH 和 NPU 采集需要对应环境单独验证。
