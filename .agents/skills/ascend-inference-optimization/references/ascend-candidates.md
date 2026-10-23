# 按 Ascend 证据选择下一项改动

下表是候选方向，不是默认参数或平台支持承诺。依据当前芯片、目标源码和 `--help` 核对支持范围，再从 worker/日志/trace 确认实际生效。CUDA/ROCm 的工具、环境变量、kernel 分类和案例数值不能直接作为 NPU 的执行配置。

| 观察到的证据 | 下一步检查与候选 | 需要排除的误判 |
|---|---|---|
| 请求队列增长、批次很小、卡间空闲且 Host 准备暴露 | 检查调度、tokenization、请求路由和实际 batch；按负载验证并发、`max_num_seqs`、`max_num_batched_tokens` 等候选 | 客户端限流、P/KV 供应不足、其他占用；不是看到低利用率就扩大 batch |
| prefill 占主导、长请求影响其他请求 TTFT | 检查 chunked prefill、batch token 预算与并行方案的支持及开销 | 改输入长度或缓存状态造成不可比；decode 和端到端退化 |
| decode 访存/attention 暴露，KV 预算限制批次 | 核对实际上下文、KV 布局、分片/CP 和可用 HBM；需要时评估 KV 精度方案 | 名义显存利用率不等于可用容量；精度与额外通信成本 |
| Host 下发空泡、细碎 kernel、图路径未覆盖 | 检查当前图模式、capture shape、回退与编译路径；在支持范围内验证 capture/融合 | profiler 丢事件或 warmup；图模式改变后的精度/shape 覆盖 |
| HCCL 或融合通信核占关键路径、跨 rank 明显不均 | 关联真实参与组、数据量、拓扑、rank 到达时间和专家负载；验证 TP/EP/DP/PP 或调度候选 | 计算/通信重叠重复计时，等待被算入融合核，慢 rank 导致陪跑 rank 等待 |
| 分配/释放/映射与同步显著，存在恢复性 OOM/重试 | 核对同窗口内存日志、workspace/KV/中间量生命周期；选择有源码支持的预算或复用候选 | HTTP 成功掩盖重试；CPU API 时长误当设备 kernel 时间 |
| 少数算子在生产 shape 持续暴露且有融合机会 | 核对当前实际 kernel、dtype/layout/shape 和已有融合，再交给算子优化路径 | 未加载候选、非关键路径算子、微基准收益未传到端到端 |
| MTP/投机接受率或 draft 成本异常 | 核对模型/后端支持、accepted tokens、draft/verify 时间与实际输出分布 | 只看名义投机 token 数；更改采样或接受语义后未验证输出质量 |

分析事件时保留 capture、phase、rank、step 与可比窗口。使用多流忙碌区间并集及暴露等待判读关键路径；硬件 counter 只能用于其原生覆盖窗口。必要时下钻更多 rank，找到足以区分假设的证据后停止扩采。

方法参考及固定源码定位见[来源说明](sources.md)。这些参考只用于方法查阅，不是运行时依赖。
