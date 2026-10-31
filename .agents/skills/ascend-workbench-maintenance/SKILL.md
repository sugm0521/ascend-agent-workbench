---
name: ascend-workbench-maintenance
description: 统筹工作台初始化、仓库安全同步、依赖检查与吸收升级、自有skill建设和发布准备。用于维护工作台及来源消费关系；业务模型、算子、部署或性能工作交对应领域。
metadata:
  workbench_role: domain_entry
  workbench_domain: maintenance
---

# 工作台维护领域

遵循[根规则](../../../AGENTS.md)和[分层协作](../../../docs/guides/skill-routing.md)。可直接启动，复用任务/授权和已有工具状态；不把每次维护变成完整初始化。

按所选来源、父声明、接口、旧适配或配置迁移定向检索已有知识；升级改变其适用前提时复核，已有结果仍有效则复用。

| 用户目标 | 本仓执行能力 |
|---|---|
| 首次接入、补齐/恢复缺失配置 | [init](../ascend-workbench-init/SKILL.md)：先集中核对本轮必要选择，按现状只补缺失 |
| 同步工作台/业务仓 | [repository-update](../ascend-repository-update/SKILL.md)：保护dirty/staged与分支；固定来源升级交dependencies |
| 版本核对、上游变化、候选兼容/吸收/采用/回退 | [dependencies](../ascend-workbench-dependencies/SKILL.md)，按[消费与升级约定](../../../docs/maintenance/upstream-consumption.md)组织事实与验证 |
| 评估是否值得融合、自建、合并或清理 | [candidate-review](../ascend-skill-candidate-review/SKILL.md)：不自动将每个候选变成建设任务 |
| 已授权skill创建/优化 | [skill-development](../ascend-skill-development/SKILL.md)：复用评估，更新受影响调用方/README/索引 |
| 提交/发布准备 | [task-review](../ascend-task-review/SKILL.md)及原Git工具：范围、DCO、验证与实际授权分别核对 |

专题见[域内选用](references/scenario-selection.md)。九个来源是可检查/准备对象，不是本入口或每个维护能力的九项运行依赖；只按本次范围读原声明，不能自动安装、升级或启用整个生态。

来源消费/吸收记录覆盖主skill、领域、具体能力及共用模块。检查新增能力，也比较已有能力增强/修复；按同一输入/证据评估改进，复查被上游覆盖的本地适配。未命中时按共用发现协议检索，不按目录数量凑新skill。

保持正在运行的实验、原provider和业务基线；候选不能隔离或必需验证不足时仅暂停受影响切换。纯文本/方法重构不升级Python环境，实际工具升级才按原工具支持的方式保存/恢复环境和绑定。报告采用/暂缓、清理项、验证范围及回退入口，不把检查视为切换或发布授权。
