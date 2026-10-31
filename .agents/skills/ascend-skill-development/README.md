# 自有Skill开发与维护

## 启动与领域归属

本能力由[工作台维护领域](../ascend-workbench-maintenance/SKILL.md)维护；可直接指定，也可由主/领域调用，按[共用约定](../../../docs/guides/skill-routing.md)复用任务和知识查询。具体输入输出、脚本与原验收边界见[SKILL](SKILL.md)。


`ascend-skill-development` 的使用说明，面向提出任务的使用者；详细执行规则以 [SKILL.md](SKILL.md) 为准。

## 能做什么

在已确认范围内创建或优化项目自有skill及必要资源，验证入口发现、格式、引用与代表请求的行为。

## 什么时候用

候选已评估且获具体实施授权时使用；尚未决定是否值得建设时先评估。

相邻入口：[ascend-skill-candidate-review](../ascend-skill-candidate-review/README.md)、[ascend-task-review](../ascend-task-review/README.md)。

## 怎么调用

- 使用 $ascend-skill-development，按已确认方案优化指定skill，先验证再给我看diff，不提交推送。
- 使用 $ascend-skill-development，创建已经批准的新skill，说明适用边界，验证触发请求和容易误用的请求。

## 需要提供什么

明确批准的候选/修改范围、预期行为、允许新增的资源及验收条件。

agent 会先查：现有维护源、skill-creator规范和固定依赖来源；不把个人全局安装当作发布前提。

## 会产出什么

范围内的skill/资源改动、审核diff、格式与引用检查、代表用法验证和未验证项。

新增 skill 配套使用说明和索引；现有内容按影响维护相关指南、模板、配置说明及其他 skill 调用约定，交付时说明同步结果或无需修改的理由。详细条件见 [SKILL.md](SKILL.md#开发已确认-skill)。

替换或迁移规则时，同步处理受影响的旧规则、入口和调用方，说明清理结果及保留原因。

交付还包括项目角色/领域、领域挂接、实际消费JSON和当前客户端发现；各模块都有显式声明，确认无采用才用空uses。缺声明不能靠格式或链接通过代替；新增接入按具体授权处理。

## 操作边界

不因普通业务任务自动新建skill，不改外部来源或全局安装。删除或合并整个skill、改变功能范围或必需验收标准、新候选及未授权依赖需具体决定；已授权优化内的重复规则清理与引用更新直接实施，提交推送仍按本轮授权。

返回[项目功能索引](../../../README.md)。提交、推送和发布统一遵循[项目规则](../../../AGENTS.md)及本轮具体授权。
