---
id: a5-memcache-pooling-diagnostics
title: A5三级池化的初始化、查询等待与回收停滞诊断
status: candidate
updated_at: '2026-10-26T14:54:10.075160+08:00'
verified_at: '2026-10-26T14:54:10.075160+08:00'
observed_at: '2026-10-24'
tags: [A5, MemCache, UBSIO, UDMA, 大页, rewarm, batch_query, reclaim_throttle]
applies_to: memcache_hybrid/memfabric_hybrid1.3.0、CANN9.2及历史叠加Ascend连接器；SDK二进制与模型源码须另行固定，错误码不可跨版本套用
evidence_scope: 保存的原生日志、计数、线程栈、配置及已部署库的静态符号/反汇编摘要；完整构建与原始材料未公开，不能由仓库独立复验；本次仅整理并复核已有小型证据，不执行修复或故障注入；本次另核对固定公开UBSIO错误枚举、Put/补偿取片及vLLM阶段统计源码；源码关系不证明部署SDK逐字节一致或历史索引空洞因果
sources:
  - id: kvc-error
    path: https://github.com/openeuler-mirror/ubs-io/blob/90ece96c110ec0ca34de8271cda821643e479523/ubsio-kv/src/csrc/utils/ubsio_kvc_err.h
    revision: 90ece96c110ec0ca34de8271cda821643e479523
    locator: KvcError L21-31
    observed_at: '2026-10-26'
    evidence: source
    access: published
  - id: bio-error
    path: https://github.com/openeuler-mirror/ubs-io/blob/90ece96c110ec0ca34de8271cda821643e479523/ubsio-boostio/src/common/bio_err.h
    revision: 90ece96c110ec0ca34de8271cda821643e479523
    locator: Error L23-51
    observed_at: '2026-10-26'
    evidence: source
    access: published
  - id: put-offset
    path: https://github.com/openeuler-mirror/ubs-io/blob/90ece96c110ec0ca34de8271cda821643e479523/ubsio-boostio/src/sdk/mirror_client.cpp
    revision: 90ece96c110ec0ca34de8271cda821643e479523
    locator: MirrorClient::PutImpl L1139-1160
    observed_at: '2026-10-26'
    evidence: source
    access: published
  - id: tombstone
    path: https://github.com/openeuler-mirror/ubs-io/blob/90ece96c110ec0ca34de8271cda821643e479523/ubsio-boostio/src/cache/write/wcache.cpp
    revision: 90ece96c110ec0ca34de8271cda821643e479523
    locator: WCache::Put L186-238; CreateMemoryTombstone L261-295
    observed_at: '2026-10-26'
    evidence: source
    access: published
  - id: meta-data-slice
    path: https://github.com/openeuler-mirror/ubs-io/blob/90ece96c110ec0ca34de8271cda821643e479523/ubsio-boostio/src/cache/write/wcache_tier.cpp
    revision: 90ece96c110ec0ca34de8271cda821643e479523
    locator: WCacheTier::GetMetaDataSlice L212-229
    observed_at: '2026-10-26'
    evidence: source
    access: published
  - id: vllm-phase-stats
    path: https://github.com/vllm-project/vllm/blob/ced6857afa0ea7b2e3f0846a62e1394e90f15607/vllm/v1/metrics/stats.py
    revision: ced6857afa0ea7b2e3f0846a62e1394e90f15607
    locator: IterationStats.update_from_finished_request L531-584; queued_time L543; prefill_time L547
    observed_at: '2026-10-26'
    evidence: source
    access: published
---

# 按实例、rank和调用层诊断池化

先记录容器ID、服务UUID、主PID/starttime、worker到pool rank映射、实际配置与成功启动边界。同一输出目录可能由新PID复用，旧错误不能自动归入新实例。先对齐各机原始时区与本次日志区间，再比较故障；全池Meta事件不能全部归因于某两个P worker。配置教程见[三级池化教程](a5-memcache-tiered-pooling-tutorial.md)。

## 1. 初始化失败：从首错走到连锁退出

| 首个证据 | 应确认的层次 | 不能直接得出的结论 |
|---|---|---|
| conf是symlink、Failed to setup config | SDK配置安全检查与真实消费路径 | Meta没启动是唯一原因 |
| rootinfo打不开、UB Entity不匹配 | 安装构建实际读取路径、rank/通信plane | 生成rootinfo就补足硬件链路 |
| UBSIO内存额度检查失败 | 同一故障时刻、该rank的预算和返回值 | 当前MemAvailable就是故障时检查额度 |
| 其他rank Gloo peer closed | 首个退出worker与同步屏障传播 | 所有rank都有独立内存故障 |
| 外部API健康但LocalService容量0 | 代理、Meta与注册分层 | 模型池化已就绪 |

