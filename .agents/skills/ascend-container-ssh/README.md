# 已有容器的独立SSH入口

`ascend-container-ssh` 的使用说明，面向提出任务的使用者；详细执行规则以 [SKILL.md](SKILL.md) 为准。

## 能做什么

为手工部署的已有Linux容器建立或恢复独立SSH登录入口，核对端口、认证并验证实际登录。

## 什么时候用

需要直接SSH登录已有容器时使用；托管目标沿用原接入工具，仅docker exec进入无需此流程。

相邻入口：[ascend-workbench-init](../ascend-workbench-init/README.md)、[ascend-runtime-snapshot](../ascend-runtime-snapshot/README.md)。

## 怎么调用

- 使用 $ascend-container-ssh，为我指定的已有容器配置独立SSH，使用已有公钥，先核对可用端口。
- 使用 $ascend-container-ssh，检查已有容器SSH入口为什么无法登录，先只读定位，不改认证配置。

## 需要提供什么

目标宿主/容器、访问端、账号及认证选择；缺失且无法从记录核实的凭据需安全补充。

agent 会先查：已有端口、转发路径、SSH配置与适用公钥；不从容器名字推断归属。

## 会产出什么

经实际登录验证的连接地址、端口和账号，或明确的入口缺口；报告变更及服务生命周期。

## 操作边界

明确配置请求会修改容器内SSH相关配置。检查请求保持只读；不自动重建容器、改宿主防火墙或扩大为模型测试，不在聊天展示口令。

返回[项目功能索引](../../../README.md)。提交、推送和发布统一遵循[项目规则](../../../AGENTS.md)及本轮具体授权。
