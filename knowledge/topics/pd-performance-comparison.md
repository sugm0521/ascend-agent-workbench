---
id: pd-performance-comparison
title: PD性能对照需要固定负载并区分计算、通信与排队长尾
status: candidate
updated_at: '2026-10-18'
verified_at: '2026-10-18'
observed_at: '2026-10-17'
tags: [PD分离, AISBench, prefix-cache, 性能对照, Mooncake, 长尾, NPU占用]
applies_to: PD长输入短输出的性能对照方法；数据生成边界限定aisbench_auto_tools_prefix固定提交ef2b6d8653d57487b622b0dc9db458f8a1e8dec6；历史数字限本文所述部署和测量条件
evidence_scope: 固定客户端源码及已保存分析和验收摘要已复核；历史运行材料未公开，不能由本仓库独立复验运行数字，本次整理未重跑模型或重放原始trace；通信冷态归因仍为候选解释
sources:
  - id: dataset-generation
    path: https://github.com/rayn-zzz/aisbench_auto_tools_prefix/blob/ef2b6d8653d57487b622b0dc9db458f8a1e8dec6/generate_dataset.py
    revision: ef2b6d8653d57487b622b0dc9db458f8a1e8dec6
    locator: generate_unique_tokens L72-90；write_data L148-161；create_multi_prefix_dataset L255-295
    observed_at: '2026-10-18'
    evidence: source
    access: published
  - id: prefix-selection
    path: https://github.com/rayn-zzz/aisbench_auto_tools_prefix/blob/ef2b6d8653d57487b622b0dc9db458f8a1e8dec6/data_picker.py
    revision: ef2b6d8653d57487b622b0dc9db458f8a1e8dec6
    locator: prefix_flag分支的get_unpicked_ids、random.choice及picked_ids更新，L53-62
    observed_at: '2026-10-18'
    evidence: source
    access: published
---

# PD性能对照与归因

## 可复用结论

长输入、输出仅一个token的PD测试仍经过P计算、KV传输、D调度和首次输出等路径。端到端输入吞吐提高，只能先说明完整请求路径更快；即使主要负载来自prefill，也不能直接换算成P算力收益。对照应先确认同一负载，再检查改善落在中位数还是少数长尾，最后核对P/D各自阶段和通信事件。

本条方法可用于设计调查；以下运行数字只是2026-10-17的历史观察，原始材料未公开。不能由该样例推出所有部署的冷启动代价、最佳PP分层或确定根因。

## 固定负载不只固定seed

固定客户端的`create_multi_prefix_dataset`先生成公共前缀，随后才调用内部设置seed的`generate_unique_tokens`；prefix选择还依赖未选数据集合及其持久化状态。[dataset-generation][prefix-selection]

因此，相同seed、名义token长度和前缀比例，不保证实际文本相同；相同命中率也不能代替数据身份。`write_data`使用写入模式打开目标，同名文件存在不表示会被复用。[dataset-generation]

需要同数据对照时，同时固定正式dataset和prefix文件的内容、行序及完整SHA，保留原件；执行副本不得重新生成并覆盖它们。具体兼容边界和最小重放方式见[AISBench调用说明](../../.agents/skills/ascend-performance-benchmark/references/aisbench-auto-tools.md#同数据对照与重放)。

## 历史观察：吞吐变化主要伴随D侧长尾消失

历史部署为Kimi K3/DSpark、TP8、P PP4/DP1、D DP4，P分层`24/24/24/21`。两轮均为输入131072、输出1、并发10、120条正式请求加一条公共前缀预热、配置90%公共前缀，两轮均未采profiling。第二轮复用同一对数据文件，实际token统计和正式缓存命中率相同。

历史代码基线为vLLM `ced6857afa0ea7b2e3f0846a62e1394e90f15607`和vLLM-Ascend `7759ceecee1c3ea21a4d47d55f93545fca895088`，叠加了未完整公开的部署修改。两轮服务进程、启动参数和已核对环境保持一致；这些基线信息仍不足以独立重建运行，不能作为完整复现声明。

| 指标 | 首次纯性能测量 | 同数据复测 |
|---|---:|---:|
| 正式耗时(s) | 121.7178 | 88.4295 |
| 输入吞吐(token/s) | 129308.9895 | 177985.8691 |
| TTFT P50(s) | 7.2891 | 7.2005 |
| TTFT P99(s) | 40.7020 | 11.4406 |
| TTFT超过15秒的正式请求 | 13 | 0 |
| P平均prefill阶段(s) | 5.4933 | 5.5673 |
| D按请求数加权的平均排队(s) | 1.3809 | 0.1333 |
| 超过1秒的KV传输日志事件 | 408 | 0 |

两轮正式总输入相同，输入吞吐包含命中的公共前缀tokens。服务阶段均值包含一条预热和120条正式请求；客户端TTFT只含120条正式请求，口径不同，不相加减。TP传输事件可以重叠，也不能累加为端到端请求耗时。

该例P阶段均值基本相当、中位数接近，但首轮出现多条30秒以上请求。固定并发下，长请求持有槽位会推迟后续派发；应先调查传输和排队长尾，而不是仅凭总吞吐推断计算优化。

## Prefix预热与通信预热分开判定

公共前缀预热成功，只证明对应请求路径已执行，不证明所有D节点、通信peer和接收路径都已进入相同状态。记录实际D分流；若要比较覆盖全部D的稳态能力，应确认参与节点和代表性peer都被负载覆盖，冷态结果另列。不要把该要求扩展成每次普通测试都必须新增全量预热。

历史首轮在测量期间出现348条`Connected to segment`日志，复测无新增同类事件；同时D侧秒级传输和排队长尾消失。两轮D分流与测前运行历史不同，支持首次通信/接收状态的候选解释，但没有对应trace量化建链、注册、同步与调度的独立贡献。日志条数不等于串行连接次数，不能将全部耗时差值归因于建链。

连接预算和同步batch预算的实现分工复用[Mooncake分层超时条目](mooncake-nested-timeout.md)。放宽超时或观察到连接成功，都不表示冷态开销已经消除。

## 绑定测量窗口与请求身份

- 怀疑NPU争用时，先对齐原生正式请求区间与已有占用记录，再区分测前、测中和测后。历史样例的近似正式窗口内有64份节点巡检均未观察到外部NPU进程，但约15秒一次的离散检查不能排除采样间隙的短暂占用；不能将另一个时段的进程套用到该轮。
- 跨机日志优先用已验证的请求身份或日志字节边界关联，记录完整备份与摘要的对应关系。样例中P/D保留共同proxy UUID、各自附加不同引擎后缀；只有核对目标实现、唯一性及请求覆盖后，才能按共同部分关联，不能通用地截掉固定字符。AISBench本地记录UUID也不能未经核对当作proxy UUID。
- 未校准多机时钟时，不相减绝对时间计算精密跨机等待。服务counter差分的请求数、预热范围和每D路由应与原生结果核对；单看累计计数不能界定本轮。

## 不能推出的结论与复查条件

本例未证实同期外部NPU占用是首轮慢的原因，也未证明全部差值由建链造成。一次较快复测不证明稳定最优性能；没有独立对照时，不能将配置、分层或profiling视为收益来源。纯性能与采样轮及采集窗口判读复用[profiler窗口条目](profiler-stop-window-boundaries.md)。

客户端seed/生成逻辑、数据选择状态、tokenizer、连接器实现、P/D拓扑、路由或预热条件变化时，复查对应结论；请求ID或日志格式变化时重新验证关联规则。取得可公开复验的运行材料或独立控制实验后，再考虑升级冷态归因的证据等级。
