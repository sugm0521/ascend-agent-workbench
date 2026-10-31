---
name: ascend-repository-update
description: 安全同步代码仓并分流版本升级，核对实际仓库、分支、远端、未提交修改及目标版本，保留现有工作。用于更新代码仓、拉取远端变更、同步业务分支或更新工作台；固定依赖升级交给 dependencies，首次接入交给 init。
metadata:
  workbench_role: capability
  workbench_domain: maintenance
---

# 代码仓更新

## 领域与直接启动

所属[工作台维护领域](../ascend-workbench-maintenance/SKILL.md)。直接启动时复用当前任务，按[分层协作与知识触发](../../../docs/guides/skill-routing.md)完成或复用定向检索，并核对领域适用/补位规则；已有上下文不完整回跑主入口。覆盖不足交所属领域，原方法和工具的授权/验证范围仍适用。


遵循[项目规则](../../../AGENTS.md)。本入口负责确定更新对象、目标和保留工作的方法；不会因“更新仓库”自动更新所有仓、切回 main 或升级运行环境。

## 确定对象与目标

1. 从本次任务、本机绑定及实际 Git 查询确认 repo/worktree 的绝对根目录，明确业务仓、工作台或固定依赖。按真实 Git 根去重，未初始化子模块回落父仓不能算独立仓。查询指定实际 repo，不使用当前目录猜归属。
2. 只读核对 HEAD、branch/detached、tracking、remotes、已暂存/未暂存/未跟踪文件，以及相关任务是否正在使用该代码。远端 URL 回传时去掉凭据；本地 ahead/behind 注明远端引用的新鲜度。查询状态或检查更新本身不授权 fetch、切分支或合入。
3. 沿用已确认的目标 remote/ref 或版本。用户要求实际更新且现有 tracking 含义明确时可继续；来源、目标或 dirty 处理会影响现有工作且无法查明时，给出具体差异与选项再确认，不默认 origin/main、最新版本或一组未经核实的双仓 SHA。

## 分流

| 对象 | 路径 |
|---|---|
| 业务仓同步 | 下述安全同步；vLLM/vLLM-Ascend 还需核对目标 vLLM-Ascend 的 CI 声明及真实配对 SHA，复用 [init 的配对方法](../ascend-workbench-init/references/operations.md#业务代码与-ci-配对)，不运行完整初始化 |
| 工作台自身更新 | 同样保留本仓 dirty/staged，按目标安全同步；若来源声明/gitlink 变化，再将受影响范围交给 [dependencies](../ascend-workbench-dependencies/SKILL.md)，不直接更新全部子模块 |
| deps 固定来源或相关工具升级 | 交 [dependencies](../ascend-workbench-dependencies/SKILL.md)解析目标父声明、传递约束、兼容验证和回退；不在本入口维护第二套 pin，不改外部维护源 |
| 首次 clone、身份/remotes 缺失 | 仅把真实缺失项交 [init](../ascend-workbench-init/SKILL.md)，已可用部分直接复用 |

## 安全同步与交付

- 用户已要求实际更新时，定向 fetch 已确认来源，记录更新前与目标 SHA 并检查差异、祖先关系及子模块/配置变化。fetch 不等于已经合入；网络失败保留原状并报告，不换到未经确认的镜像或账号。
- 默认只做可快进同步（如针对已核实目标的 `merge --ff-only`）。dirty、已有暂存或活动实验需要先确定不会覆盖/混入旧工作的方法：保留可恢复备份，或在隔离 checkout 准备候选；必要时请用户选择。不能为凑干净状态自动整仓 stash、commit、reset、clean、强推或覆盖文件，也不移动仍被实验使用的分支。
- 分支分叉、detached 或目标无法快进时停止该仓合入，保留原分支/修改并说明差异；显式选择 merge/rebase/cherry-pick 后才按范围执行。冲突只展示解决 diff，不整篇输出文件；提交、DCO、推送及 PR 信息遵循根规则，更新请求不自动授权发布。
- 版本组合按任务验收。同步源码不代表需要重装环境、重启服务或重新测试全项目；先核对实际受影响入口，只执行已授权且必要的检查，真实运行缺口单列。尚未满足配对或验证要求时交付候选，不能报告环境已升级完成。
- 最后记录各仓更新前后 branch/SHA、目标与来源、实际操作、dirty/staged 保留情况、配对约束、验证和未完成项。失败或回退需要恢复时只处理本轮拥有的变更，不能顺带撤销他人的工作。
