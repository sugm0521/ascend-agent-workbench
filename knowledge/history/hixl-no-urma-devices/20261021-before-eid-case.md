---
id: hixl-no-urma-devices
title: HIXL偶发No urma devices：临时恢复与继续定位的边界
status: candidate
updated_at: '2026-10-16T22:22:59+08:00'
verified_at: '2026-10-16T22:22:59+08:00'
observed_at: '2026-10-16'
evidence_scope: 公开固定源码已核对；2026-10-16运行及只读检查仅保留历史摘要，原始现场材料未发布；故障瞬间的DCMI查询结果缺失，底层根因未闭环
tags: [HIXL, ADXL, URMA, DCMI, A5, LocalCommRes, Mooncake, 启动失败]
applies_to: A5/Ascend950DT、CANN 9.2.0、HIXL自动生成version 1.3 LocalCommRes并用于Mooncake KV传输初始化的历史现场；其他版本、静态资源配置或通信路径需重新核对
sources:
  - id: hixl-rootinfo
    path: https://github.com/hicann/hixl/blob/fac0203cc317df29973850b49ff886997caacb20/src/hixl/engine/endpoint_generator/rootinfo_builder_generator_v1.cc
    revision: fac0203cc317df29973850b49ff886997caacb20
    locator: LoadUrmaDevicesFromDcmi L78–114；GetUrmaDeviceList L121–124；BuildNpuRootInfo L230–238
    observed_at: '2026-10-10T01:26:35+00:00'
    evidence: source
    access: published
  - id: hixl-eid-skip-fix
    path: https://github.com/hicann/hixl/commit/fac0203cc317df29973850b49ff886997caacb20
    revision: fac0203cc317df29973850b49ff886997caacb20
    locator: 提交说明的9.1.x至9.2.0行为回归及LoadUrmaDevicesFromDcmi的GetEidList失败处理diff
    observed_at: '2026-10-10T01:26:35+00:00'
    evidence: source
    access: published
---

# HIXL偶发No urma devices

## 结论与再次遇到时的处理

`No urma devices for npu_id:...` 表示HIXL构建通信资源时没有获得可用URMA设备列表，不能单凭这条报错认定物理设备消失、硬件损坏或模型显存不足。历史现场曾在不改源码、配置和驱动的情况下，仅重新拉起失败的任务服务就恢复初始化；这是偶发故障的临时恢复经验，不保证每次有效，也不代表底层根因已解决。

再次遇到同类报错时，先查询本条并说明临时恢复经验和根因边界。恢复业务或继续定位由当前任务目标与授权决定；范围未定时确认，已有明确选择时沿用，不重复询问。

- 若用户选择先恢复业务，在当前任务已有授权范围内有限重拉失败服务，保留其他正常角色、容器和历史资料；不能把历史恢复经验扩展为整机重启、设备复位或驱动变更授权。
- 若用户选择继续定位，优先保留故障时的完整启动日志、原生PLOG和相同时间窗内核日志，并核对DCMI设备数及全部EID索引；需要插桩或重启复现时另行遵循当前任务的变更边界。
- 重拉恢复后按当前任务要求验证初始化和请求路径；仍将根因标为未闭环。有限恢复后复发时保留新的失败，不以连续盲目重启替代定位。

## 触发特征与故障链

典型路径是自动LocalCommRes生成中的`BuildNpuRootInfo`报`No urma devices`，随后`GenerateLocalCommRes`、`AutoGenA5EndpointList`失败，继续上抛为AdxlEngine初始化失败（状态503900/E19999）、Ascend transport安装失败或TransferEngine初始化失败。优先查找这条链的最早错误，不能把后续worker退出、其他rank等待或清理异常当作首因。

对公开固定版本的hixl-rootinfo，设备总数由`GetUrmaDeviceCnt`取得，再逐设备调用`GetEidList`；失败或数量非法的设备会被跳过，全零或空EID也不会成为可用设备。设备数为零、各设备查询被跳过、EID为空等情况都可能汇合到最终空列表。因此仅凭末尾错误无法区分这些分支。该源码解释属于source层级，不能替代现场二进制构建对应关系及运行记录。

## 已有证据和复核要点

2026-10-16历史运行摘要记录了不同节点、不同卡在启动时出现同类失败，以及一次任务服务重拉后恢复的情况。稍后的DCMI/EID查询正常，只能说明检查时可查询，不能反推故障瞬间正常；这些原始材料未发布，不作为仓库可独立复验的端到端证据。

1. 核对实际库、驱动/固件、CANN版本和初始化资源模式。公开提交hixl-eid-skip-fix修正过CANN 9.2.0中单个设备EID查询失败即导致整体失败的回归；不能只凭9.2.0版本号就认定当前安装缺少该处理。库内字符串存在也不等于已证明实际执行分支或整包构建对应关系。
2. 记录物理NPU到逻辑ID映射，再调用`dcmiv2_get_urma_device_cnt`，按实际返回数量查询每一个`dcmiv2_get_eid_list_by_urma_dev_index`。不要固定只查索引0、1：历史复核中某卡返回4个设备，仅前两个索引成功不等于全量资源正常。
3. 尽量取得故障时设备数、逐索引返回码、EID数量及非零EID数量。接口报错、接口成功但空结果、过滤后为空是不同分支；事后的成功快照无法补回这些值。
4. 按同一故障进程和时间窗关联PLOG、内核和驱动事件。内核出现URMA/UDMA控制队列超时或IPoURMA发送超时属于排查线索；若PID属于内核工作线程、未映射到故障设备/查询，就不能直接认定它导致本次失败。

本条不提供占卡测试、自动重启或驱动修改脚本；处理动作依当前用户的选择和当前任务已有授权执行。

## 不能推出的结论与复查条件

目前没有足够证据确认具体驱动缺陷、跨进程竞争、初始化时序、固件问题或其他底层机制；也没有证据将本症状直接归因为MLA workspace返回值或PP手工分层。重启恢复、事后EID查询正常和上游存在相似修复，都不能单独证明根因或永久修复。

更换CANN/HIXL/驱动/固件、改用静态LocalCommRes、更改容器设备可见性，或获得故障瞬间查询值、匹配的驱动记录及受控复现后，应复查并更新本条。补齐可复核证据前保持candidate，不升级为通用根因结论；实质纠正或替代时按知识库历史规则保留旧条目及原因。
