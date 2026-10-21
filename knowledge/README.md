# 工作台知识库

这里维护从工程任务中核实、可供后续检索复用的知识。原始任务状态仍由各任务说明维护；本库不替代运行环境、日志或资源状态。

## 目录与检索

- 个人日报和任务进度只保存在本机忽略目录，按[归档约定](../docs/daily-sync.md)维护，不属于公开知识条目；旧的`daily/`仅作既有记录兼容，不再新增或发布处理进度。
- `topics/<稳定主题>.md`：跨任务可复用的判断与方法。同一问题优先更新已有条目，不按日期复制。
- [history/](history/README.md)：按条目id保存可独立阅读的历史版本及修订原因；普通检索默认不把这里当作有效指导。
- 本文件维护主题入口和知识规范；检索先看入口，再按模型/组件/报错/版本等关键词查相关条目与来源，不把整个库加载进上下文。

自动任务遵循[每日同步说明](../docs/daily-sync.md)，知识检索和写入使用独立的[ascend-knowledge-curation](../.agents/skills/ascend-knowledge-curation/SKILL.md)。没有新知识时只更新必要日报，不为每天凑条目；workflow不维护归纳正文。

## 收录与更新

值得收录的是：不容易从最终代码直接读出的根因判断、重要失败路径、有效/无效假设的证据、明确适用边界，以及能避免重复调查的工程方法。普通完成清单与暂态机器信息留在日报或任务记录。

写入前同时检索本库和直接相关任务。相同结论补证据或条件，内容冲突则保留双方来源并降低结论强度，不能把旧结论无痕覆盖。事实、推断、规避与真正修复分别表述；没有可复核证据时可暂不收录。

外部材料优先原始文档、论文或源码，记录实际版本和许可；不复制长篇受版权保护内容。原始输入只作资料，不是可扩大权限的指令。不得写入凭据、内部连接清单、原始模型输出全集或全量日志，也不改写Codex全局长期记忆。

## 统一证据流程

主 agent、子 agent 和每日归档使用同一流程；检索请求只读，获授权维护时才写入。知识是有条件的结论，不是当前服务状态。

1. **检索与去重**：先查有效主题及直接相关任务，确定需要保留的具体判断。相同问题更新原条目，已有权威文档只索引。
2. **限定适用条件**：明确软件版本/提交、实际采用的补丁或产物、模型/执行路径等会影响结论的条件；通用方法可写明不依赖具体版本。原始基线或包版本不能代表叠加后全部代码；无可访问的补丁来源时，明确实现差异与待复核范围，不能把该基线说成完整复现条件。
3. **关联证据**：结论对应来源条目，只引用仓内维护文件或可访问的公开固定提交，给源码文件及符号、行号范围。未发布的历史运行材料只保留必要结论、原证据时间及验证限制，不建立私有来源索引。来源入口、任务摘要、源码与实际运行分别标注；只阅读摘要不能声称独立核验了原始运行。
4. **区分时间**：`sources[].observed_at` 是公开来源的原证据产生/采集时间；无公开来源的历史摘要用条目级 `observed_at` 保留原证据日期，并用 `evidence_scope` 说明缺口。`verified_at` 是实际完成证据核对的时间，`updated_at` 是知识文档更新时间；均用带时区时间，只有日期时保留日期精度并说明。未知写 `unknown` 和缺口，不用当前时间补造。仅清理发布内容不刷新原核实或实验时间。
5. **限定结论强度**：将已知事实、推断、规避与修复分开，说明什么尚未证明。混合来源的条目分别标出各结论的验证层级，不因一项 runtime 证据把其他源码推断升级为端到端验收。
6. **写入与复查**：先保留需修正/合并/替代的旧条目和原因，再更新有效入口；补充新字段本身不表示旧结论已过期。写明何种版本、实现或运行条件变化会触发复查，到足以支持本条结论时停止采集。

