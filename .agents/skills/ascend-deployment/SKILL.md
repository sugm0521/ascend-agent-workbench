---
name: ascend-deployment
description: 统筹Ascend模型服务单机/PD部署、容器SSH、环境检查和运行复现记录，按实际provider及已有授权组织原工具。用于部署/运行环境目标；普通性能或精度任务不自动重新部署。
metadata:
  workbench_role: domain_entry
  workbench_domain: deployment
---

# 部署与运行环境领域

遵循[根规则](../../../AGENTS.md)和[分层协作](../../../docs/guides/skill-routing.md)。可直接启动，复用已定目标、环境/身份和知识查询；针对部署方式、框架/CANN、容器/动态库、网络和启动首错检索相关经验。

| 目标 | 选择与边界 |
|---|---|
| 新服务/单机或PD部署 | [部署流程](references/service-deployment.md)：先核对版本、拓扑、原运行工具和启动材料；服务启动与真实请求分别验收 |
| 已有手工容器独立SSH | [container-ssh](../ascend-container-ssh/SKILL.md)：只补本次SSH入口；托管目标按原契约交接 |
| 容器最小复现、原镜像/PR/替换依赖 | [runtime-snapshot](../ascend-runtime-snapshot/SKILL.md)：复用统一记录，单项版本问答不全采 |
| 加载/环境/网络异常 | 从实际进程、挂载和库来源定位，按证据有界展开；不默认新容器或安装整套环境 |

来源与前提见[域内选用](references/scenario-selection.md)和[消费声明](references/upstream-usage.json)。workspace serving/PD仅在原session/后端契约满足时调用；当前MindIE与手工Docker沿用实际工具，不能传错绑定、伪造lease或另建资源系统。

部署前复用有效版本/环境证据，缺项有界补齐；授权、资源占用和副作用沿原规则。记录完整实际启动材料；已启动/端口占用/API列表正常不代替目标请求或PD路径。需要压测或精度回归交对应领域，不静默停止/修改用户要求保留的服务。

本域方法不足时按发现协议查已登记来源，核对真实输入和运行前提。交付实际服务/环境、来源/变更、请求证据、未完成项及资源归属，不把历史配置视作当前状态。
