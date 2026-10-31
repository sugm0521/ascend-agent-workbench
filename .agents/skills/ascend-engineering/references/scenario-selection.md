# 域内场景与来源选择

从本域SKILL按目标进入，只读取相关行及原资源。表中候选未承诺工具就绪；与当前后端/输入不适用时只保留方法范围，不另建运行状态。实际采用记录在upstream-usage.json，原资源路径按lock/本机配置解析。

| 场景与输入 | 本域方法/原资源定位 | 条件与边界 |
|---|---|---|
| C04 Agent/SWE等任务评测 | 本领域按实际runner及SWE记录规范组织 | 先核对runner支持，尚无统一依赖入口；awesome广泛触发描述不代表AISBench对所有agent benchmark有执行支持 |
| I01 代码/CI/PR审查 | 项目review和实际diff/workflow/check证据组织验收；AscendC专项审查交[算子领域](../../ascend-operator/SKILL.md)选择语言方法；一般工程的条件候选：[matt/code-review](../../../../deps/matt-pocock-skills/skills/engineering/code-review/SKILL.md)、[compound_engineering/ce-code-review](../../../../deps/compound-engineering/skills/ce-code-review/SKILL.md) | 按真实语言/对象核对适用性，不把AscendC方法用于一般代码；只参考本轮所需方法，不自动启用commit/push/PR文案写回 |
| I02 文档可用性审查 | msagent document-ux-review仅在明确文档体验任务时评估；定位：[msagent/document-ux-review](../../../../deps/msagent/skills/minos/document-ux-review/SKILL.md)（方法候选） | 与代码缺陷review区分；跟文档运行命令仍按本轮执行范围；不默认部署 |
| Z01 CV/训练框架迁移、RL/投机训练、K8s、驱动安装等 | 来源库存保留可发现能力，尚无本项目固定采用关系 | 用户实际目标落入该范围时，核对对应候选正文、平台、接口和副作用后选择；不因依赖已下载就自动纳入vLLM业务流程，也不无依据删除这些能力 |

方法不足时按[依赖能力发现](../../../../upstream/skill-mapping.md#依赖能力发现入口)查询已登记来源，足够即停。候选选择或上游更新影响本域时核对新增/增强/修复及旧适配，采用后同步消费声明与受影响引用。
