# 文档导航

首次使用见[项目首页](../README.md#快速开始)，选择能力见[skill 功能索引](../README.md#按任务选择入口)。反馈与参与修改见[贡献说明](../CONTRIBUTING.md)。本文按用途组织文档，不重复维护执行规则、工具参数或任务状态。

## 按目标阅读

| 当前目标 | 阅读入口 |
|---|---|
| 开始任务、选择领域或直接使用能力 | [上手与初始化](../README.md#快速开始) → [skill 使用说明索引](../README.md#按任务选择入口)；启动与交接规则见[分层协作](guides/skill-routing.md) |
| 调用工具、保存输入与结果 | 下方[工具说明](#工具使用说明) → [任务材料规范](guides/task-records.md)；工具前提仍由实际执行入口核对 |
| 查找上游能力、检查更新并吸收改进 | [来源发现](../upstream/skill-mapping.md#依赖能力发现入口) → [消费与升级约定](maintenance/upstream-consumption.md) → [只读检查工具](maintenance/upstream-consumption.md#只读检查辅助工具)；维护流程见[工作台维护领域](../.agents/skills/ascend-workbench-maintenance/README.md) |
| 改进或新建自有 skill | [贡献流程](../CONTRIBUTING.md#如何提交修改) → [候选评估](../.agents/skills/ascend-skill-candidate-review/README.md)或[已授权开发](../.agents/skills/ascend-skill-development/README.md) → [适用验证](maintenance/validation.md) |

配置字段见[配置示例](../config/workbench.example.yaml)及[配置约定](../.agents/skills/ascend-workbench-init/references/config-schema.md)；知识库接入和运行时检索见[知识协议](../knowledge/README.md)与[知识触发规则](guides/skill-routing.md#知识在业务运行中的触发)。来源版本和许可分别见[来源锁](../upstream/sources.lock.yaml)与[来源许可](../upstream/来源与许可.md)。

| 目录 | 内容 | 什么时候读 |
|---|---|---|
| [guides](#使用与执行规范) | 现行使用与执行规范 | 准备业务推送、保存任务材料或进行归档维护时 |
| [tools](#工具使用说明) | 公共脚本的输入、调用和输出边界 | 任务实际需要对应工具时 |
| [maintenance](#项目建设与维护) | 架构、开发计划、变更记录与工作台自测 | 维护工作台时 |
| [templates](#记录模板) | 通用任务记录与本机台账模板 | 按任务需要创建记录时 |

## 使用与执行规范

| 文档 | 用途 |
|---|---|
| [无服务器入门案例](guides/first-task/README.md) | 分析 vLLM-Ascend 合成启动参数与 KV Cache 容量冲突，无需运行环境 |
| [分层协作与直接启动](guides/skill-routing.md) | 主入口、领域、具体能力的职责，知识触发及上游补位 |
| [业务仓 CI 预检](guides/business-ci-preflight.md) | 推送前的静态检查、相关 CPU 用例、PR 标题只读检查、环境隔离及失败处理 |
| [任务材料与台账](guides/task-records.md) | 任务目录、编号、启动材料、日志和本机台账的共用约定 |
| [本机归档、知识维护与授权发布](guides/daily-sync.md) | 归档与两类发布的范围、授权和回执边界 |

## 工具使用说明

| 文档 | 用途 |
|---|---|
| [AISBench 证据报告](tools/aisbench-evidence.md) | 离线汇总已有评测结果、请求证据及按需输出审计 |
| [部署声明与只读预检](tools/deployment-preflight.md) | 从声明检查部署前提、生成参数并核对实际容器 |
| [已有 GPQA 客户端的多组执行](tools/gpqa-batch.md) | 复用指定客户端材料，准备、监督及收集多组运行 |
| [原生运行探针与产物核对](tools/runtime-tools.md) | 原生导入的进程退出检查及文件、wheel 一致性核对 |
| [上游来源只读检查](maintenance/upstream-consumption.md#只读检查辅助工具) | 读取固定版本与实际消费关系，收集候选变化和待复核项；前提、参数和退出状态由该章节维护 |

## 项目建设与维护

| 文档 | 用途 |
|---|---|
| [项目框架](maintenance/项目框架.md) | 项目架构、职责、流程与建设标准 |
| [当前开发事项](maintenance/开发计划.md#当前待办与待验收) | 工作台建设待办、完成条件与状态；追溯决定时再读关联历史 |
| [开发记录](maintenance/开发记录.md) | 实际变更、决定和当时的验证范围 |
| [上游消费与更新](maintenance/upstream-consumption.md) | 实际消费声明、历史依据、影响评估、吸收与采用/清理 |
| [工作台验证说明](maintenance/validation.md) | 干净克隆自测、发布引用、跨机器复用和可选 Git 推送大小策略 |

## 记录模板

只在需要时复制模板，按[任务材料规范](guides/task-records.md)放入实际位置并调整相对链接。具体任务、测试结果和服务器信息留在本机，不填回公开模板。

| 模板 | 用途 |
|---|---|
| [任务说明](templates/任务说明.md) | 任务当前状态、授权、计划与材料入口 |
| [实验记录](templates/实验记录.md) | 假设、改动、对照与结果 |
| [验证矩阵](templates/验证矩阵.md) | 覆盖、标准、结果及缺口 |
| [CI 记录](templates/CI记录.md) | 推送前预检、CI 问题、修复、审核与复验 |
| [交付与回顾](templates/交付与回顾.md) | 交付证据、交接快照和回顾 |
| [容器总表](templates/容器总表.md) | 本机容器及环境版本记录 |
| [服务器总表](templates/服务器总表.md) | 已核验宿主及关联容器入口快照 |
| [性能测试总表](templates/性能测试总表.md) | 正式性能运行 |
| [精度测试总表](templates/精度测试总表.md) | 正式精度评测 |
| [SWE 测试总表](templates/SWE测试总表.md) | 软件工程数据集上的正式 agent 评测 |
| [AISBench 旧总表](templates/AISBench测试总表.md) | 历史兼容入口；新增正式运行使用上述三类测试表 |

新增、移动或删除文档时，同步本文和受影响的引用。评估过程留当前本机任务；已确认的工作台/skill改进和实际修改分别维护在开发计划、开发记录，工程经验按私有知识流程吸收，不建立公开评估目录或知识建设待办。导航只概述用途。
