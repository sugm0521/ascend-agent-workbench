# 固定依赖核对与升级

`ascend-workbench-dependencies` 的使用说明，面向提出任务的使用者；详细执行规则以 [SKILL.md](SKILL.md) 为准。

## 能做什么

核对领域依赖及相关传递依赖，评估目标父提交约束、受影响接口、兼容验证与回退，按授权切换已验证组合。

## 什么时候用

固定版本核对、依赖漂移或明确升级请求使用；首次接入用初始化，普通代码同步用更新入口。

相邻入口：[ascend-workbench-init](../ascend-workbench-init/README.md)、[ascend-repository-update](../ascend-repository-update/README.md)。

## 怎么调用

- 使用 $ascend-workbench-dependencies，检查本次任务所用依赖是否偏离固定版本，给出影响，不切换版本。
- 使用 $ascend-workbench-dependencies，为指定依赖升级评估目标组合和回退方案，先验证受影响入口，再给我看修改。

## 需要提供什么

要核对或升级的来源、目标版本/问题、本轮用途及允许变更范围。

agent 会先查：当前父/子SHA、声明、接口、dirty状态和正在使用的组合；只查本次相关依赖。

## 会产出什么

实际与目标版本、受影响依赖关系、验证分层、未执行项、候选/切换结果与回退信息。

## 操作边界

检查请求不等于升级授权，不默认全生态fetch或拉最新。保护运行实验和业务分支，不改外部维护源，不顺带更新业务子模块；发布按具体授权。

返回[项目功能索引](../../../README.md)。提交、推送和发布统一遵循[项目规则](../../../AGENTS.md)及本轮具体授权。