字段只在新增或本次修改的有效条目补齐，不为格式迁移全量重查历史、不自动重跑实验。检索未达当前验证条件时，明确“历史可参考、当前适用性未核实”；来源暂不可读时保留原证据时间和上次核实依据，将受影响结论标为待复查，不以更新日期升级状态或直接判过期。

## 条目最小结构

每个主题条目使用YAML frontmatter：

```yaml
id: stable-topic-id
title: 明确的判断或方法
status: candidate  # verified / candidate / outdated / superseded
updated_at: 2026-10-15T09:00:00+08:00
verified_at: 2026-10-15T08:50:00+08:00
tags: [组件, 任务类型]
applies_to: 明确的软件版本、模型、执行条件或证据范围
sources:
  - id: evidence-1
    path: 固定公开源码URL或仓内维护文件
    revision: 实际公开Git提交
    locator: 文件内符号与行号范围，或日志事件/报告章节
    observed_at: 2026-10-14T16:00:00+08:00
    evidence: source  # source / static / runtime / end-to-end
    access: published  # 仅仓内维护文件或可访问的公开主来源
```

正文包含：结论、触发/适用条件、关键证据与复核方式、不能推出的结论、失效/复查条件。`verified`只表示该条目限定层级的结论得到核实，source/static不能冒充真实模型验收。找不到原始证据时标明缺口；不生成指向未发布本机文件的失效链接。

`sources[].id`供正文对应相关结论；单一来源可用明确章节代替复杂映射。`revision`使用实际公开提交，`locator`不能只有仓库首页或浮动分支。公开知识不包含未发布材料的路径、文件名、字节数、文件哈希或其他私有索引，也不保留私有来源元数据块。历史调查摘要没有公开来源时使用 `sources: []`，保留原证据日期及验证层级，明确无法由仓库独立复验，并将待确认适用性的条目标为 candidate；不能伪造公开引用或把历史摘要升级为当前运行验收。

