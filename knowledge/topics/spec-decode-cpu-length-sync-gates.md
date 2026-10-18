---
id: spec-decode-cpu-length-sync-gates
title: Kimi K3与DSpark的CPU长度同步优化需分别核对目标和草稿门控
status: candidate
updated_at: '2026-10-18'
verified_at: '2026-10-18'
observed_at: '2026-10-18'
tags: [KimiK3, DSpark, MRV2, FlashMLA, SpecDecode, DCP, 优化门控]
applies_to: vLLM-Ascend PR19038固定head476f0ca416821b161e6cc2f04b4d3bede877ca0f；其他实现需重新检查，运行摘要仅限历史PP4与DCP8组合
evidence_scope: 固定公开源码条件已核实；运行日志摘要未公开，未在本次整理中重跑精度或性能测试，未测量draft分支性能
sources:
  - id: target-gate
    path: https://github.com/vllm-project/vllm-ascend/blob/476f0ca416821b161e6cc2f04b4d3bede877ca0f/vllm_ascend/worker/v2/model_runner.py
    revision: 476f0ca416821b161e6cc2f04b4d3bede877ca0f
    locator: NPUModelRunner._can_skip_spec_cpu_length_sync L1237-1254
    observed_at: '2026-10-18'
    evidence: source
    access: published
  - id: draft-gate
    path: https://github.com/vllm-project/vllm-ascend/blob/476f0ca416821b161e6cc2f04b4d3bede877ca0f/vllm_ascend/worker/v2/spec_decode/dspark/speculator.py
    revision: 476f0ca416821b161e6cc2f04b4d3bede877ca0f
    locator: set_attn的草稿predicate L257-258；_prepare_draft_dcp_metadata_inputs L263-282
    observed_at: '2026-10-18'
    evidence: source
    access: published
  - id: all-layer-predicate
    path: https://github.com/vllm-project/vllm-ascend/blob/476f0ca416821b161e6cc2f04b4d3bede877ca0f/vllm_ascend/attention/mla_v1.py
    revision: 476f0ca416821b161e6cc2f04b4d3bede877ca0f
    locator: all_mla_use_flashmla L3421-3425
    observed_at: '2026-10-18'
    evidence: source
    access: published
---

# Kimi K3与DSpark的CPU长度同步优化需分别核对目标和草稿门控

## 固定源码支持的结论

PR已应用、模型可以推理和优化分支已生效是三个不同的验收项。这个固定PR分别处理DSpark草稿长度拷贝和目标模型拒绝采样后的CPU长度同步，不能用一个条件或一条日志替代两侧检查。

| 路径 | 旁路条件 | 不满足时 |
|---|---|---|
| DSpark草稿的该处阻塞D2H拷贝 | 进入`not self.use_dcp`分支；草稿attention为MLA，且已加载的MLA实现集合非空、每层`use_flashmla`都为true | 相应MLA/FIA路径保留原CPU长度同步；DCP路径另行执行 |
| 目标模型的CPU长度拷贝与后续等待/镜像覆盖旁路 | 支持的Kimi K3 architecture；草稿predicate满足；PP=1、PCP=1、DCP=1；adaptive verification关闭、sparse KV offload关闭、KVPP size=1；目标所有已加载MLA实现均选择FlashMLA | `_can_skip_spec_cpu_length_sync()`返回false，保留精确CPU同步路径 |

上述target门控里的architecture限定为`KimiK3ForCausalLM`、`KimiK3ForConditionalGeneration`。[target-gate] “全部层选择FlashMLA”依据最终已加载impl的`use_flashmla`判定，空MLA集合返回false；不能用安装了FlashMLA模块、一个全局开关或单层成功替代。[draft-gate, all-layer-predicate]

## PP4 / DCP8组合的判读

在[P/D配置参考](kimik3-pd-configuration-reference.md)的拓扑中：

- P使用PP4，已不满足目标旁路PP1条件。
- D使用DCP8，已不满足目标旁路DCP1条件。
- 因此目标日志`Speculative CPU length synchronization bypass enabled: False`符合该配置的预期，不表示PR应用失败。
- 该目标日志不直接报告草稿分支。不能进一步断言“整个PR完全没有执行优化”；P侧草稿是否满足自身条件，应另按加载后的backend核对。

历史运行摘要记录64个target worker门控均为false，同配置完整GPQA完成。它证明该次回归经过相应fallback配置，不构成优化激活、draft分支性能或加速比验收；原始运行材料未公开，条目保留candidate。

## 配置与验收方法

保持用户指定的并行配置，将本轮测试定位为相应分支的回归。如果需要验证优化收益，另选有授权且满足全部门控的配置；改变PP/DCP还改变并行和资源条件，不能把不同拓扑的成绩直接归为PR单变量收益。

先核对固定代码，再检查实际进程的并行配置与加载后的每层backend，最后分别记录target gate、draft predicate、真实精度和性能结果。即使target gate为true，也不能仅凭该布尔值宣称数值正确或吞吐提升。

PR、runner生命周期、模型architecture、attention backend、并行、adaptive verification、offload或KVPP实现变化时，重新核对这些条件。source层事实只对本固定提交负责，不将当前门控推广为所有后续版本的永久限制。
