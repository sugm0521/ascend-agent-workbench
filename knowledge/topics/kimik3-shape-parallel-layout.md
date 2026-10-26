---
id: kimik3-shape-parallel-layout
title: Kimi K3的SP、DCP、latent MoE与AttnRes逻辑shape
status: candidate
updated_at: '2026-10-26T14:40:16.513692+08:00'
verified_at: '2026-10-26T14:40:16.513692+08:00'
observed_at: '2026-10-23'
tags: [Kimi-K3, shape, SP, TP, PP, DCP, KDA, MLA, AttnRes, EPLB]
applies_to: Ascend b0e4e29a2626706cfe306c5217db7648d46d3103配CI-pinned vLLM c0b6f74bee518aeaf5d72b200a0216e72fbb5e7c；历史H7168、93层、96头配置；P TP8/PP4、D TP8/DP4/DCP8且SP生效
evidence_scope: 固定源码与历史权重config的逻辑推导，不是NPU张量采样；数值配置原件未公开，读者需核对自己的config；实际部署曾使用另一双SHA，不以教学源码代表运行代码
sources:
  - id: ascend-model
    path: https://github.com/vllm-project/vllm-ascend/blob/b0e4e29a2626706cfe306c5217db7648d46d3103/vllm_ascend/models/kimi_k3.py
    revision: b0e4e29a2626706cfe306c5217db7648d46d3103
    locator: AscendKimiMLP.forward、AscendKimiMoE、load_eplb_expert_weights、decoder及PP forward
    observed_at: '2026-10-23'
    evidence: source
    access: published
  - id: ascend-kda
    path: https://github.com/vllm-project/vllm-ascend/blob/b0e4e29a2626706cfe306c5217db7648d46d3103/vllm_ascend/ops/kimi_kda.py
    revision: b0e4e29a2626706cfe306c5217db7648d46d3103
    locator: AscendKimiK3DeltaAttention构造、TP heads与forward
    observed_at: '2026-10-23'
    evidence: source
    access: published
  - id: ascend-mla-cp
    path: https://github.com/vllm-project/vllm-ascend/blob/b0e4e29a2626706cfe306c5217db7648d46d3103/vllm_ascend/attention/context_parallel/mla_cp.py
    revision: b0e4e29a2626706cfe306c5217db7648d46d3103
    locator: DCP query gather、decode与输出/LSE合并路径
    observed_at: '2026-10-23'
    evidence: source
    access: published
  - id: vllm-sp
    path: https://github.com/vllm-project/vllm/blob/c0b6f74bee518aeaf5d72b200a0216e72fbb5e7c/vllm/models/common/ops/sequence_parallel.py
    revision: c0b6f74bee518aeaf5d72b200a0216e72fbb5e7c
    locator: sp_shard、sp_all_gather、sp_reduce_scatter、sp_padding_mask
    observed_at: '2026-10-23'
    evidence: source
    access: published
  - id: vllm-kimi
    path: https://github.com/vllm-project/vllm/blob/c0b6f74bee518aeaf5d72b200a0216e72fbb5e7c/vllm/models/kimi_k3/amd/linear.py
    revision: c0b6f74bee518aeaf5d72b200a0216e72fbb5e7c
    locator: KimiLinearModel、KimiDecoderLayer、KimiMLAAttention及AttnRes契约
    observed_at: '2026-10-23'
    evidence: source
    access: published
---

# 先固定配置，再推导逻辑shape

