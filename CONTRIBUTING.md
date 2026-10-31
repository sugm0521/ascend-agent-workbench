# 反馈与贡献

使用中遇到问题，可提交[问题反馈](https://github.com/sugm0521/ascend-agent-workbench/issues/new?template=bug_report.yml)；有流程或功能建议，可提交[改进建议](https://github.com/sugm0521/ascend-agent-workbench/issues/new?template=feature_request.yml)。也可从仓库 Issues → New issue 选择表单。提交前先查看[已有讨论](https://github.com/sugm0521/ascend-agent-workbench/issues)，重复问题优先补充原 Issue。

## 如何反馈

问题反馈只要求说明目标、最小操作步骤或调用请求、预期与实际差异。skill 名称、工作台提交号、客户端和操作系统均可选填；提交号可在工作台根运行 `git rev-parse --short HEAD` 获取，不清楚可填“未知”。依赖版本仅在影响问题时提供，无需先完成接入审计。

改进建议说明实际场景、当前困难和期望结果即可，实现方案选填。欢迎提出难用的地方，不要求先研究项目架构或证明问题重复发生。

优先提供最小、合成或脱敏材料，以及错误附近的必要片段。不要上传 token、密钥、私有配置、内部连接清单、私有仓库内容、完整初始化报告或全部会话/运行日志；请求、截图和文件附件也应检查。无法公开材料时可先描述现象及缺少的条件，本项目不要求另找私下渠道发送原件。提交反馈不授予连接服务器、修改代码或执行实验的权限。

## 由agent协助反馈

可以请求[工作台维护域](.agents/skills/ascend-workbench-maintenance/README.md)整理skill使用问题或验证反馈，例如“整理这次问题的本仓Issue草稿，先给我审核，不对外提交”。细节由[反馈流程](.agents/skills/ascend-workbench-maintenance/references/skill-feedback.md)维护，复用下方现有贡献与表单入口。

初始化会提供是否参加项目改进的可选项；未选择/不参加时不主动邀请，手动反馈始终可用，调整方式见[参与偏好](.agents/skills/ascend-workbench-init/references/config-schema.md#项目改进参与偏好)。同意参加仅允许有价值时邀请，不是采集或发布许可。

第一版只代投本工作台维护仓，先查重；上游问题保留公开来源、实际版本与适配关系，由维护者判断转交。Issue可如实说明缺资料、未复现或未知根因；PR另需具体修改授权、最小diff和适用验证。

每次公开发布前，agent必须提供收集清单及本机原件审阅入口、完整拟公开正文/附件或diff、验证范围及准确目标，等你审核后对当次最终版本明确同意；任何旧批准不能代替。材料或目标变化须重新审核，未答复保持本机待审。上传远端分支、创建草稿PR以及后续评论/附件/修改同样适用，不先上传再补审核。

## 反馈如何处理

维护者先核对目标、已有覆盖与可复现条件，信息不足时只补问影响判断的缺项。区分用法问题、文档缺口、skill 行为、工具缺陷和上游业务问题；无法复现时说明缺失条件，不把业务报错自动归为工作台缺陷。若工作台遗漏关键材料、错误归因或越过授权边界，也可独立反馈。

涉及 skill 改进时，使用[候选评估流程](.agents/skills/ascend-skill-candidate-review/SKILL.md)判断最小范围，再按[开发流程](.agents/skills/ascend-skill-development/SKILL.md)实施已确认的修改。仅明确决定实施的工作台建设进入开发计划；Issue 不自动成为开发承诺、知识收录或发布授权。不会因反馈自动运行环境、实验或新增服务。

## 如何提交修改

小型错字、失效链接等修正可以直接提 PR；新增能力、改变流程或操作边界，建议先开 Issue 明确问题和范围，避免重复实现。Fork 后在自己的分支准备修改，保留来源和许可，不直接改写 `deps/` 外部维护源。

| 修改类型 | 需要关注的验证与同步 |
|---|---|
| 文档 | 检查实际内容、受影响引用及示例；适用时使用[文档与发布检查](docs/maintenance/validation.md) |
| skill | 遵循[开发规范](.agents/skills/ascend-skill-development/SKILL.md)，核对入口、适用/不适用请求、旧规则清理及受影响说明 |
| 工具或代码 | 按改变的输入输出和失败分支运行相关测试，具体自测入口见[验证说明](docs/maintenance/validation.md)；不为低影响修改重跑无关全套测试 |

项目目录和公共/本机内容边界以 [AGENTS.md](AGENTS.md#2-目录职责与事实源) 为准。不要提交本机配置、`tasks/`、`records/`、私有知识或原始实验资料；公共内容应能在没有作者本机材料的环境中理解和使用。

PR 说明写清解决什么问题、行为如何变化、实际验证及尚未验证的部分，可关联已有 Issue。源码/本地/模拟检查与真实远程或 NPU 验收分别表述，不要求所有贡献运行 NPU 或全部测试。

使用贡献者本人有效的 Git 作者身份，并为每个提交添加匹配的 DCO 签署，例如 `git commit -s`；不要复制维护者姓名或邮箱。参考 [Developer Certificate of Origin](https://developercertificate.org/)。提交前审查 diff 和提交范围，避免混入无关工作。

返回[项目首页](README.md)。

领域/具体能力的职责与三种启动按[分层协作](docs/guides/skill-routing.md)维护；实际借用原skill/脚本/方法时更新[消费声明](docs/maintenance/upstream-consumption.md)，候选和普通导航不冒充运行依赖。迁移同时更新调用方、当前接入与索引，删除旧位置兼容；不用作者私有材料作为公开必需输入。
