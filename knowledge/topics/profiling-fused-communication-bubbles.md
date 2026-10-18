---
id: profiling-fused-communication-bubbles
title: 融合通信算子的空泡与分块性能判读
status: candidate
updated_at: '2026-10-18'
verified_at: '2026-10-18'
observed_at: '2026-10-16'
tags: [profiling, 空泡, PP, TP, MLA, FIA, MatmulReduceScatterV2, 融合通信]
applies_to: 通用事件区间与同工作量比较方法；历史数值仅限2026-10-16 Kimi K3 P侧PP4/TP8四个TP0采样，完整部署边界见关联内存预算主题
evidence_scope: 区间定义与合成示例自包含；公共固定源码只支持MLA分块机制；历史匹配段及分配统计已复核，原始trace和完整叠加补丁未公开，本次未重放或新增NPU实验
sources:
  - id: mla-chunks
    path: https://github.com/vllm-project/vllm-ascend/blob/7759ceecee1c3ea21a4d47d55f93545fca895088/vllm_ascend/attention/mla_v1.py
    revision: 7759ceecee1c3ea21a4d47d55f93545fca895088
    locator: build_chunked_metadata L561-579；_compute_prefill_context的kv_b_proj及FIA输入准备L1289-1311
    observed_at: '2026-10-18'
    evidence: source
    access: published
---

# 融合通信算子的空泡与分块性能判读

## 两种空窗都不是有效计算利用率

给定同一rank的分析窗口W，先将事件裁剪至W，再合并同类事件的重叠区间。设C为计算核事件并集，A为全部采集事件并集，则定义：

```text
计算核事件空窗率 = (长度(W) - 长度(C)) / 长度(W)
全事件空白率     = (长度(W) - 长度(A)) / 长度(W)
```

按目标导出格式核对AIC/AIV/MIX等计算核类别，明确HCCL范围、AICPU和融合事件如何归类，保留rank、stream、原事件与窗口边界的定位。不要直接跨流相加duration；若另算“仅通信覆盖”，应使用通信区间扣除与C重叠的部分，而非相减两个duration总和。

长HCCL范围可以覆盖等待时间；计算通信融合核也可以在等待其他rank时保持事件存在。因此全事件空白率低、计算核事件覆盖率高，均不能直接推出有效计算高。`MatmulReduceScatterV2`一类融合事件的跨度不能全部叫做纯matmul计算；配对AICPU/通信事件若重叠也不能再次计入墙钟损失。无法拆分融合核内部计算/等待时保留未知，不强算指令级利用率或网络带宽。

自包含的合成示例：10ms窗口里有计算事件[0,3]、[2,5]及融合事件[5,10]。duration相加为11ms，并集为10ms，计算核事件空窗为0；即使融合事件内部有4ms等待，这些事件范围本身也无法证明有效计算时间。该例只是区间定义演示，不是NPU测量。

## 分块变化后匹配总工作量

MLA固定源码按workspace预算生成上下文chunk，并对每块准备K/V后调用FIA。[mla-chunks] chunk大小改变时，单次FIA耗时及调用次数都会改变，不能只比较调用均值。

比较时至少固定或核对Q长度、各请求的有效K/V长度及分布、batch、heads/head维度、dtype、mask/causal、布局和模型路径。多请求场景只有总K相等仍不足以证明计算量完全相同；优先匹配每请求长度及对应stage。然后分别比较：

1. 一个逻辑attention的全部chunk累计kernel耗时，以及更新/拼接等配套工作。
2. 对应工作段的墙钟和区间覆盖；首/尾边界应为同样的模型阶段，标明是否完整step。
3. 主机提交、内存申请/回收、同步及后续融合通信的时序。先找最早出现的阻塞，不把后续collective长跨度直接归因于网络。

只有Q和总K可匹配时，把结果称为“同Q/总KV的匹配段”，保留各请求分布未完全匹配的限制；不要升级为严格逐请求A/B。端到端耗时、kernel累计和融合等待保持各自分母，不相互替代。

## 历史反例：FIA加速而PP3主段变慢

原观察为2026-10-16，2026-10-18仅核对已有摘要。部署版本、P/D角色、workspace与本地补丁缺口见[长序列内存预算](ascend-long-context-memory-budget.md#分块减少仍可能因可恢复分配失败而变慢)；公共基线不代表全部实际实现，历史例子保持candidate。

在Q15959、总prefix KV368640的四TP0首次匹配段中，原版prefix分为129024、129024、109056、1536四块，修改版合为一块368640。取每PP首个主模型current FIA至最后一个主模型prefix FIA，不含末尾draft FIA，不称为完整execute_model step。

| PP3历史指标 | 原分块 | 大分块 |
|---|---:|---:|
| 匹配主段墙钟 | 791.446ms | 2583.344ms |
| Prefix FIA累计 | 354.050ms | 278.810ms |
| 21次MatmulReduceScatterV2累计跨度 | 27.212ms | 1557.850ms |

同段普通MatMul、KDA和GroupedMatmul累计基本不变，另有物理内存失败及缓存回收重试证据。可保留的解释是：局部FIA加速被分配/同步及融合等待放大抵消；不能把融合跨度增加全部归为矩阵乘变慢，也不能据此定位每个TP rank的首因或精确分摊全部端到端差值。分配器机制和可恢复失败的辨识沿用关联内存主题，不重复复制。

## 窗口、证据与复查边界

严格前5秒可能主要是流水线填充，延长原生记录又可能包含不同stop阶段，先按[Profiler窗口条目](profiler-stop-window-boundaries.md)限定可比性。四个TP0只能说明这四份采样，不能称为完整32rank或D侧验收。

原始运行及完整补丁未公开，仓库不能独立复验这些历史数值；本次没有回退A/B、allocator快照或全rank归因。通用区间定义和同工作量方法可独立采用，历史根因保持上述条件，不把某个workspace值或固定stage当成通用规则。事件导出格式、融合实现、并行/分层、cache/chunk策略及profiler行为改变时复查。
