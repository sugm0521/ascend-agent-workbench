# 参考与适配边界

## 分析输入与方法

先判断当前证据能区分哪个假设，再按[场景选用表](../../../../upstream/skill-mapping.md#按任务选用与重叠处理)的E01–E09、G04–G06定位来源。固定版本由[source lock](../../../../upstream/sources.lock.yaml)和本机配置确定；这里维护输入判断，不另复制来源优先级。输入、环境和本轮授权满足时直接按原专题skill工作，调用其解析脚本或工具，无需先重写为项目实现。分析任务可使用适用的只读解析/查询工具；额外采集、服务重启、安装或业务修改按已有授权范围另核对，缺具体前提只暂停受影响步骤。

| 已有材料或问题 | 先做的判断 | 何时够用、何时转下一步 |
|---|---|---|
| kernel_details/trace，需要step、layer或跨rank报告 | capture/rank/phase、时间单位、采集级别与事件完整性是否适合当前窗口 | 先做整体切分和关键路径；已有报告能回答问题就停止，不再启动另一套完整报告 |
| Profiler DB，需要SQL或具体字段 | 先查实际schema、rank和step范围；SQL查询与通信/计算/调度归因是不同目标 | 精确查询用DB方法；专题问题直接进对应方法，不把DB工具的宽泛触发扩大成必经总流程 |
| HCCL/融合通信核耗时高 | 对齐各rank到达、真实数据量和同窗口重叠，区分等待与传输 | 未排除上游慢计算/调度时不建议换链路；P2P超出方法覆盖时保留限制 |
| Host空泡或计算热点 | 先区分事件丢失、warmup、CPU下发暴露、设备计算暴露和跨流等待 | 按证据选调度或计算专题；绑核、batch或融合候选只在对应假设成立后验证 |
| HBM容量、KV预算，或msMemScope dump/OOM | vLLM服务组件拆分和msMemScope事件是不同输入；查是否已有可用证据 | 分别选对应方法；已有dump先分析，不默认重新采集或在服务上插桩 |
| 两份Prof/集群结果 | 负载、缓存、采集级别、step与工具版本是否可比 | 不等价窗口只报告各自观察；不能用更长窗口的总耗时归因单次改动 |
| 已指向具体算子/msOpProf | 确认生产shape、dtype、当前kernel与device/simulator模式 | 转算子专题；局部counter和微基准不直接推导模型吞吐收益 |
| 材料不足或原MCP/脚本不可用 | 缺失内容是否会改变当前判断，原入口是否要求旧session | 只补能区分假设的最小证据；可离线部分继续，必需缺口明确等待，不换一套管理系统绕过 |

## 上游更新后的复核

本表的时间窗口、数据可比性和证据要求继续适用；来源格式、P2P覆盖、后端接口等版本相关限制随对应原文/脚本更新重新核对。升级时用同一捕获或可比负载比较结论、覆盖和工具输出，改进经验证后可更新所选专题并删除已失效的本地限制。只适配原输入或工具确实不兼容的部分，项目不复制完整归因算法或报告器。更新步骤统一见[依赖维护](../../ascend-workbench-dependencies/references/dependency-check.md#能力发现入口维护)。

## 外部方法来源

本 skill 独立编写；以下外部参考只用于方法查阅，运行不依赖下载这两个参考仓，没有复制其代码、配置表或案例正文。

- [BBuf/AI-Infra-Auto-Driven-SKILLS / llm-serving-auto-benchmark](https://github.com/BBuf/AI-Infra-Auto-Driven-SKILLS/blob/c9dbfe7a4237c88d39a74636cce020bab1731a50/skills/llm-serving-auto-benchmark/SKILL.md)，核对版本 `c9dbfe7a4237c88d39a74636cce020bab1731a50`：参考同负载/SLA 下的候选比较、原生结果留存及 profiling 交接方法。本文将实际负载执行交给本项目 AISBench 入口，并新增 NPU 来源核验、PD 每卡指标及配置/代码实验边界。该版本仓库 license API 返回 404，未取得明确仓库许可；不复制、打包或引入其实现。
- [NVIDIA/TensorRT-LLM / perf-analysis](https://github.com/NVIDIA/TensorRT-LLM/blob/3163e66b2c5b8e5de2995f87dafb06ef62148446/.claude/skills/perf-analysis/SKILL.md)，核对版本 `3163e66b2c5b8e5de2995f87dafb06ef62148446`：参考先分类瓶颈、按适用条件选择案例、验证并保留回退的组织方式。原 skill frontmatter 标注 Apache-2.0；本文独立编写，使用 Ascend 的实际执行证据，不带入 CUDA/Nsight 命令、厂商专属参数或预期数值收益。

本项目依赖版本以[来源锁](../../../../upstream/sources.lock.yaml)为准；分析/回归等旧入口可读不等于与当前运行工具兼容。调用前按[能力映射](../../../../upstream/skill-mapping.md)核对实际入口，缺能力时保留明确缺口。