历史40GiB缓存请求大于检查到的26.53GiB额度，随后UBSIO失败并断言退出，其他rank在屏障报peer closed。该例证明要追首错；没有取得额度公式，不把减少缓存或清文件页写成普遍修复。配置变更应由使用者决定，不能通过擅自降低需求“通过验收”。

## 2. 可用内存很多，仍可能卡大页分配

历史一个worker通信线程进入：

```text
reclaim_throttle
  ← memory direct compact/reclaim
  ← udma_remap_hugepage / udma_alloc_u_hugepage
  ← udma_alloc_u_sq_buf / uburma_cmd_active_jfs
```

同机仍有约805GiB MemAvailable，说明整机可用量不能单独排除该分配/整理路径阻塞；没有证明是通用驱动缺陷或单一碎片率阈值。用连续栈、rank等待关系、隔离页和实际线程进展定位，不能只看NPU占用。

旧`migratepages`曾持有大量隔离页；核对cgroup、PID/starttime和归属后清理，隔离页归零。后续模型`cpu_binding`主动启动的NUMA迁移是另一批正常任务，不能沿用旧清理名单。一次compact退出0、隔离页0与空闲NPU只代表启动前快照，不保证权重加载后仍满足大页及UBSIO条件。

NFS权重加载停滞也要独立排除：历史NO-CARRIER、VLAN LOWERLAYERDOWN、NFS目的不可达与READ不增长能定位到当时链路异常；物理、交换机或驱动根因仍不明。SSH能登录不代表NFS读取正常，换节点后能加载也不证明原节点已修复。

## 3. 注册成功与退出成功分开

历史64/64 rank初始化和UBSIO成功，保持至少20秒无ERROR，注册2.5TiB DRAM及约8TiB SSD；并发关闭时53个进程exit0、11个SIGSEGV(-11)，出现RemoveRanks transport not opened与空对象错误。两组事实同时成立。

少rank预检、全rank注册、模型常驻后初始化、三级读写和依赖关闭流程是不同验收门。退出后容量归零可符合客户端销毁预期；Meta还在不代表依赖退出没有缺陷。后来的新服务短时正常不自动关闭旧轮退出故障。

## 4. 同号错误码按组件解释

公开UBSIO固定提交的枚举可提供明确对照；以下值仅适用于所列源码版本，安装二进制仍需独立核对：

| 所属层 | 名称与值 | 不能直接推出 |
|---|---|---|
| BIO | `BIO_ALLOC_FAIL=5`、`BIO_INNER_RETRY=14` | 14不是内存池满专用码。[bio-error] |
| UBSIO-KVC | `UBSIO_KVC_ALLOC_FAIL=4`、`UBSIO_KVC_EAGAIN=5` | KVC的5不能套用BIO的5解释。[kvc-error] |

固定源码中`MirrorClient::PutImpl`先分配flow offset/index再发送Put，失败后flow处理受运行模式影响。[put-offset] 内存写入失败时可进入`CreateMemoryTombstone`，其`GetMetaDataSlice`继续取得元数据和数据切片。[tombstone][meta-data-slice] 这些可复核的源码事实支持检查“补偿也申请资源”的路径；仍未证明实际SDK版本相同、留下了哪一个索引空洞，或该空洞导致历史回收停滞。UBSIO源码采用Mulan PSL v2，本条只概述调用关系，不复制实现。


记录组件、函数、源文件/构建、输入对象和首个返回码。历史BIO、UBSIO-KVC及上层Batch put出现同号返回时，所属枚举/包装不同；不能将一个层的`5`解释直接移植到另一个层，也不能仅凭`14`宣布池满。配置解析、分配、写入、异步flush和模型请求失败要分别计数。

历史8机20/64问题worker的连续样本中，成功alloc/free/evict差分为0，而失败计数继续增加，支持“这些rank的回收/写入进展停滞”的判断。它不是失败模型请求数，也不表示其余rank相同。保存成功和失败计数的同窗差分比只报累计错误行数更有用。

