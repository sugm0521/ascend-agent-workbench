# 工程任务主入口

`ascend-agent-workflow`负责明确目标、必要澄清、任务恢复、领域选择及跨领域交付。详细流程见[SKILL](SKILL.md)，八领域见[索引](../../../upstream/skill-mapping.md#领域入口)。

可以说“使用主workflow推进这个工程目标”；已明确性能/精度/部署等目标时，也可直接用领域或具体能力。不会因为直接启动而重复建立任务或重新询问已知信息。

输入为目标、已有材料、版本/环境与具体授权；输出为推进路径、实际结果/证据、验证范围和下一步。简单问答保持轻量，多agent和完整计划仅在需要时采用。

主入口融合Matt grilling的事实自查、分轮澄清和停止条件；来源见[消费声明](references/upstream-usage.json)。业务知识查询按[共用触发](../../../docs/guides/skill-routing.md)在合适层完成，已有结果复用，不等同自动写库或建skill。
