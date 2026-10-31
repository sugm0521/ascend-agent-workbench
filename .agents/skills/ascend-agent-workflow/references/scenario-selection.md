# 域内场景与来源选择

从本域SKILL按目标进入，只读取相关行及原资源。表中候选未承诺工具就绪；与当前后端/输入不适用时只保留方法范围，不另建运行状态。实际采用记录在upstream-usage.json，原资源路径按lock/本机配置解析。

| 场景与输入 | 本域方法/原资源定位 | 条件与边界 |
|---|---|---|
| A01 目标澄清 | 项目workflow组织事实核对和必要澄清；定位：[ascend-agent-workflow](../SKILL.md)（主入口）、[matt/grilling](../../../../deps/matt-pocock-skills/skills/productivity/grilling/SKILL.md)（方法参考） | matt grilling只提供提问方法；已有目标和授权直接复用；不引入上游setup/问卷系统 |
| A02 计划、依赖与交接 | 项目planning/execution/review分别负责计划、推进与验收；定位：[ascend-task-planning](../../ascend-task-planning/SKILL.md)（计划）、[ascend-task-execution](../../ascend-task-execution/SKILL.md)（执行）、[ascend-task-review](../../ascend-task-review/SKILL.md)（验收）、[matt/to-tickets](../../../../deps/matt-pocock-skills/skills/engineering/to-tickets/SKILL.md)（方法参考）、[matt/handoff](../../../../deps/matt-pocock-skills/skills/productivity/handoff/SKILL.md)（方法参考） | matt to-tickets/handoff仅借拆分和交接方法；不另建外部tracker，不并行启用compound完整工作流 |

方法不足时按[依赖能力发现](../../../../upstream/skill-mapping.md#依赖能力发现入口)查询已登记来源，足够即停。候选选择或上游更新影响本域时核对新增/增强/修复及旧适配，采用后同步消费声明与受影响引用。
