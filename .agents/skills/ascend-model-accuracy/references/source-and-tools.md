# 来源与项目接入

本项目 skill 独立维护调用决策与适配说明，上游提供只读领域手册。这里不维护诊断正文副本、远程连接器或评测运行器。

## 来源、版本与许可

- 来源：[zhaochuang001/awesome-agent-skills](https://github.com/zhaochuang001/awesome-agent-skills)，原入口为 [vllm-ascend-accuracy](../../../../deps/awesome-agent-skills/vllm-ascend-accuracy/SKILL.md)。实际版本以 [sources.lock.yaml](../../../../upstream/sources.lock.yaml) 与父仓 gitlink 为准；初次审查基线为 `836e239f80cb76c45a5dd667839e40f336789472`。
- 原仓采用 [MIT License](../../../../deps/awesome-agent-skills/LICENSE)，copyright 为 2026 zhaochuang；原文件和许可随只读依赖保留。本 skill 的项目说明独立编写，症状路由、消融和因果验证方法参考该来源。
- 依赖未准备时按 README 仅初始化该顶层来源，不递归其他依赖；也可按固定提交读取所需原文。读取资料不要求安装上游全部 skill、Python 包、面板或服务器工具。
- 升级通过原 dependencies 流程核对实际消费的手册与行为差异；不随业务排障自动拉最新版本。

## 按阶段读取原资料

| 时机 | 原资料与消费方式 |
|---|---|
| 需要更多症状路由或消融维度 | [diagnostic-playbook](../../../../deps/awesome-agent-skills/vllm-ascend-accuracy/references/diagnostic-playbook.md)，按问题选分支，不全量铺测试 |
| 已缩小致因并获授权修复 | [remediation-playbook](../../../../deps/awesome-agent-skills/vllm-ascend-accuracy/references/remediation-playbook.md)，核对目标版本与最小修复层级 |
| 需要核对远程取证字段 | [remote-container-workflow](../../../../deps/awesome-agent-skills/vllm-ascend-accuracy/references/remote-container-workflow.md)，只参考证据字段；目标、认证与启动路径先查现有记录/工具，不照搬首轮问卷或默认修改权限 |
| 需要组织交付内容 | [final-report-template](../../../../deps/awesome-agent-skills/vllm-ascend-accuracy/references/final-report-template.md)，内容写当前任务记录，按定位/修复模式报告实际结果；不强制 cwd 再生成一份报告 |
| 用户明确要求准备公开 issue/缺陷单 | [issue-report](../../../../deps/awesome-agent-skills/vllm-ascend-accuracy/references/issue-report.md)，先脱敏并提供审核稿，实际发布沿用具体授权 |

## 专题补充资料

已有手册足够时不再加载同方向的完整skill。只有当前证据存在以下缺口时，按[场景选用表](../../../../upstream/skill-mapping.md#按任务选用与重叠处理)读取具体资源；仍在同一精度任务组织结论和回归。

| 当前证据与缺口 | 消费资源 | 判断与停止条件 |
|---|---|---|
| 症状和触发配置可能匹配已知案例 | msagent [precision-debugger案例汇总](../../../../deps/msagent/skills/accuracy/precision-debugger/references/summary.md) | 只作根因候选，核对目标版本源码、配置与复现；不按案例相似度直接认定已定位，不整体加载其问卷、修改日志或修复循环 |
| 首个差异已指向KVCache/FlashAttention、Prefill/Decode映射 | cannbot [model-infer-precision-debug](../../../../deps/cannbot-skills/model/model-infer-precision-debug/SKILL.md)的相关分支 | 核对目标实现的metadata、packed sequence和cache协议，不把其框架假设强加给所有模型；已有证据可排除分支就停止 |

上述来源按lock固定并保持只读；msagent的[MulanPSL-2.0](../../../../deps/msagent/LICENSE)与cannbot的[原许可](../../../../deps/cannbot-skills/LICENSE)随源保留。本项目只引用方法/案例，未复制正文；候选工具与当前后端兼容性仍需实际核对。

## 工具使用与版本相关适配

满足当前任务输入、运行前提与授权时可直接按上游流程使用原脚本/工具，不要求先写一份项目替代实现。以下工具限制是当前固定版本的审查事实，不是永久禁用；版本以lock为准。上游相关文件改变时，按[依赖维护](../../ascend-workbench-dependencies/references/dependency-check.md#能力发现入口维护)复验原问题，并更新实际消费方式。

- 环境信息使用项目 runtime-snapshot 与已有执行工具。原 `env_snapshot.py` 不作为本项目默认采集器：当前审查版本包含个人库路径、按空格拆 Docker 配置、按最高 Python 版本探测等假设，不能据此认定服务实际解释器和 worker 库来源。
- 输出证据优先使用现有 AISBench 证据报告，比较与验收使用 correctness-validation。原 `analyze_generations.py` 仅为字符/复读初筛参考；其 exact_match 会计入两个空答案，重复 ID 会覆盖，不能代替可比性、完整性或精度判定。
- 流式 delta、原始字节、token/logits 等超出既有工具契约的证据，按实际问题用原工具采集并保留引用，不伪造已有字段或修改上游结果。字符重复只是候选，逻辑错误和业务精度需要独立证据。
- 不引入原仓 server-management、npu-migrate、disk-cleanup 的 inventory、迁移或自动清理路径。资源/身份沿用当前工具；缺少绑定或环境只暂停相应运行，源码分析与已有证据审查继续。
- 原 skill 默认可修改测试容器、候选必须继续修复及独立报告位置等约定，由本项目具体授权、任务状态和交付规则决定。项目“只定位”不扩大为修复；验证所需的服务变更也先核对已有授权。

升级复核至少针对变化涉及的原缺陷：env_snapshot的配置分词、解释器和实际worker库来源；analyze_generations的空答案、重复ID及结果分母。修复经代表输入验证后，可以重新使用相应原工具并撤掉已被覆盖的本地替代/例外；没有验证或仍有缺陷的部分保留。正确性验收、原始证据、授权和任务记录属于项目要求，不因某个脚本修复而一起移除。
