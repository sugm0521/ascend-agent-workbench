---
name: ascend-knowledge-and-report
description: 统筹工程知识检索、收录/复查和周报等周期报告，按查询、维护或报告目标调用本仓能力。普通业务可直接查询相关知识，无需绕行本入口；报告不自动写知识库。
metadata:
  workbench_role: domain_entry
  workbench_domain: knowledge_report
---

# 知识与报告领域

遵循[根规则](../../../AGENTS.md)和[分层协作](../../../docs/guides/skill-routing.md)。明确本轮是查询、维护还是报告，复用已有范围和授权。知识检索本身只读；原始业务状态仍由任务记录/实际工具提供。

| 目标 | 本仓能力与停止条件 |
|---|---|
| 查已有经验/方法或评估知识收录 | [knowledge-curation](../ascend-knowledge-curation/SKILL.md)：解析私有根和规则，定向检索/核对；取得足够结论或明确缺口即停止 |
| 已授权收录、复查/合并/修正知识 | 同上沿库内历史和证据规则；具体写入与Git同步分别授权，不按更新时间覆盖结论 |
| 周报/周期回顾与展示 | [weekly-report](../ascend-weekly-report/SKILL.md)：从任务和实际变更生成报告，不为渲染而全库搜索；技术解释需要时查相应主题 |

知识归纳/复查方法经curation引用compound；周报用本仓报告器，Node/marked是其独立渲染前提，不因此依赖全部skill仓。专题见[域内选用](references/scenario-selection.md)。候选方法不足按发现协议核对，但不引入另一套知识正文或任务系统。

本入口不垄断业务查询：主、领域、具体能力均按共用事件触发查询，已有结果可交接复用。candidate保留假设和缺口，verified限原条件；不把知识当当前服务状态或运行通过证明。

交付命中/覆盖/缺口及证据范围，或本轮授权的知识变更/报告。私有正文、索引、历史和原始材料留绑定私有库/任务；公开skill只保留通用方法，不默认提交、同步或安排自动化。
