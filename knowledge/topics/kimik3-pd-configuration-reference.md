---
id: kimik3-pd-configuration-reference
title: Kimi K3 的 P/D 角色配置与版本化验证参考
status: candidate
updated_at: '2026-10-18'
verified_at: '2026-10-18'
observed_at: '2026-10-18'
tags: [KimiK3, PD分离, PP, TP, DP, EP, DCP, 配置]
applies_to: Ascend 950 DT、Kimi K3 W4A8-MXFP、DSpark3、vLLM MRV2；具体双仓提交与叠加范围见正文，不能作为其他版本的默认启动配置
evidence_scope: 公开固定源码已只读复核；历史运行摘要来自2026-10-18北京时间的保存结果，完整环境和运行材料未公开，未在本次知识整理中重新运行服务
sources:
  - id: parallel-config
    path: https://github.com/vllm-project/vllm/blob/ced6857afa0ea7b2e3f0846a62e1394e90f15607/vllm/config/parallel.py
    revision: ced6857afa0ea7b2e3f0846a62e1394e90f15607
    locator: ParallelConfig字段L122-168、L353-356；EP及DCP约束检查L533-568
    observed_at: '2026-10-18'
    evidence: source
    access: published
  - id: pp-partition
    path: https://github.com/vllm-project/vllm/blob/ced6857afa0ea7b2e3f0846a62e1394e90f15607/vllm/distributed/utils.py
    revision: ced6857afa0ea7b2e3f0846a62e1394e90f15607
    locator: get_pp_indices L127-154
    observed_at: '2026-10-18'
    evidence: source
    access: published
---

# Kimi K3 的 P/D 角色配置与版本化验证参考

## 可复用结论

P、D分别承担预填充和解码，应分别记录并行、调度、显存和图模式。DCP复用已有并行ranks，不额外增加一套设备；在本例PCP=1时，DCP必须整除TP。因此D侧TP8/DP4/DCP8使用32个ranks，不应再乘8。EP启用后，本例MoE专家组跨TP×DP，共32个ranks。[parallel-config]

显式PP分层需同时满足“分段数等于PP大小”和“各段之和等于模型层数”。`24,24,24,21`有4段、合计93层，仅适用于对应层数的模型；合法分层不证明各stage显存或耗时最优。[pp-partition]

## 已观察的角色组合

以下为一轮历史验证的配置参考，不是完整部署命令。它省略模型路径、网络地址、rank入口和依赖准备；复用者应通过自己环境的实际配置补齐。

| 项目 | P角色 | D角色 |
|---|---|---|
| 设备拓扑 | 4节点，每节点8卡；TP8、PP4、DP1 | 4节点，每节点8卡；TP8、DP4、PP1、EP32 |
| PCP / DCP | 1 / 1 | 1 / 8 |
| 主模型 `max-model-len` | 204800 | 1048576 |
| `max-num-seqs` | 32 | 40，每个DP实例的服务配置 |
| `max-num-batched-tokens` | 16384 | 768 |
| `gpu-memory-utilization` | 0.8 | 0.91 |
| PP层划分 | `24,24,24,21` | 不使用PP分层 |
| MLA prefill workspace配置 | `409600` token rows | 不用P侧覆盖值推断D的实际分配 |
| attention block / CP KV interleave | 混合缓存对齐后attention block768 | block768、interleave768 |
| 执行模式 | `--enforce-eager` | `FULL_DECODE_ONLY`；Ascend static/super kernel配置开启 |
| MLAPO | additional-config中为false | additional-config中为true |
| EPLB | 未启用 | enable；window600 / step50 / redundant32 / async / stair |
| KV角色 | producer | consumer |
| 公共项 | expert parallel、prefix cache、MRV2、Kimi K3 tokenizer/reasoning parser | 与P相同，但各项应在自身进程中复核 |

主/草稿配置分开记录：本例DSpark为3个speculative tokens、draft TP8、greedy draft sampling、草稿配置`max_model_len=4096`。该字段属于草稿配置，不能拿它覆盖主模型长度，也不能代替主模型长请求验收。

`max-num-seqs`是服务调度配置，客户端并发60是请求负载配置；它们不要求数值相等。P/D角色、DP分配和实际running/waiting需一起观察。

### 可复制的参数片段

```bash
# P：加入已有、已确认的P启动入口，不是完整serve命令。
export VLLM_PP_LAYER_PARTITION="24,24,24,21"
p_role_args=(
  --tensor-parallel-size 8
  --pipeline-parallel-size 4
  --max-model-len 204800
  --max-num-seqs 32
  --max-num-batched-tokens 16384
  --gpu-memory-utilization 0.8
  --enforce-eager
)
# 将该字段并入原有additional-config对象，保留其他已有字段：
# "chunked_prefill_workspace_size": 409600

# D：同样只定义角色片段；还需组合下文EPLB参考中的eplb_args。
d_role_args=(
  --tensor-parallel-size 8
  --data-parallel-size 4
  --enable-expert-parallel
  --decode-context-parallel-size 8
  --block-size 768
  --cp-kv-cache-interleave-size 768
  --max-model-len 1048576
  --max-num-seqs 40
  --max-num-batched-tokens 768
  --gpu-memory-utilization 0.91
)
```