使用本表前核对双仓提交、模型config、量化布局、runner及实际并行开关。下文矩阵写为激活`X[T,K] × W[K,N]`的逻辑维度；实际权重可能转置、量化打包或NZ/padding，不能把逻辑表当真实kernel内存布局。[固定Ascend模型源码](https://github.com/vllm-project/vllm-ascend/blob/b0e4e29a2626706cfe306c5217db7648d46d3103/vllm_ascend/models/kimi_k3.py)提供组合方式，数值来自该次历史config，不代表任意Kimi K3。

## 1. 并行分别切什么

令`T`为一个DP实例本次forward的真实token行数，`Tpad=8*ceil(T/8)`为TP8下SP最低补齐量，`n=Tpad/8`。图bucket可能要求更大补齐；推测验证和chunked prefill时`T`不等于请求数。

| 机制 | 本例中的分工 | 不应进行的换算 |
|---|---|---|
| DP4 | 四个attention/请求状态实例，路由不保证均分 | 不把hidden7168除4 |
| TP8 | 按具体投影/权重布局切分 | 复制投影不能全部除8 |
| SP | 层间hidden按token行保留`[n,7168]` | 不把hidden宽变成896 |
| PP4 | 将93层分配到四个stage | 不将token或hidden逐级除4 |
| DCP8 | 复用D侧TP组，分片MLA历史KV | 不再乘一套8卡，也不再次切KDA头数 |

SP入口AllGather恢复token行；RowParallel投影后的ReduceScatter同时求和和按token切分，不能只当切片。参考[SP固定实现](https://github.com/vllm-project/vllm/blob/c0b6f74bee518aeaf5d72b200a0216e72fbb5e7c/vllm/models/common/ops/sequence_parallel.py)。

## 2. 层次与主链

历史config为H=7168、93层、96头、head_dim128、词表163840。69层KDA、24层MLA；首层Dense，其余92层latent MoE，attention排列按该config前92层每四层KDA/KDA/KDA/MLA、末层MLA。其他配置必须重新按layer类型计算。

```text
IDs[T] → embedding[T,7168] → SP[n,7168]
→ 每层AttnRes/Norm → attention前AllGather → KDA或MLA
→ O投影/ReduceScatter[n,7168] → AttnRes/Norm → Dense或MoE
→ prefix更新 → PP边界恢复并传递token行
→ 最终AttnRes → AllGather[T,7168] → runner选行[R,7168]
→ compute_logits的RMSNorm → 分词表logits[R,20480] → 采样
```

`R`是runner选择的logits位置数，不一定为T；分布式采样也不保证每次物化完整词表。PP4不唯一决定分层；历史24/24/24/21只有在实际分层配置匹配时可用，未核对就保留unknown。多模态图像编码另需实际分辨率/patch输入，不能从主干hidden推造视觉shape。

## 3. KDA与MLA

[KDA固定实现](https://github.com/vllm-project/vllm-ascend/blob/b0e4e29a2626706cfe306c5217db7648d46d3103/vllm_ascend/ops/kimi_kda.py)按TP8持有12个本地头。Q/K/V各`[T,1536]`，核心视图`[1,T,12,128]`；beta为`[T,12]`量级，输出gate与O对应1536宽。合并/量化路径可能改变可见kernel数量。

每slot/层/rank的递归state逻辑为`[12,128,128]`，卷积state为`[4608,3+spec_num]`或其转置布局。DCP不把该KDA状态再次除8；它是固定递归状态，不是随历史长度线性增长的普通token KV。

本例MLA Q低秩1536、KV低秩512，QK额外分支64，因此cache逻辑宽仍512+64=576；配置不做RoPE不能据此删除64维。P侧展开KV后计算attention；有prefix/chunk时query行数与总KV行数不同。

D侧吸收式decode将Q映射到512 latent维，DCP gather后可用全部96个query头读取本rank历史KV片；输出/LSE再交换合并，恢复本TP rank需要的12头，最后V上投影及O/ReduceScatter。合并关系为`LSE=logsumexp_r(LSE_r)`、`O=sum_r exp(LSE_r-LSE)*O_r`，不能直接平均各rank输出。具体分支见[MLA DCP实现](https://github.com/vllm-project/vllm-ascend/blob/b0e4e29a2626706cfe306c5217db7648d46d3103/vllm_ascend/attention/context_parallel/mla_cp.py)；history/current与推测分支不能都套同一临时shape。

## 4. Dense、latent MoE与物理专家

Dense中间维33792，TP8下gate/up输出`[Tpad,8448]`，SituAndMul后`[Tpad,4224]`，down投影与SP规约回`[n,7168]`。

latent MoE配置为896路由专家、top16、latent3584、每专家中间3072、2共享专家。router读原hidden`[n,7168]`并产生`[n,896]`，不是先降到latent再路由；routed分支投影至3584、dispatch后各专家`M_e`行，gate/up→6144、激活→3072、down→3584，combine与latent norm后恢复7168。

`M_e`取决于路由、padding和负载均衡，不是`n/896`。EP下专家可完整驻留owner，不再机械把每专家3072按TP8切成384。共享专家是否复制或TP切分有独立分支。896是逻辑专家数；EPLB物理slot、冗余副本及初始权重映射须另查，不能据此算每卡物理slot。关联[EPLB运行证据](eplb-runtime-evidence.md)。

## 5. AttnRes及融合路径的限制

该固定decoder契约用`prefix_delta`延迟累加，返回prefix、block residual与MLP输出，历史block buffer逻辑为`[n,K,7168]`，最终K=8来自本例块长12/93层。块边界、valid数量和stage预分配不等于每层都新增一块。PP会传hidden及历史块状态，不只一条窄化hidden；参考[固定上游契约](https://github.com/vllm-project/vllm/blob/c0b6f74bee518aeaf5d72b200a0216e72fbb5e7c/vllm/models/kimi_k3/amd/linear.py)。

OProj通信融合可改变独立O投影+ReduceScatter的kernel边界，FlashMLA启用也受硬件、后端、量化、runner与并行门控。基础逻辑表不是全部分支的真实kernel清单；融合组合是否重复规约、实际临时shape和性能需要NPU采样。教学源码与CI pin、独立main和真实部署SHA分别记录；新源码推导不证明旧服务已加载它。

更换模型config、两仓提交、量化/runner或融合门控时重算。本文没有新的模型启动、真实shape、精度或性能验收。
