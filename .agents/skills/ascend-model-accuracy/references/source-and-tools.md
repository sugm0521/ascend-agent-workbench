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

## 工具与状态复用

- 环境信息使用项目 runtime-snapshot 与已有执行工具。原 `env_snapshot.py` 不作为本项目默认采集器：当前审查版本包含个人库路径、按空格拆 Docker 配置、按最高 Python 版本探测等假设，不能据此认定服务实际解释器和 worker 库来源。
- 输出证据优先使用现有 AISBench 证据报告，比较与验收使用 correctness-validation。原 `analyze_generations.py` 仅为字符/复读初筛参考；其 exact_match 会计入两个空答案，重复 ID 会覆盖，不能代替可比性、完整性或精度判定。
- 流式 delta、原始字节、token/logits 等超出既有工具契约的证据，按实际问题用原工具采集并保留引用，不伪造已有字段或修改上游结果。字符重复只是候选，逻辑错误和业务精度需要独立证据。
- 不引入原仓 server-management、npu-migrate、disk-cleanup 的 inventory、迁移或自动清理路径。资源/身份沿用当前工具；缺少绑定或环境只暂停相应运行，源码分析与已有证据审查继续。
- 原 skill 默认可修改测试容器、候选必须继续修复及独立报告位置等约定，由本项目具体授权、任务状态和交付规则决定。项目“只定位”不扩大为修复；验证所需的服务变更也先核对已有授权。
