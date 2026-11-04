# 域内场景与来源选择

从本域SKILL按目标进入，只读取相关行及原资源。表中候选未承诺工具就绪；与当前后端/输入不适用时只保留方法范围，不另建运行状态。实际采用记录在upstream-usage.json，原资源路径按lock/本机配置解析。

| 场景与输入 | 本域方法/原资源定位 | 条件与边界 |
|---|---|---|
| B01 运行环境与容器复现记录 | 项目runtime-snapshot；定位：[ascend-runtime-snapshot](../../ascend-runtime-snapshot/SKILL.md)（主入口） | 使用当前工具采集实际容器/进程证据；不采用awesome自带默认env_snapshot假设；不重复采集仍有效字段 |
| B02 机器、会话、代码一致性 | 按[初始化接入](../../ascend-workbench-init/references/operations.md)核对当前原provider/coordinator及真实任务绑定；代码以实际worktree/提交和产物证据核验 | 只沿实际执行工具支持的身份/目标契约；不调用已迁出的旧machine/session/code-parity入口，不建第二份身份/资源表，手工容器另走B03 |
| B03 手工已有容器独立SSH | 项目container-ssh；定位：[ascend-container-ssh](../../ascend-container-ssh/SKILL.md)（主入口） | 已有托管目标仍走原工具；与宿主登录、普通exec及资产管理分开 |
| B04 模型服务部署与PD | 项目[service-deployment](service-deployment.md)组织生命周期；单机参考[pisces/serving](../../../../deps/vllm-ascend-skills/skills/vllm-ascend-serving/SKILL.md)，PD主方法选[pd-disaggregation-serving](../../../../deps/vllm-ascend-pd-disaggregation-skills/skills/pd-disaggregation-serving/SKILL.md)；[pisces/PD](../../../../deps/vllm-ascend-skills/skills/vllm-ascend-pd-serving/SKILL.md)仅补通用背景 | 方法与执行工具分开；复用当前部署owner及原工具，不要求旧VAWS session，不并行启动第二套服务控制流程；实际请求/KV路径验收独立 |
| B05 MemCache池化部署与配置 | 明确池化目标时参考[ascend-memcache-pooling](../../../../deps/ascend-pooling-skills/skills/ascend-memcache-pooling/SKILL.md)；仍由B04维护当前服务 | 先核对模型、芯片、MemCache/连接器版本及拓扑；读取方法不授权安装/重启，指标可读不等于池化部署已验收 |

方法不足时按[依赖能力发现](../../../../upstream/skill-mapping.md#依赖能力发现入口)查询已登记来源，足够即停。候选选择或上游更新影响本域时核对新增/增强/修复及旧适配，采用后同步消费声明与受影响引用。
