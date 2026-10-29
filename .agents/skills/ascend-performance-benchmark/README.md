# 现有服务性能压测

`ascend-performance-benchmark` 的使用说明，面向提出任务的使用者；详细执行规则以 [SKILL.md](SKILL.md) 为准。

## 能做什么

使用AISBench测量现有模型服务的吞吐、时延、并发和公共前缀负载，或核验补录已有正式性能结果。

## 什么时候用

需要TTFT、TPOT、吞吐等性能数据时使用；精度异常用精度入口，持续瓶颈优化用调优入口。

相邻入口：[ascend-inference-optimization](../ascend-inference-optimization/README.md)、[ascend-model-accuracy](../ascend-model-accuracy/README.md)。

## 怎么调用

- 使用 $ascend-performance-benchmark，对指定现有服务做一次AISBench性能压测，使用我给出的负载和并发，不重启服务。
- 使用 $ascend-performance-benchmark，核验并登记已有AISBench结果，只采集必要CSV/JSON和配置，不重新压测。

## 需要提供什么

服务地址、模型/tokenizer与负载、并发/速率、请求数、采样/流式、重复次数等；已有结果模式指定结果位置。

agent 会先查：任务已有客户端配置、正式阶段原始结果和所用工具版本；只澄清影响可比性的缺项。

## 会产出什么

带单位和统计口径的TTFT、TPOT、吞吐、成功/失败数、重复结果与必要出处；符合条件时登记正式测试表。

## 操作边界

发起压测会向服务发送实际负载；仅核验已有结果不发请求。不会自动部署、重启或升级服务，不把性能结果当精度通过，不默认收集全量诊断日志。

返回[项目功能索引](../../../README.md)。提交、推送和发布统一遵循[项目规则](../../../AGENTS.md)及本轮具体授权。
