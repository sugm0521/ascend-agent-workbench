# 来源与项目适配

上游为MIT许可的`EveryInc/compound-engineering-plugin`，通过[source lock](../../../../upstream/sources.lock.yaml)的`compound_engineering`固定到`bdc53d034ccfa5baf01b6139cd46082145ff95cc`。唯一维护源位于`deps/compound-engineering`，不安装整套插件或改写其文件。

按目的查阅：

- [ce-compound](../../../../deps/compound-engineering/skills/ce-compound/SKILL.md)：把解决且验证的问题转成值得长期保留的工程推理；已有文档不重复创建。采用其是否值得长期保留的判断，不把每次完成或改动量当作收录理由。
- [ce-compound-refresh](../../../../deps/compound-engineering/skills/ce-compound-refresh/SKILL.md)：对照当前实现复查旧知识的准确性、重叠、矛盾与被替代关系。只检查本次范围实际关联的条目。
- [MIT许可](../../../../deps/compound-engineering/LICENSE)：此处为方法参考和本项目独立适配，没有复制完整上游skill或模板。

项目适配决定如下：

| 上游行为或假设 | 本项目处理 |
|---|---|
| 解决方案默认在docs/solutions，可能维护CONCEPTS.md | 仅维护用户指定的knowledge/；不创建另一份概念库、记忆库或修改项目指令 |
| Full模式包含多角色研究与会话历史探测 | 按具体证据量决定读取范围；不为普通每日维护默认创建agent或扫描全部会话 |
| Lightweight省略语义重叠检查 | 不直接调用该快捷模式；保留本库实际语义去重、来源核验和条件检查 |
| refresh可删除知识并自动提交 | 用户明确要求历史保留：失效、合并、替代均先归档完整旧条目并记原因；Git提交由每日发布流程统一处理 |
| 从当前代码校准知识 | 保留来源事实、适用版本与独立成立的指导；实现偏离指导时记录冲突，不能自动改业务代码或宣称指导错误 |

当前源码审查确认方法适合工程经验沉淀；项目文本行为与真实本机归档检查单独记录，不把上游支持多客户端的声明当作本项目自动发现/定时执行实测。升级只按依赖流程处理，不每天自动拉最新。