D侧EPLB参数及生效判读复用[已有启用参考](eplb-enable-reference.md)和[运行阶段判读](eplb-runtime-evidence.md)。组合其中的eplb_args时需同时满足本表的模型/量化支持条件，不能只增加开关。本例没有把D的EPLB配置复制到P，也没有用草稿模型关闭EPLB的日志判断主模型关闭。示例数值不是性能最优解。

P侧曾先打印backend block128，随后因attention/Mamba页大小对齐设置attention block768；上表取最终对齐结果。容量计算不能停在初始化的第一条block日志。

## 版本、补丁与可复验边界

历史基线为vLLM `ced6857afa0ea7b2e3f0846a62e1394e90f15607`、vLLM-Ascend `52cf60438115e7b3b6a1c81babb360567126ba92`，CANN9.2、torch2.10.0+cpu配torch_npu2.10.0.post4。Ascend为editable安装，包版本字符串不包含全部叠加修改；FlashMLA外部算子/Python绑定和量化模型也属于复现条件。

下表保留这份历史组合的固定公开版本，便于对照；不建议对其他分支无条件照搬整组PR。

| PR | 本例采用的head |
|---|---|
| 18756 | [70544faec4c28743ddc2222433fb041facbca285](https://github.com/vllm-project/vllm-ascend/commit/70544faec4c28743ddc2222433fb041facbca285) |
| 18758 | [d1aa5a5152ba9f40a60c480bfc5123aacbd41ada](https://github.com/vllm-project/vllm-ascend/commit/d1aa5a5152ba9f40a60c480bfc5123aacbd41ada) |
| 18897 | [4a59301096e69dd88952b453f6ec2b6d16c4fcf3](https://github.com/vllm-project/vllm-ascend/commit/4a59301096e69dd88952b453f6ec2b6d16c4fcf3) |
| 18954 | [d360338b885f8dc46b458369e01bb6dc64c6bb7a](https://github.com/vllm-project/vllm-ascend/commit/d360338b885f8dc46b458369e01bb6dc64c6bb7a) |
| 19011 | [6ef97a0d9709029047d4ab5a44a1cafcd7536aad](https://github.com/vllm-project/vllm-ascend/commit/6ef97a0d9709029047d4ab5a44a1cafcd7536aad) |
| 19013 | [82f42d551e860cfa5a626e16794fa03b37dd3b59](https://github.com/vllm-project/vllm-ascend/commit/82f42d551e860cfa5a626e16794fa03b37dd3b59) |
| 18035 | [d9067430102864cd60607f2e4f1d69e692d0a5e7](https://github.com/vllm-project/vllm-ascend/commit/d9067430102864cd60607f2e4f1d69e692d0a5e7) |
| 19098 | [cbb6c1b1edec477647942eb69a1e02a0aa0484a5](https://github.com/vllm-project/vllm-ascend/commit/cbb6c1b1edec477647942eb69a1e02a0aa0484a5) |

另有本地KDA预编译launcher兼容修改，未提供完整公开产物。其调用边界见[KDA条目](kda-compiled-launcher-arguments.md)。因此表中基线和PR列表仍不足以独立重建全部环境，整篇保留candidate；公开配置源码事实与历史端到端摘要分别看待。

历史记录中，本组合完成GPQA Diamond198题（最大输出80000、并发60、temperature/top_p各1、reasoning_effort=max），原生183/198；真实EPLB提交33次，前后短curl文本相同。仍保留两处孤立异常字符及一题答案格式抽取失败，不能称全部精度问题已修复。

同组合再叠PR19038固定head `476f0ca416821b161e6cc2f04b4d3bede877ca0f` 后，也完成同配置198题、原生184/198、30次EPLB提交。两轮随机采样各一次，分数净增1题不证明PR带来精度或性能收益；目标同步旁路的限制见[门控条目](spec-decode-cpu-length-sync-gates.md)。这些为历史结果摘要，原始运行材料未公开，不能由本仓库独立复验。

## 复用检查与复查条件

1. 对照实际模型层数、双仓提交、补丁、算子与依赖；分开保存P/D和主/草稿配置。
2. 从实际PID/starttime绑定的argv/environ核对配置，再读同轮初始化日志；仅修改另一个shell不证明进程已采用新值。
3. D侧结合主模型EPLB启用日志、DCP初始化/rank日志和业务负载后的真实迁移提交验证；启动profile或内存注册只证明相应阶段。
4. 按目标工作负载验收。204800仅是本例对“200k”的明确整数口径；1048576是另一角色的长度配置，均不单独证明内存充足，参阅[长序列预算](ascend-long-context-memory-budget.md)。

模型层数/量化、runner、并行分组、CLI消费逻辑、草稿模型、FlashMLA选择、EPLB实现或设备内存发生变化时，重新核对对应条件，不将历史配置自动升级为新环境的默认值。
