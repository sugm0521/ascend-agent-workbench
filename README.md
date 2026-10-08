# vLLM-Ascend Agent 工作台

`ascend-agent-workbench` 用于需求分析、问题定位、模型性能与精度、算子开发、部署、CI/PR 和工程 skill 开发。它负责组织任务和证据，按需使用已有领域 skill 与执行工具。

首版采用项目规则、七个项目级 skill、Markdown 任务记录和固定版本的领域依赖。没有自建 agent 平台、资源调度器或 GUI。

## 开始使用

在 Codex 中打开本仓库作为项目主目录。首次接入请提出：

> 使用 $ascend-workbench-init 初始化本工作台。先检查上层与各启用下层的初始化要求，汇总所有适用的必需信息后集中确认，再只补缺失项；不要重复初始化依赖中的业务仓库。

下层按用途初始化：workspace 的本机身份、工具与服务器接入分别准备，cannbot/Matt 的资料或方法引用不要求全量安装插件。现有工具与 SSH 优先复用，远程目标需实际连接并确认 NPU；源码可读、接口能启动、实际调用可用和客户端已接入分别报告。具体清单见 [init 操作约定](.agents/skills/ascend-workbench-init/references/operations.md#下层初始化清单)。

需要专用业务副本时可补充：

> 为 vLLM 和 vLLM-Ascend 在 repos/ 下独立克隆；沿用可用的 GitHub 身份，核对 fork，并按目标 vLLM-Ascend 的 CI 版本配对。

这两种接入方式会在初始化中确认。当前仓库已构建；业务 checkout、个人本机配置和运行环境尚未由本次建设初始化。

技能目录是 `.agents/skills/`，符合 [官方本地 skill 发现入口](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills)。若当前客户端没有自动发现，先明确读取对应 `SKILL.md`；发现能力和实际工具能力分别核对。项目不自动安装全局副本。

## 在另一台机器取得项目

使用有本私仓读取权限的 GitHub 身份克隆：

```bash
git clone https://github.com/sugm0521/ascend-agent-workbench.git
cd ascend-agent-workbench
git -c submodule.recurse=false submodule update --init -- deps/vllm-ascend-workspace deps/cannbot-skills deps/matt-pocock-skills
```

该命令只准备三个顶层来源仓库。不要对整个依赖树无条件执行递归初始化，否则可能另外克隆 workspace 内的业务代码。目标提交由父仓库 gitlink 和 [sources.lock.yaml](upstream/sources.lock.yaml) 固定。

## 后续任务

初始化后可以直接描述需求，例如“定位这个问题单的根因”“优化这个模型的吞吐”或“实现算子替换”。[workflow skill](.agents/skills/ascend-agent-workflow/SKILL.md) 负责查证与必要澄清，再按收益动态分工；明确的小任务无需完整采访或多个 agent。

| 入口 | 用途 |
|---|---|
| [init](.agents/skills/ascend-workbench-init/SKILL.md) | 本机接入、业务仓库/身份准备、初始化报告；按状态复用下层步骤 |
| [dependencies](.agents/skills/ascend-workbench-dependencies/SKILL.md) | 版本变化、相关传递依赖、升级与组合验证 |
| [workflow](.agents/skills/ascend-agent-workflow/SKILL.md) | 目标、事实、验收、领域路由与整体推进 |
| [planning](.agents/skills/ascend-task-planning/SKILL.md) | 依赖、子任务、写入归属与资源边界 |
| [execution](.agents/skills/ascend-task-execution/SKILL.md) | 在授权范围内调查、实验、实现与验证 |
| [review](.agents/skills/ascend-task-review/SKILL.md) | 关键结论复核、覆盖、交付与回顾 |
| [skill-development](.agents/skills/ascend-skill-development/SKILL.md) | 评估候选并建设已确认的自有 skill |
| [HCCL 打流](.agents/skills/ascend-hccl-traffic-test/SKILL.md) | 复用 MPI/CANN，验证单机或多机 alltoallvc 双模式及限时故障诊断；真实覆盖另行验收 |

定位/分析默认交付证据与建议；明确要求修复/优化/实现才推进业务修改。提交、推送和发布按本次授权处理，未授权时提供可审核结果。数值语义、支持范围和必需验收的变化由用户决定。

## 文档与记录

- [AGENTS.md](AGENTS.md)：所有会话共享的行为规则与导航。
- [项目框架](docs/项目框架.md)：架构、职责、init 去重与建设标准。
- [开发计划](docs/开发计划.md)：工作台自身待办和完成状态。
- [开发记录](docs/开发记录.md)：实际变化、验证和决定。
- [五种任务模板](docs/templates/任务说明.md)：任务说明、实验、验证矩阵、CI、交付与回顾。
- [领域映射](upstream/skill-mapping.md)：锁定版本中的真实入口和能力边界。
- [配置示例](config/workbench.example.yaml)：本机配置的参考结构，`null` 不是默认授权。
- [流程演练](tasks/2026-10-05-流程演练/任务说明.md)：明确标记的模拟场景，真实工程验收另行完成。

具体任务状态只在其 `任务说明.md` 维护。大型原始数据与本机报告放 `.workbench-local/`，本机配置放 `config/workbench.local.yaml`；均不提交。`repos/` 下业务仓库各自维护 Git 历史，父项目只记录定位和证据。

## 验证边界

首版验证涵盖 skill 格式、引用、领域入口、隔离的行为走查和模拟流程。标准初始化与真实 NPU、模型、服务、CI 验收需要实际任务与环境；来源 checkout 可读不代表远程能力已就绪。实际结果与待完成项见开发计划和开发记录。
