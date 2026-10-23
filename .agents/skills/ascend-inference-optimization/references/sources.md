# 参考与适配边界

本 skill 为项目自有流程说明；没有复制第三方代码、配置表或案例正文。外部参考仅用于方法查阅，运行不依赖下载这些仓库。

- [BBuf/AI-Infra-Auto-Driven-SKILLS / llm-serving-auto-benchmark](https://github.com/BBuf/AI-Infra-Auto-Driven-SKILLS/blob/c9dbfe7a4237c88d39a74636cce020bab1731a50/skills/llm-serving-auto-benchmark/SKILL.md)，核对版本 `c9dbfe7a4237c88d39a74636cce020bab1731a50`：参考同负载/SLA 下的候选比较、原生结果留存及 profiling 交接方法。本文将实际负载执行交给本项目 AISBench 入口，并新增 NPU 来源核验、PD 每卡指标及配置/代码实验边界。该版本仓库 license API 返回 404，未取得明确仓库许可；不复制、打包或引入其实现。
- [NVIDIA/TensorRT-LLM / perf-analysis](https://github.com/NVIDIA/TensorRT-LLM/blob/3163e66b2c5b8e5de2995f87dafb06ef62148446/.claude/skills/perf-analysis/SKILL.md)，核对版本 `3163e66b2c5b8e5de2995f87dafb06ef62148446`：参考先分类瓶颈、按适用条件选择案例、验证并保留回退的组织方式。原 skill frontmatter 标注 Apache-2.0；本文独立编写，使用 Ascend 的实际执行证据，不带入 CUDA/Nsight 命令、厂商专属参数或预期数值收益。

本项目依赖版本以[来源锁](../../../../upstream/sources.lock.yaml)为准；分析/回归等旧入口可读不等于与当前运行工具兼容。调用前按[能力映射](../../../../upstream/skill-mapping.md)核对实际入口，缺能力时保留明确缺口。
