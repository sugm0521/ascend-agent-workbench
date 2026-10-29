# Skill改进候选评估

`ascend-skill-candidate-review` 的使用说明，面向提出任务的使用者；详细执行规则以 [SKILL.md](SKILL.md) 为准。

## 能做什么

判断候选的实际价值、已有覆盖、重复性和维护成本，给出不改、复用或最小修改的建议。

## 什么时候用

明确要求评估skill优化、新能力或经验提炼时使用；已经确认的实施交给开发入口。

相邻入口：[ascend-skill-development](../ascend-skill-development/README.md)、[ascend-knowledge-curation](../ascend-knowledge-curation/README.md)。

## 怎么调用

- 使用 $ascend-skill-candidate-review，评估这个重复失败是否值得补到现有skill，先给最小方案，不修改。
- 使用 $ascend-skill-candidate-review，检查这项候选是否已被其他入口覆盖，比较复用、补引用和新建的成本。

## 需要提供什么

具体问题、候选目标与直接证据，或能定位到它们的任务/文件；说明希望评估的范围。

agent 会先查：现有skill、引用和相关工具，优先找覆盖与遗漏，不全量扫描历史。

## 会产出什么

少量候选或无需修改结论，附触发条件、已有覆盖、最小位置、收益/成本和验证方式。

评估过程和待决定项留当前本机任务；仅已确认要实施的工作台/skill改进进入开发计划，实际修改及原因进入开发记录。工程经验按[知识维护](../ascend-knowledge-curation/README.md)吸收，不把知识待验证状态变成开发待办。

## 操作边界

评估不自动实施、新建skill、改业务代码或安装工具；有价值不等于已获收录/发布授权。不会为凑候选给正常路径堆叠检查。

返回[项目功能索引](../../../README.md)。提交、推送和发布统一遵循[项目规则](../../../AGENTS.md)及本轮具体授权。
