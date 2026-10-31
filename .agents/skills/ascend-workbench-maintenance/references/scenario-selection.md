# 域内场景与来源选择

从本域SKILL按目标进入，只读取相关行及原资源。表中候选未承诺工具就绪；与当前后端/输入不适用时只保留方法范围，不另建运行状态。实际采用记录在upstream-usage.json，原资源路径按lock/本机配置解析。

| 场景与输入 | 本域方法/原资源定位 | 条件与边界 |
|---|---|---|
| A03 Skill使用反馈、评估与开发 | 使用反馈按[本域反馈流程](skill-feedback.md)准备本仓草稿；candidate-review决定是否值得改，development实施已授权范围；定位：[ascend-skill-candidate-review](../../ascend-skill-candidate-review/SKILL.md)（评估入口）、[ascend-skill-development](../../ascend-skill-development/SKILL.md)（实施入口） | 参与偏好仅控制主动邀请；Issue不以完成候选评估为门槛，每次公开发布须审核当次最终资料；外部审查器按实际检查缺口评估，不把反馈/评估变成修复授权 |
| A04 首次与增量接入、安全同步、固定依赖变化 | init负责首次完整准备、更新差异与新功能增量接入，repository-update负责安全同步，dependencies负责固定来源兼容；定位：[ascend-workbench-init](../../ascend-workbench-init/SKILL.md)（首次接入）、[ascend-repository-update](../../ascend-repository-update/SKILL.md)（安全同步）、[ascend-workbench-dependencies](../../ascend-workbench-dependencies/SKILL.md)（依赖维护）、[workspace/repo-init](../../../../deps/vllm-ascend-workspace/.agents/skills/repo-init/SKILL.md)（条件方法） | workspace repo-init仅在原布局和所选能力适用时使用；同步影响发现/接入时交init只读检查，必要准备只补确认项；三者不互跑完整流程 |

方法不足时按[依赖能力发现](../../../../upstream/skill-mapping.md#依赖能力发现入口)查询已登记来源，足够即停。候选选择或上游更新影响本域时核对新增/增强/修复及旧适配，采用后同步消费声明与受影响引用。
