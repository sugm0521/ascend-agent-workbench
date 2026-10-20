---
id: dspark-pd-spec-state-layout
title: Kimi K3 的 DSpark 预算是 PD 状态布局条件
status: candidate
updated_at: 2026-10-19T09:18:44+08:00
verified_at: 2026-10-19T09:18:44+08:00
observed_at: 2026-10-19T03:13:06.276334+08:00
tags: [KimiK3, DSpark, KDA, PD分离, Mooncake, Mamba, spec_num]
applies_to: vLLM-Ascend b411aca2577f5e1858cd431fba183eaad4a37086 和 2581a69bcc16ee6af56e72985a15799bb5f61808，分别配套 vLLM ced6857afa0ea7b2e3f0846a62e1394e90f15607 和 c4df37dfcc7f72ca41cd43801a468526ecf99a2b 的 Kimi K3 KDA/Mooncake 状态搬运路径
evidence_scope: 固定公开源码及本地CPU合成元数据验证；未运行真实PD/NPU、未验证输出精度或性能，其他补丁和RecoverSSM路径需另查
sources:
  - id: shape-main
    path: https://github.com/vllm-project/vllm/blob/c4df37dfcc7f72ca41cd43801a468526ecf99a2b/vllm/model_executor/layers/mamba/mamba_utils.py
    revision: c4df37dfcc7f72ca41cd43801a468526ecf99a2b
    locator: MambaStateShapeCalculator.kda_state_shape L303-326
    observed_at: 2026-10-19T03:13:06.276334+08:00
    evidence: source
    access: published
  - id: shape-v030
    path: https://github.com/vllm-project/vllm/blob/ced6857afa0ea7b2e3f0846a62e1394e90f15607/vllm/model_executor/layers/mamba/mamba_utils.py
    revision: ced6857afa0ea7b2e3f0846a62e1394e90f15607
    locator: MambaStateShapeCalculator.kda_state_shape L298-321
    observed_at: 2026-10-19T03:13:06.276334+08:00
    evidence: source
    access: published
  - id: v2-main
    path: https://github.com/vllm-project/vllm-ascend/blob/2581a69bcc16ee6af56e72985a15799bb5f61808/vllm_ascend/distributed/kv_transfer/kv_p2p/mooncake/pull_worker.py
    revision: 2581a69bcc16ee6af56e72985a15799bb5f61808
    locator: MooncakePullRecvingThread._append_mamba_transfer_addresses L918-1099；状态块选择L898-900
    observed_at: 2026-10-19T03:13:06.276334+08:00
    evidence: source
    access: published
  - id: v2-v030
    path: https://github.com/vllm-project/vllm-ascend/blob/b411aca2577f5e1858cd431fba183eaad4a37086/vllm_ascend/distributed/kv_transfer/kv_p2p/mooncake/pull_worker.py
    revision: b411aca2577f5e1858cd431fba183eaad4a37086
    locator: MooncakePullRecvingThread._append_mamba_transfer_addresses L918-1099
    observed_at: 2026-10-19T03:13:06.276334+08:00
    evidence: source
    access: published
  - id: v1-main
    path: https://github.com/vllm-project/vllm-ascend/blob/2581a69bcc16ee6af56e72985a15799bb5f61808/vllm_ascend/distributed/kv_transfer/kv_p2p/mooncake_connector.py
    revision: 2581a69bcc16ee6af56e72985a15799bb5f61808
    locator: KVCacheRecvingThread._append_mamba_transfer_meta L1202-1294；接收块选择L925-948；发送端归一化L1829-1867
    observed_at: 2026-10-19T03:13:06.276334+08:00
    evidence: source
    access: published
  - id: v1-v030
    path: https://github.com/vllm-project/vllm-ascend/blob/b411aca2577f5e1858cd431fba183eaad4a37086/vllm_ascend/distributed/kv_transfer/kv_p2p/mooncake_connector.py
    revision: b411aca2577f5e1858cd431fba183eaad4a37086
    locator: KVCacheRecvingThread._append_mamba_transfer_meta L1195-1287；接收块选择L918-941；发送端归一化L1818-1856
    observed_at: 2026-10-19T03:13:06.276334+08:00
    evidence: source
    access: published