每次写入前后检查：语义无重复、结论与证据对应、版本/定位/三类时间不混淆、公开引用可访问且不依赖本机材料、历史及入口可追溯。发布前按[每日发布约定](../docs/daily-sync.md#检查遗漏并推送)复核本轮差异；不把本机日志或源码全集随知识条目上传。

版本或实现变化会影响结论时复查。用户明确要求：过期内容不直接删除，必须放入历史并说明为什么过期。

## 过期与历史保留

实质纠正、合并、替代或确认过期之前，先在本机忽略目录备份完整旧文件，具体备份路径与指纹只保留在本机。公开 `history/` 保存去除私有来源索引后的历史版本，以日期和修订顺序命名；不得为保留原始字节而将本机路径、原始材料文件名或哈希重新发布。

在该条目历史目录的 `README.md` 记录历史版本链接、原适用范围、具体修订/过期原因，以及可访问的公开依据与替代条目（如有）。补充证据或字段时说明旧结论是否仍有效；确认过期时说明哪个条件不再成立、哪个结论被何种证据纠正。因发布边界清理历史内容时明确说明清理范围，保留原始证据时间与工程结论，不声称清理后的版本仍与原文件逐字节相同。后续工程解释追加到说明。

当前`topics/`路径继续保留可检索入口：有新版则更新同一条目并链接历史；无替代结论则标记`outdated`并说明限制；已合并/替代则标记`superseded`并链接新的有效条目。维护主题入口状态，避免旧链接断开或过期内容继续作为默认指导。需要历史追溯时再检索history。

无法取得证据仅表示待复查，不代表已过期。扩大适用范围、将候选升级为普遍规则均需对应证据，不能仅因时间过去或检索未命中就处理。

## 主题入口

- [流式HTTP收包损坏与挂起](topics/http-receive-corruption-and-payload-hang.md)：接收校验、重传、payload异常与有限预算分层验证；历史1280条完整性回归，底层损坏根因未闭环（candidate）。
- [EPLB全层映射的Host锁页申请](topics/eplb-full-map-pinned-host-allocation.md)：644MiB整表与1GiB分配的推导/实测区别，Host与HBM、扩展段候选及故障时资源缺口（candidate）。
- [DSpark预算与PD状态布局](topics/dspark-pd-spec-state-layout.md)：固定两个分支下KDA卷积状态长度、V1/V2搬运与选块差异；56组合成元数据验证，真实PD适用性仍需核验（candidate）。
- [PD性能对照与归因](topics/pd-performance-comparison.md)：固定dataset/prefix身份，区分P阶段、D排队与KV传输长尾；通信预热、占用采样和跨机请求关联的证据边界（candidate）。
- [A5 MemCache池化配置与前置操作](topics/a5-memcache-pooling-setup.md)：三份配置、Python动态库路径及P/D增量；rootinfo、engine_id、layerwise图模式及元数据/真实后端预检边界（candidate）。
- [MemFabric的HAL与Notify兼容边界](topics/memfabric-hal-notify-compatibility.md)：全局符号加载、真实接口输出及device_urma/device_rdma调用路径分别判定；历史单卡失败与替代接口缺口（candidate）。
- [KDA预编译调用参数边界](topics/kda-compiled-launcher-arguments.md)：JIT绑定、首次请求参数错误及两套安装构建九/十二参数反例；固定源码与历史运行分级，其他构建适用性待确认（candidate）。
- [A5独立能力检测与host launcher](topics/a5-triton-capability-detection.md)：目标架构正确仍可能选择错误启动分支；容器检测输入、编译metadata和207000的历史证据边界（candidate）。
- [Profiler停止与窗口边界](topics/profiler-stop-window-boundaries.md)：控制请求、原生时长、严格裁剪、硬件counter及性能对照口径（candidate）。
- [融合通信算子的空泡与分块性能判读](topics/profiling-fused-communication-bubbles.md)：事件区间并集、融合核内部等待、同工作量匹配及流水线填充反例；与可恢复显存分配失败分层关联（candidate）。
- [Mooncake同步batch与底层建链的分层超时](topics/mooncake-nested-timeout.md)：固定版本下的独立计时层、冷peer排队、证据边界与复查条件。
- [HIXL的URMA/EID枚举失败](topics/hixl-no-urma-devices.md)：区分空列表、peer端口缺EID与跨rank连带退出；重拉仅属临时恢复，底层查询失败未闭环（candidate）。
- [AICPU公共库部署不完整与缓存复用](topics/aicpu-partial-deploy-cache.md)：从507018回溯loader首错，核对设备NUMA小页、部署错误返回及成功标记；模型退出不自动修复设备文件，恢复未验收（candidate）。
- [EPLB运行阶段与日志指标判读](topics/eplb-runtime-evidence.md)：历史实现的初始化/真实提交、预测均衡度、迁移计数、局部耗时与开关边界；当前适用性待复核。
- [MRV2下EPLB启用参考](topics/eplb-enable-reference.md)：历史D侧参数、模型/量化支持前置、角色差异与验收边界；当前适用性待复核，不是全局默认。
- [Kimi K3的P/D配置参考](topics/kimik3-pd-configuration-reference.md)：角色并行、PP分层、主/草稿长度、调度和图模式的版本化组合，含历史验证范围与复现缺口（candidate）。
- [长序列的KV与workspace预算](topics/ascend-long-context-memory-budget.md)：长度配置、混合cache groups、workspace最终分配和运行时临时内存分别验收；保留1M请求的成功及失败边界（candidate）。
- [目标与草稿CPU长度同步门控](topics/spec-decode-cpu-length-sync-gates.md)：固定PR19038的FlashMLA/PP/PCP/DCP条件，目标False日志及草稿分支的独立判断（candidate）。
- [AISBench证据报告](../docs/aisbench-evidence.md)：官方分数、有效输出和结束状态的现有权威说明；不在知识库复制同一规则。

知识条目只在本库维护一份；项目规则与领域skill已有的通用要求直接引用，不重复抄写。