一个待验证机制是：写入失败后tombstone或补偿元数据仍可能需要新的slice，满池时补偿再次失败，形成flow索引空洞并影响回收。现场停滞与静态路径是线索，**未做故障注入或逐对象因果关联，不能把该机制写成已确认根因**。

## 5. 本地高命中仍可能查询外部目录

历史一次请求总139287 token、本地computed138240，剩余仅1047 token，仍观察到5792键的组查询参数。本地命中未在该coordinator分支直接裁剪全部目录查询，且混合cache group的可达性语义仍生效。这个观察不能推出“应机械截断全部键”，裁剪需要保留组间一致性及对应源码契约。

连续Python样本曾进入`pool_scheduler → memcache_backend → batch_get_key_info`。反复出现说明该运行路径经常被观察到，不等于一次SDK调用连续阻塞了整个采样跨度。样本间对象地址不同、请求仍推进时，更不能把它们拼成单次耗时。

已部署1.3.0库的静态符号与反汇编支持：

```text
BatchGetKeyInfo → mmcc_batch_query → BatchQuery
  → MetaNetClient::SyncCall<BatchQueryRequest, BatchQueryResponse>
服务端 HandleBatchQuery → MmcMetaMgrProxy::BatchQuery → MmcMetaManager::Query
```

这不是一次完整C++运行栈。另一`GetByRank → PendingWaitAndFill → pthread_cond_timedwait`分支存在，**尚未证明该等待直接位于当前BatchQuery的实际调用路径**。没有请求级RPC/锁关联前，不能断言每次query都在等rewarm。

## 6. 审计计数、消息文本和健康接口的边界

| 历史观测 | 正确读法 |
|---|---|
| query增加6693756且fail增量0 | 全池目录请求计数；不代表低延迟或都属于一个评测 |
| rewarm与rewarm_fail都增加 | 先核对两个字段事件语义，不能直接相除当成功率 |
| 261条`timeout or no readable blob` | 是合并条件，不能全算超时 |
| 91条lease消息中60条waitedMs=0、31条约9–10秒 | 按原字段分布报告，不能说91条全等待10秒 |
| alloc/flush/evict持续增长 | 可说明对应工作在推进，不证明模型真正回读 |
| HTTP200但metrics body为空 | 指标内容不可用，不能写健康或延迟0 |
| 一次线程采样多数futex | 不足以确定哪把锁、哪个请求，不能称CPU饱和 |

若工具不支持所需的非阻塞native采样，保留缺口；不能为拿到栈自动切换会暂停业务的采样方式。精确关键词尾部出现0次，也不能证明整个日志不存在其他格式的错误。

## 7. 关联模型等待与当前状态

固定vLLM源码用首次SCHEDULED减QUEUED得到排队时间，用首次NEW_TOKEN减SCHEDULED得到prefill墙钟。[vllm-phase-stats] 若部署调度器在起点取时、随后同步查询再记录SCHEDULED，查询及同轮工作可能落入该prefill区间；公开统计公式本身不证明部署侧查询所占时长。部署侧三份连接器源码在记录基线下的固定公开路径不可取得，相关分支仍限历史快照，不把基线SHA当作完整可公开复现条件。


用response UUID、调度事件和同窗日志关联请求。一例tool→assistant间隔570.383秒、输出142 token包含可能的Agent编排等待，不能全归池查询。P侧`prefill`墙钟包含哪些等待取决于SCHEDULED等打点位置；一次4样本窗口的均值不能代替NPU算子时间或整个SWE吞吐。

旧实例有Put/flush失败，新实例短时分配与刷盘正常，要分别报告。后者不证明旧回收故障机制已修复；读取计数为0可表示未触发池回读，不能自动归为读取失败。正常本地prefix、Mooncake外部传输、池目录命中、真正DRAM/SSD读取和端到端收益各自核验。

早期没有原件支持的数值被撤回后，后续新采样应单独绑定时间和实例；不以新证据回填旧说法。需要进一步确认SDK客户端锁/序列化、RPC排队、Meta目录锁或回温竞争，必须取得同请求/键批次的关联证据。当前仍无修复A/B与长期回读验收。

## 复查触发

更换SDK构建、驱动/CANN、cache group、模型/并行、配置或实例后，重新核对上述调用链和指标语义。原件不可取得时降为历史线索；hash清单本身不是日志已存在的证明。部署教程与诊断不授权停止其他任务、清缓存、修改系统参数或重启服务。
