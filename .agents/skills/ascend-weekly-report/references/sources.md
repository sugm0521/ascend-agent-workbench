# 方法来源与项目取舍

以下是查证过的方法参考，不是运行依赖；不要求每次周报联网更新，不复制上游代码、完整模板或安装其工作流。本skill的指令、示例结构、渲染器与样式独立编写。

| 来源 | 固定版本与参考点 | 取舍 |
| --- | --- | --- |
| [Datawhale weekly-status](https://github.com/datawhalechina/ai-skills-for-everyone/blob/247ffdf08114c73c44c89aa56cc1eb0f65bc2271/skills/weekly-status/SKILL.md) | 247ffdf08114c73c44c89aa56cc1eb0f65bc2271；事实/不确定性与分层阅读思路 | 中文表达参考；本项目保留按日实际工作及两份不同用途报告，不采用默认字数、交互追问和模板正文。其[许可说明](https://github.com/datawhalechina/ai-skills-for-everyone/blob/247ffdf08114c73c44c89aa56cc1eb0f65bc2271/LICENSE)将原创文档列为CC BY-NC-SA 4.0、代码列为MIT。 |
| [YangsonHung git-weekly-report](https://github.com/YangsonHung/awesome-agent-skills/blob/cb9d2b21801a687d4bd8e52b2c88e8ec9c0e48af/skills/en/git-weekly-report/SKILL.md) | cb9d2b21801a687d4bd8e52b2c88e8ec9c0e48af；提交定位与不能从Git推断未来计划 | MIT；只把Git作为来源之一，实验、排障和未提交工作不能遗漏。 |
| [yy1115 weekly-report](https://github.com/yy1115/weekly-report-skill/blob/5992b16999fbccd2580c833d80bb652258fa332b/SKILL.md) | 5992b16999fbccd2580c833d80bb652258fa332b；限定项目的Codex会话补漏 | 未确认复用许可，不复制脚本。其parse_session按整段会话汇总后判断时间相交，本项目要求逐事件筛选，避免跨周混入；不采用默认宏观结论/图片优先的报告正文。 |

现有knowledge-curation负责知识证据判断，candidate-review负责优化提案筛选；周报只消费它们的职责，不新增知识库、发布流程或自动skill改写系统。周报不改变任何候选的实施授权。
