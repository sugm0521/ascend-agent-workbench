# HCCL通信打流

## 启动与领域归属

本能力由[性能领域](../ascend-performance/SKILL.md)维护；可直接指定，也可由主/领域调用，按[共用约定](../../../docs/guides/skill-routing.md)复用任务和知识查询。具体输入输出、脚本与原验收边界见[SKILL](SKILL.md)。


`ascend-hccl-traffic-test` 的使用说明，面向提出任务的使用者；详细执行规则以 [SKILL.md](SKILL.md) 为准。

## 能做什么

准备并验证单机或多机HCCL alltoallvc通信，顺序执行ccu_ms和aicpu_ts，按原始结果区分通信、环境及启动问题。

## 什么时候用

明确的通信验证或故障诊断使用；模型服务吞吐/时延测试应使用性能压测入口。

相邻入口：[ascend-performance-benchmark](../ascend-performance-benchmark/README.md)、[ascend-workbench-init](../ascend-workbench-init/README.md)。

## 怎么调用

- 使用 $ascend-hccl-traffic-test，为指定节点规划一次alltoallvc打流，先给我命令和资源检查结果，不执行。
- 使用 $ascend-hccl-traffic-test，在已确认的空闲卡上执行单机HCCL双模式测试，记录两种模式的结果。

## 需要提供什么

节点、卡数/卡范围、容器或宿主、启动节点，以及规模、迭代或时间预算。

agent 会先查：已有MPI/CANN、网卡、连接与卡占用；从实际程序帮助核对参数。

## 会产出什么

打流计划和命令；执行时给出两种模式的原生结果、退出状态及失败分类。

## 操作边界

计划helper不等于已执行。打流会使用所选设备和通信资源，须在授权范围内运行；不停止他人服务，不自动安装环境或创建容器。

返回[项目功能索引](../../../README.md)。提交、推送和发布统一遵循[项目规则](../../../AGENTS.md)及本轮具体授权。
