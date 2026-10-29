# 工作与项目改进周报

`ascend-weekly-report` 的使用说明，面向提出任务的使用者；详细执行规则以 [SKILL.md](SKILL.md) 为准。

## 能做什么

从指定周期内的任务、产物和变更证据生成个人工作、项目与知识库改进两份周报，并提供Markdown和HTML展示。

## 什么时候用

明确要求周报或周期回顾时使用；知识条目维护、业务验收和调度配置分别使用对应入口。

相邻入口：[ascend-knowledge-curation](../ascend-knowledge-curation/README.md)、[ascend-task-review](../ascend-task-review/README.md)。

## 怎么调用

- 使用 $ascend-weekly-report，整理我指定周期的两份周报，区分实际完成、失败和待验证内容，生成HTML阅读版。
- 使用 $ascend-weekly-report，根据已有任务证据更新本周期周报，只写本机产物，不发布、不安排定时任务。

## 需要提供什么

周期与时区、项目/任务范围、已有周报及输出位置偏好；缺失项按实际上下文核对。

agent 会先查：任务记录、实际文件与Git变化，以及知识改进证据；不编造收益、负责人或下周承诺。

## 会产出什么

work-weekly.md、project-knowledge-weekly.md及由两份Markdown渲染的index.html；说明证据与缺口。

## 操作边界

周报产物留本机，不自动上传、发布、写知识或创建调度。只读知识，改进建议不直接应用；报告中的静态、模拟与真实运行证据分开。

返回[项目功能索引](../../../README.md)。提交、推送和发布统一遵循[项目规则](../../../AGENTS.md)及本轮具体授权。
