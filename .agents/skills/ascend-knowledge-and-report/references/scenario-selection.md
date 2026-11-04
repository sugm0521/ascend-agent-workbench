# 域内场景与来源选择

从本域SKILL按目标进入，只读取相关行及原资源。表中候选未承诺工具就绪；与当前后端/输入不适用时只保留方法范围，不另建运行状态。实际采用记录在upstream-usage.json，原资源路径按lock/本机配置解析。

| 场景与输入 | 本域方法/原资源定位 | 条件与边界 |
|---|---|---|
| H02 工程知识收录/复查 | 项目knowledge-curation负责当前私有库和证据流程；定位：[ascend-knowledge-curation](../../ascend-knowledge-curation/SKILL.md)（主入口）、[PR/提交材料专项](../../ascend-knowledge-curation/references/pr-knowledge-analysis.md)（仅变更知识归纳时读取）、[compound_engineering/ce-compound](../../../../deps/compound-engineering/skills/ce-compound/SKILL.md)（现有方法参考）、[compound_engineering/ce-compound-refresh](../../../../deps/compound-engineering/skills/ce-compound-refresh/SKILL.md)（现有方法参考） | 查询按当前库导航/正文；指定上游材料蒸馏核固定源及父条件；结构维护只在明确授权范围同步规范/模板/索引。PR材料由调用方提供；compound仅方法参考，报告不自动收录或重整知识库 |
| I03 周报与周期回顾 | 项目weekly-report；定位：[ascend-weekly-report](../../ascend-weekly-report/SKILL.md)（主入口） | 工程知识写入与业务验收仍分开；不引入上游日报或任务状态表 |

方法不足时按[依赖能力发现](../../../../upstream/skill-mapping.md#依赖能力发现入口)查询已登记来源，足够即停。候选选择或上游更新影响本域时核对新增/增强/修复及旧适配，采用后同步消费声明与受影响引用。
