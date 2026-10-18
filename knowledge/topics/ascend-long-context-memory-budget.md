---
id: ascend-long-context-memory-budget
title: 长序列的长度上限、混合KV容量与prefill workspace预算
status: candidate
updated_at: '2026-10-18'
verified_at: '2026-10-18'
observed_at: '2026-10-18'
tags: [长序列, KVCache, KimiK3, DCP, PP, workspace, 显存]
applies_to: 指定vLLM/vLLM-Ascend固定源码的MLA workspace与混合KV分组规则；容量数值和失败点仅属于正文限定的历史Kimi K3配置
evidence_scope: 源码事实已只读复核；历史容量及请求摘要的原始运行材料未公开，本次没有重新请求模型或测试内存边界
sources:
  - id: workspace-allocation
    path: https://github.com/vllm-project/vllm-ascend/blob/6ef97a0d9709029047d4ab5a44a1cafcd7536aad/vllm_ascend/attention/utils.py
    revision: 6ef97a0d9709029047d4ab5a44a1cafcd7536aad
    locator: ascend_chunked_prefill_workspace_size L253-296
    observed_at: '2026-10-18'
    evidence: source
    access: published
  - id: workspace-documentation
    path: https://github.com/vllm-project/vllm-ascend/blob/6ef97a0d9709029047d4ab5a44a1cafcd7536aad/docs/source/user_guide/configuration/additional_config.md
    revision: 6ef97a0d9709029047d4ab5a44a1cafcd7536aad
    locator: chunked_prefill_workspace_size表项L67及说明L87-96
    observed_at: '2026-10-18'
    evidence: source
    access: published
  - id: hybrid-kv-capacity
    path: https://github.com/vllm-project/vllm/blob/ced6857afa0ea7b2e3f0846a62e1394e90f15607/vllm/v1/core/kv_cache_utils.py
    revision: ced6857afa0ea7b2e3f0846a62e1394e90f15607
    locator: check_enough_kv_cache_memory L975起；get_max_concurrency_for_kv_cache_config L1067-1100
    observed_at: '2026-10-18'
    evidence: source
    access: published
---

# 长序列的长度上限、混合KV容量与prefill workspace预算

## 三类判断分别验收

| 判断 | 核对内容 | 不能据此代替的验收 |
|---|---|---|
| 长度配置 | 模型可支持的长度、服务解析后的max-model-len、实际输入和预留输出 | 当前KV分配、所有运行时临时内存 |
| KV容量 | 每个角色/PP stage/DP副本的真实block池、cache groups、DCP分片及额外状态 | prefill workspace、通信/图捕获等其他设备内存 |
| 完整请求 | 在同一配置下真实完成指定输入/输出/并发，并核对usage、结束状态、错误 | 未运行的长度边界、更高并发或精度正确性 |

本例服务总长度预算包含输入与输出；输入1000000、输出100的总长度为1000100，不等于实测过1048576边界。声明`max-model-len=1048576`本身不是一条完整请求通过的证据。

## workspace配置值不一定等于最终分配

在PR19011固定源码中，`additional-config.chunked_prefill_workspace_size`为正整数token-row容量配置，默认131072。它不是字节数，也不等于调度参数`max-num-batched-tokens`。[workspace-documentation]

该公共helper先计算：

```text
requested = max(8 × max_model_len,
                4 × max_num_seqs × block_size)
minimum   = max_num_seqs × block_size
workspace = max(min(requested, configured_capacity), minimum)
```

因此需求小时实际值可以小于配置cap，最小需求超过cap时也会高于它；PCP/DCP路径还可能进一步扩容。应检查目标metadata builder和最终原生日志，不能把配置值当成所有路径的硬上限。[workspace-allocation, workspace-documentation]

P侧配置片段：

```bash
export VLLM_PP_LAYER_PARTITION="24,24,24,21"
# 将下面字段合入已有的additional-config对象：
# "chunked_prefill_workspace_size": 409600
```

PP划分的数量和层数约束见[P/D配置参考](kimik3-pd-configuration-reference.md)。增大workspace通常减少上下文分块并增加设备内存占用，不等于必然加速或支持更长请求。应同时保留分块、KV容量和临时内存的证据。

## 混合KV容量按cache groups求和

固定vLLM源码按每个设备cache group计算单请求页数，再合计使用同一池的block需求；host-resident groups另有host池约束。直接用`num_blocks × token_block_size`可能忽略混合状态和分组需求。[hybrid-kv-capacity]

历史Kimi K3例子限定：attention block768、Mamba align、RecoverSSM关闭、DSpark3、目标/草稿attention及三个recurrent groups；完整版本缺口见[P/D参考的版本章节](kimik3-pd-configuration-reference.md#版本补丁与可复验边界)。本例的运行时分组计算可写为：

```text
单请求需要的池blocks = ceil(L / (768 × DCP)) + 3 × (2 + 3)
```

其中15个额外blocks属于本例三个recurrent groups及speculative配置，不是通用Mamba固定开销，也不能只按DCP除整个公式。

| 历史角色 | DCP | 池blocks | L=1048576的attention需求 | 额外状态需求 | 单条合计 |
|---|---:|---:|---:|---:|---:|
| P的各PP stage/rank | 1 | 2384 | 1366 | 15 | 1381 |
| 每个D的DP副本/rank | 8 | 716 | 171 | 15 | 186 |

该次计算另预留1个null block，支持当时的单条总长度预算。它不代表所有KV池能跨DP相加使用，也不是把多副本容量汇成一条超长序列；与该轮完整请求一起才形成有效容量观察。容量数值是未公开原始运行材料的历史摘要，保持candidate。

## 保留成功与失败两个边界

| 历史场景 | 观察 | 可以保留的判断 |
|---|---|---|
| EPLB关闭、主模型maxlen1048576、P原生workspace131072；输入1000000/输出100、并发1、1条 | 请求完成，usage为1000000/100，总1000100 | 此配置完成过该长度负载；没有运行1048576满边界 |
| 保持D运行，P采用workspace409600、分层24,24,24,21、主模型maxlen1048576；同规模长请求 | P的KV池仍报告2384blocks；请求HTTP500，PP3在采样路径的HCCL初始化申请约1.56GiB设备内存失败 | KV容量统计足够，仍可能在其他运行时分配处失败；不能声称三项复测均通过 |
| P改为maxlen204800、workspace409600；D maxlen1048576、EPLB开启、DCP8；短输入GPQA/最大输出80000 | 两轮198题均完成 | 支持该GPQA工作负载的历史观察，不能据此外推P侧1M请求通过 |

workspace增加与后续失败有时间关联；没有受控显存分配轨迹或充分A/B，不能断言它是该次OOM的唯一原因，也不提供“固定留出1.56GiB即可解决”的规则。失败位置和已知条件足以保留，不据此自动展开其他组件调查。

## 复用与失效条件

复用时记录明确整数token长度，重新核对实际cache groups、block大小、DCP、speculative宽度、PP划分、workspace、图模式、EPLB冗余专家、内存利用率和并发。P和D分别核对；PP以各stage约束为准，DP副本各自保有预算。

参数变化后先验实际分配，再按目标长度/输出/并发完成请求契约；模型权重或量化、缓存布局、Mamba模式、FlashMLA builder、通信器或图捕获策略改变时复查。上述公共源码支持分组和workspace规则，不能替代未公开的历史运行材料或新环境验收。
