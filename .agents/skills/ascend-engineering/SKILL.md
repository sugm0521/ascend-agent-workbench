---
name: ascend-engineering
description: 处理Ascend工程的一般代码调查与实现、源码学习、CI/PR和文档审查及实际Agent/SWE评测，按真实对象选专项方法。已明确的性能、模型精度、算子和部署目标交对应领域。
metadata:
  workbench_role: domain_entry
  workbench_domain: engineering
---

# 通用工程开发与审查领域

遵循[根规则](../../../AGENTS.md)和[分层协作](../../../docs/guides/skill-routing.md)。先复用目标/授权和当前任务；按组件、首错、源码/CI workflow及验证/恢复边界查相关知识，新证据或方向变化再补查。

| 目标 | 推进与交付依据 |
|---|---|
| 业务代码调查/修复、功能实现 | 实际源码、触发条件和测试；调查授权不自动成为修复，确认范围内由execution推进 |
| 源码学习 | 固定版本的连续调用链，区分源码事实/推断，不依赖作者个人source skill |
| CI/PR审查 | 当前diff、head SHA、真实workflow/job及终态；按对象选语言审查方法，不因审查自动写回PR或提交 |
| 文档体验/quickstart审查 | 明确执行边界，按原说明走真实可用路径；msagent document-ux-review为对应候选，不自动安装/部署 |
| Agent/SWE任务评测 | 核对实际runner、数据集、采样和原生评分/退出；没有统一runner时明确缺口，不能用性能AISBench代替 |

本领域不固定依赖某一个外部skill仓。候选与资源见[域内选用](references/scenario-selection.md)；Matt/CE代码审查、msagent文档体验、workspace变更验证按具体目标评估，不同时启用多套完整工程工作流。

已明确专业对象时交[性能](../ascend-performance/SKILL.md)、[精度](../ascend-model-accuracy/SKILL.md)、[算子](../ascend-operator/SKILL.md)、[部署](../ascend-deployment/SKILL.md)或[模型分析与适配](../ascend-model-engineering/SKILL.md)。领域未知时先查事实再分流；方法不足按共用发现协议找已登记来源，目录未列出不表示能力不存在。

复用planning/execution/review及原Git/执行工具。按实际变更验证正常与边界路径，清晰交付证据、改动、未验范围和恢复状态；提交/推送/PR描述沿具体授权，不自动扩大为公共工具、知识写入或新skill。
