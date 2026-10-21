---
id: eplb-full-map-pinned-host-allocation
title: 异步EPLB全层映射锁页可触发大块Host分配失败
status: candidate
updated_at: '2026-10-21T09:06:04+08:00'
verified_at: '2026-10-21T09:06:04+08:00'
observed_at: '2026-10-20T18:04:45+08:00'
tags: [EPLB, pin_memory, Host, allocator, KimiK3, Ascend950]
applies_to: vLLM-Ascend固定提交0a174d6c38c805b6c61be5ed4dae42431a557e54的异步映射准备路径；torch_npu 2.10.0.post7对应3363ea59d49f3e08cfd8d4a1f532b756ccda0682；历史Kimi K3 92个MoE层、896专家、D侧PP1
evidence_scope: 公开固定实现为source证据；历史worker/plog、安装来源及映射预算已核对，但故障时tensor形状与Host/NUMA资源快照缺失。原始运行及完整环境未公开，本次没有NPU分配实验或修复验收
sources:
  - id: eplb-pin-map
    path: https://github.com/vllm-project/vllm-ascend/blob/0a174d6c38c805b6c61be5ed4dae42431a557e54/vllm_ascend/patch/platform/patch_eplb.py
    revision: 0a174d6c38c805b6c61be5ed4dae42431a557e54
    locator: _run准备映射与迁移循环L608-613；_pin_host_map和_prepare_commit_maps L698-720
    observed_at: '2026-10-20'
    evidence: source
    access: published
  - id: host-allocator
    path: https://github.com/Ascend/pytorch/blob/3363ea59d49f3e08cfd8d4a1f532b756ccda0682/torch_npu/csrc/core/npu/CachingHostAllocator.cpp
    revision: 3363ea59d49f3e08cfd8d4a1f532b756ccda0682
    locator: 默认分配失败的aclrtMallocHostWithCfg检查L240-252；segmentSize定义L41和Host分配器选择L1277-1284
    observed_at: '2026-10-20'
    evidence: source
    access: published
  - id: host-allocator-config
    path: https://github.com/Ascend/pytorch/blob/3363ea59d49f3e08cfd8d4a1f532b756ccda0682/torch_npu/csrc/core/npu/NPUAllocatorConfig.cpp
    revision: 3363ea59d49f3e08cfd8d4a1f532b756ccda0682
    locator: parsePinMemoryExpandableSegments L70-95及pin_memory_expandable_segments解析入口
    observed_at: '2026-10-20'
    evidence: source
    access: published
---

# 异步EPLB全层映射锁页与Host分配失败

## 结论与触发条件

EPLB异步worker在`_prepare_commit_maps → _pin_host_map → pin_memory`失败时，先判断申请属于Host锁页内存还是设备HBM。历史首错为`aclrtMallocHostWithCfg`返回207001，原生HostMemAlloc记录驱动申请1073741824字节；后续cleanup终止属于次级结果。降低KV池或`gpu-memory-utilization`不能据此视为对症修复。

固定实现会在逐层迁移前准备映射并对CPU表锁页，包含将逻辑映射补到目标槽数的路径。[eplb-pin-map] 因而“按层迁移”不等于“只锁页本次改变层的映射”，必须核对映射准备的位置、实际形状和Host allocator。

## 历史预算与直接证据分别记录

2026-10-20 18:04:45，两名D侧worker分别在上述调用链失败，plog均指向Host申请，故障前仍有KV传输成功。保存的安装文件与固定公开EPLB实现相符，镜像原始层与实际路径一致；不能仅凭故障发生在HCOMM替换之后归因为安装改坏源码。

该轮模型93层、首层dense、其余92层MoE，896逻辑专家，D侧PP1保留全部MoE层。保存的vLLM实现按1024固定槽准备int64逻辑映射；不能用该轮冗余专家数32替换成33槽。预算为：

```text
92 × 896 × 1024 × 8 = 675282944 bytes = 644 MiB
PowerOf2Ceil(675282944) = 1073741824 bytes = 1 GiB
```

644MiB是源码、模型配置和层统计推导，故障时没有tensor.shape快照；1GiB是原生分配日志的实测。保存的torch Host缓存分配头文件采用2次幂向上取整，该默认慢路径进入`aclrtMallocHostWithCfg`。[host-allocator] 不能将推导形状和日志请求大小混称为同一项直接测量。

## 如何继续定位

- 对齐首个worker异常、CANN HostMemAlloc、大小/返回码和映射准备代码；避免把后续EPLB清理、peer初始化失败当首错。
- 在相同故障窗口获取Host/NUMA、进程锁页、memlock、cgroup和分配器状态；重启后充足的MemAvailable、无限memlock或较低VMA只能说明后来的状态，不能排除故障瞬间竞争、碎片或驱动限制。
- 预算按实际MoE层数、专家数、槽宽和dtype分别计算，核对PP stage以及整表/分层锁页。不能以全模型层数直接替代MoE层数，也不能把Host失败当作显存池容量不足。

历史后续快照中Host可用内存充足、未见对应OOM killer，但缺少故障瞬间资源证据。因此已确认触发点是大块全层映射锁页，尚未确认驱动为何拒绝该次申请。未实施业务修复，也未验证根因消除。

## 规避候选与验收边界

固定torch_npu实现有独立的`pin_memory_expandable_segments`开关，解析还检查CANN/驱动支持；Host分配器据此选择另一条实现，段大小为20MiB。[host-allocator-config, host-allocator] 仅设置设备的`expandable_segments`不等于已启用Host锁页扩展段。

下次经用户授权启动前，可以评估合并到已有配置：

```bash
export PYTORCH_NPU_ALLOC_CONF=expandable_segments:True,pin_memory_expandable_segments:True
```

这只是与固定版本关联的候选；历史任务未应用、未做重启对照，不能称已修复或所有950环境支持。配置解析日志、真实加载及实际EPLB迁移需分别验收。

按改变层准备并复用锁页缓冲也是设计候选：同布局单层为7MiB，历史默认取整8MiB；需保持异步copy/event和提交生命周期，再验证正确性与真实迁移。该预算不是已实现优化，关闭EPLB的隔离对照也不能当成保留EPLB功能的修复。

## 复查条件

EPLB映射布局/槽数、准备时机、MoE层划分、Host分配器、CANN/驱动或扩展段支持改变时复查。公开源码支持调用机制，未公开的历史日志不构成新环境验收。设备KV/workspace问题见[长序列内存预算](ascend-long-context-memory-budget.md)，迁移与初始化的证据区别见[EPLB运行阶段](eplb-runtime-evidence.md)。