---

## 结论与适用条件

在上述固定实现中，`spec_num`（`speculative_config.num_speculative_tokens`，下记 K）影响主模型 KDA 状态布局。保持 P/D 的 K 一致是当前状态兼容条件之一；P 只做 prefill 不能作为忽略该条件的理由。配置全貌见[Kimi K3 P/D参考](kimik3-pd-configuration-reference.md)，本条解释预算一致性的源码原因，不提供新的最优参数。

卷积核长 w、KDA 头数 H、head_dim d、TP=T 时，卷积通道 C=3Hd/T，状态时间长度 S=w−1+K。SD 布局为 `(S,C)`，DS 为 `(C,S)`，有效字节数为 S×C×dtype_size；基础 recurrent state 的单块形状不随 K 改变。相同 page stride 或相同草稿权重不能证明 conv 状态兼容（shape-main、shape-v030）。

例如 w=4、H=4、d=2、TP=1、dtype为2字节时，K=1 的 conv 有效192字节，K=3 为288字节。此为合成几何，不代表生产模型尺寸。

## 两代 connector 的约束不同

| 路径 | 固定源码行为 | 不同 K 的后果与边界 |
|---|---|---|
| V2，同 TP | 比较双方有效 block 字节数 | conv 长度不同会拒绝元数据；这是合成调用的报错路径，不是线上故障归因 |
| V2，异 TP 的二维 conv 分支 | 校验首维并做通道切片 | 对本次 SD 布局，首维是 S，不同 K 被拒绝；不泛化为 DS 路径已验收 |
| V1，状态搬运 | 以 D 的 conv 长度/形状构造读取 | 没有不同 S 间转换；K_D较大时可能超出P的逻辑有效状态，较小时可能少搬或错配，不能据此断言物理越界或输出已错 |
| V1，align 模式 | P 归一化并提供最终状态块，D使用该块 | 选块已不依赖 D 的 K，conv 布局兼容要求仍存在 |
| V1，非 align | D 使用 `len(remote_group_block_ids)-K_D-1` | K不同时另有选中推测块或下标检查失败的风险 |

V2 的发送端先去掉自己的推测块，D再取远端最终状态块；不要套用 V1 非 align 的跨端索引解释。两个固定分支的 V2 该文件相同，shape及V1搬运/发送端归一化函数AST一致；没有发现这两个分支之间已加入不同K转换的证据（v2-main/v030、v1-main/v030）。

## 证据与可复核方法

原源码调查时间为2026-10-19 03:13北京时间；本次复核逐字节核对48份源码快照与固定Git blob，并重新从源码抽取纯元数据函数在CPU执行：V1搬运24组、align归一化8组、非align索引6组、V2校验18组，共56组；4个关键函数跨分支AST一致。未导入torch/torch_npu，未发送模型请求。

公开读者可从上列固定源码独立核对 S 的计算、V2字节数/首维校验，以及V1的布局搬运和选块分支。合成检查使用上述小几何，比较 K=(3,3)/(1,3)/(3,1) 与 P/D TP=1/1、2/1、1/2；相同K仅表示所测元数据分支接受，不是服务验收。原运行材料和任务状态不作为公开复验的必需输入。

## 不能推出的结论与复查触发

本条不能判定任意部署不同K必然报错，也不能用来解释未绑定实际版本的乱码、超时或吞吐变化。部署叠加补丁、其他connector、RecoverSSM、DS布局、图重放及真实token位置恢复均需按实际路径核验。

允许不同K需要按有效历史与接受位置设计状态转换，同时保持已提交recurrent state和token位置一致。只放宽校验、取最小字节数或修改块下标不构成正确性证明；本次未实施此类改动。shape计算、connector元数据/布局或状态恢复逻辑变化时复查，并以真实PD状态与输出一致性验收后再扩大适用范围。
