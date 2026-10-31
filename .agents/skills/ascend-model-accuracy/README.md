# 模型精度领域

统筹乱码/复读/空输出、数值差异、模型数据集评分与回归。可直接指定，也可由主workflow交接，复用同一任务和[知识查询规则](../../../docs/guides/skill-routing.md)。

例如“定位模型输出复读”或“核对这次数据集评测的原生分数”。输入为现象/数据集、基线、版本、采样/评分器、证据及授权；输出为偏差、根因/规避边界、正式指标或验证缺口。定位不自动改业务代码，工具成功不等于精度通过。

完整方法和材料边界见[SKILL](SKILL.md)，诊断/修复分支见[症状诊断](references/diagnosis.md)，选用与原资源见[域内专题](references/scenario-selection.md)及[消费声明](references/upstream-usage.json)。模型评分与性能负载/SWE runner分别组织。
