---
id: mooncake-nested-timeout
title: Mooncake同步批量等待与底层建链预算需要分层核对
status: verified
updated_at: '2026-10-15T19:23:21+08:00'
verified_at: '2026-10-15T16:52:33+08:00'
tags:
- Mooncake
- KV传输
- 超时
- 冷启动
applies_to: Mooncake v0.3.11.post1固定提交的Python同步batch/Ascend ADXL路径；vLLM-Ascend helper仅作历史实现观察；运行观察限2026-10-15，目标实现仍须核对
sources:
- id: mc-binding
  path: https://github.com/kvcache-ai/Mooncake/blob/e9c61075720039bcfc5fffd19f847608402be3d0/mooncake-integration/transfer_engine/transfer_engine_py.cpp
  revision: e9c61075720039bcfc5fffd19f847608402be3d0
  locator: TransferEnginePy构造函数L100–107；batchTransferSync的超时检查L547–551
  observed_at: '2026-10-15T16:50:45+08:00'
  evidence: source
  access: published
- id: mc-connect
  path: https://github.com/kvcache-ai/Mooncake/blob/e9c61075720039bcfc5fffd19f847608402be3d0/mooncake-transfer-engine/src/transport/ascend_transport/ascend_direct_transport/transfer_executor_base.cpp
  revision: e9c61075720039bcfc5fffd19f847608402be3d0
  locator: ParseExecutorEnvIntoInitParams L66–82；checkAndConnect L245起
  observed_at: '2026-10-15T16:50:45+08:00'
  evidence: source
  access: published
---

# Mooncake同步批量等待与底层建链预算需要分层核对

## 结论与适用条件

调整内层等待后仍在固定时长失败时，先定位实际返回超时的调用层。本版本Python同步batch有独立外层预算；冷peer的串行建链和排队可能使其提前返回。单条连接在各自期限内成功，不能推出调用已在外层期限内完成。

本条 verified 仅覆盖所列公开固定源码事实。历史调查摘要记录于2026-10-15，运行片段为当日11:27–11:35；原始运行材料未发布，摘要不作为仓库可独立复验的运行证据，本次整理没有重新验证服务已修复。

## 三个变量的分工

| 变量 | 单位与控制层 | 消费时机及证据 |
|---|---|---|
| ASCEND_CONNECT_TIMEOUT | 毫秒，单次ADXL Connect等待 | Ascend执行器初始化参数解析；mc-connect |
| ASCEND_TRANSFER_TIMEOUT | 毫秒，底层数据传输预算 | Ascend执行器初始化参数解析；mc-connect；历史helper观察为显式值优先，目标实现待复核 |
| MC_TRANSFER_TIMEOUT | 秒，Python同步batch外层基础等待 | TransferEnginePy构造函数读取；该版本缺省30秒、显式值最小按5秒处理；mc-binding |

mc-binding的batch截止条件为基础等待加`total_length`纳秒，后者是源码中的按字节数增加的预算。不能把基础预算当成精确且与数据长度无关的硬截止，也不能用底层传输预算替代外层接口预算。

历史核对的 helper 中 `get_transfer_timeout_value()`优先返回显式ASCEND_TRANSFER_TIMEOUT；未设置时按HCCL_RDMA_TIMEOUT/RETRY_CNT推导，再由连接器初始化写入。故“没有手写export”不等于“没有底层传输预算”。该观察没有公开补丁来源，只作为复查线索，不能替代目标版本的消费逻辑核对。

变量应进入相应引擎构造/初始化使用的环境。启动命令里的export、进程初始环境和组件实际解析日志分别记录；仅修改另一个shell不证明存量worker生效。

## 证据与复核方式

- mc-binding：[固定提交构造函数](https://github.com/kvcache-ai/Mooncake/blob/e9c61075720039bcfc5fffd19f847608402be3d0/mooncake-integration/transfer_engine/transfer_engine_py.cpp#L100)及[batch检查](https://github.com/kvcache-ai/Mooncake/blob/e9c61075720039bcfc5fffd19f847608402be3d0/mooncake-integration/transfer_engine/transfer_engine_py.cpp#L547)，可按固定提交重新检查。
- mc-connect：[参数读取](https://github.com/kvcache-ai/Mooncake/blob/e9c61075720039bcfc5fffd19f847608402be3d0/mooncake-transfer-engine/src/transport/ascend_transport/ascend_direct_transport/transfer_executor_base.cpp#L66)及[Connect互斥](https://github.com/kvcache-ai/Mooncake/blob/e9c61075720039bcfc5fffd19f847608402be3d0/mooncake-transfer-engine/src/transport/ascend_transport/ascend_direct_transport/transfer_executor_base.cpp#L245)，同一实例的冷连接可能串行等待。
- 历史调查摘要记录连续三次26.449、25.384、25.330秒建链，每条小于该次60秒预算，累计超过外层30秒。原始运行材料未发布，因此该数值例子只说明内外预算的区别，不能作为当前部署验收；本次未运行服务器。

## 不能推出的结论

60秒建链、180秒底层传输、300秒外层等待只是该任务试验配置，不是本条提供的通用默认值。历史证据支持避免单次建链/外层等待提前超时；没有独立证据证明底层传输180秒始终必要。

放宽预算是容错调整，不能证明冷链变快、所有KV请求成功或根因修复。EPLB/HIXL共存抢核是可能解释，缺少隔离证据，不能写成已确认根因。一个路径的采样不能外推全节点；人工停止后的退出也不能统一归因于此前通信失败。

历史运行与 helper 观察均不提供仓库可独立复验的证据；使用者须核对目标实现与当次运行，不能据此声称当前部署已验证。当前EPLB日志含义另见[运行阶段与指标判读](eplb-runtime-evidence.md)。

## 失效与复查条件

安装版本、Python预算算法、变量读取/覆盖顺序或Connect互斥实现改变时，重查相应来源。来源暂不可读时保留已核实范围和缺口，不按更新时间延长结论效力，不默认重跑实验。

## 历史

本次补全变量分工与统一证据字段，旧结论仍有效。已清理私有索引的历史版本及修订依据见[历史记录](../history/mooncake-nested-timeout/README.md)。
