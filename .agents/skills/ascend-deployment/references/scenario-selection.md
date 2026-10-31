# 域内场景与来源选择

从本域SKILL按目标进入，只读取相关行及原资源。表中候选未承诺工具就绪；与当前后端/输入不适用时只保留方法范围，不另建运行状态。实际采用记录在upstream-usage.json，原资源路径按lock/本机配置解析。

| 场景与输入 | 本域方法/原资源定位 | 条件与边界 |
|---|---|---|
| B01 运行环境与容器复现记录 | 项目runtime-snapshot；定位：[ascend-runtime-snapshot](../../ascend-runtime-snapshot/SKILL.md)（主入口） | 使用当前工具采集实际容器/进程证据；不采用awesome自带默认env_snapshot假设；不重复采集仍有效字段 |
| B02 机器、会话、代码一致性 | 使用当前实际绑定的原执行工具；workspace方法须匹配原后端；定位：[workspace/machine-management](../../../../deps/vllm-ascend-workspace/.agents/skills/machine-management/SKILL.md)（条件方法）、[workspace/session-management](../../../../deps/vllm-ascend-workspace/.agents/skills/session-management/SKILL.md)（条件方法）、[workspace/remote-code-parity](../../../../deps/vllm-ascend-workspace/.agents/skills/remote-code-parity/SKILL.md)（条件方法） | workspace machine/session/code-parity可作契约参考；awesome server-management、ascend ssh-dev-suite不是默认替换；不建第二份身份/资源表 |
| B03 手工已有容器独立SSH | 项目container-ssh；定位：[ascend-container-ssh](../../ascend-container-ssh/SKILL.md)（主入口） | 已有托管目标仍走原工具；与宿主登录、普通exec及资产管理分开 |
| B04 模型服务部署与PD | 项目workflow的service-deployment reference组织部署；实际执行依当前工具；定位：[workspace/vllm-ascend-serving](../../../../deps/vllm-ascend-workspace/.agents/skills/vllm-ascend-serving/SKILL.md)（条件方法）、[workspace/vllm-ascend-pd-serving](../../../../deps/vllm-ascend-workspace/.agents/skills/vllm-ascend-pd-serving/SKILL.md)（条件方法） | workspace serving/PD仅用于支持的session/binding路径；ascend vllm-ascend-deploy默认cron和其他inventory不整体采用 |

方法不足时按[依赖能力发现](../../../../upstream/skill-mapping.md#依赖能力发现入口)查询已登记来源，足够即停。候选选择或上游更新影响本域时核对新增/增强/修复及旧适配，采用后同步消费声明与受影响引用。
