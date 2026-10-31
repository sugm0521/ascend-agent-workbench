# 代码仓安全同步

## 启动与领域归属

本能力由[工作台维护领域](../ascend-workbench-maintenance/SKILL.md)维护；可直接指定，也可由主/领域调用，按[共用约定](../../../docs/guides/skill-routing.md)复用任务和知识查询。具体输入输出、脚本与原验收边界见[SKILL](SKILL.md)。


`ascend-repository-update` 的使用说明，面向提出任务的使用者；详细执行规则以 [SKILL.md](SKILL.md) 为准。

## 能做什么

核对仓库、分支、远端、未提交内容与目标版本，安全同步代码，并分流固定依赖升级及首次接入。

## 什么时候用

已接入仓库的更新或同步使用；首次准备仓库走初始化，工作台固定依赖组合升级走依赖入口。

相邻入口：[ascend-workbench-init](../ascend-workbench-init/README.md)、[ascend-workbench-dependencies](../ascend-workbench-dependencies/README.md)。

## 怎么调用

- 使用 $ascend-repository-update，检查指定业务仓与已配置远端分支的差异，先只读，不fetch、不合入。
- 使用 $ascend-repository-update，将指定业务分支安全同步到已确认目标，保留现有未提交工作，不推送。

## 需要提供什么

实际仓库或已绑定项目、目标分支/ref，以及只查询还是授权同步；明确正在使用的工作。

agent 会先查：真实Git根、HEAD、远端、tracking和dirty内容；业务双仓核对适用的CI配对。

工作台更新影响skill发现、客户端入口或接入要求时，交init只读检查已启用能力的差异，补齐按具体授权执行。源码更新不代表外层项目已发现新入口；普通业务仓同步保持原范围。

## 会产出什么

同步前后SHA、分支及保留的修改；不可快进或存在冲突时给出差异、缺口和待决定项。

## 操作边界

只查询不自动fetch、切分支或合入。更新授权不包含发布；不reset/覆盖现有工作，分叉时不擅自merge/rebase，不自动重装环境或重启服务。

返回[项目功能索引](../../../README.md)。提交、推送和发布统一遵循[项目规则](../../../AGENTS.md)及本轮具体授权。
