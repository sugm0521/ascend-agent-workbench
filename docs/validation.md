# 本地验证与引用边界

在实际工作台根运行：

```sh
python scripts/validate_workbench.py
```

此入口使用当前 Python（3.10+ 标准库）、已有 Git、Node.js 和 `marked`，不安装软件、不联网、不初始化依赖仓、不连接服务器或占用 NPU。它先核对文档引用，再运行 `tests/` 的全部测试（含真实 Node 渲染）及历史路径下 HCCL helper 的测试。任何必需步骤失败都返回非零；平台权限或 POSIX 语义导致的用例跳过保留在测试摘要中，不能作为该分支已实测的证据。

## 运行时与 skill 格式校验

默认从 `NODE_BINARY` 或 PATH 定位 Node，从当前进程 `NODE_PATH`/Node 模块机制定位已有 `marked`。可显式传入本机已找到的路径：

```sh
python scripts/validate_workbench.py --node /actual/node --node-modules /actual/node_modules
```

`marked` 需要提供当前渲染器使用的 `Marked`/`Renderer` 接口。路径是占位符；缺运行时或接口不兼容会报错，修复环境选择按本轮授权处理。公共脚本不硬编码客户端缓存路径，也不自动调用包管理器。

skill-creator 的 `quick_validate.py` 属于客户端提供的技能工具，不是本仓安装的 Python 包。已存在时可把其实际路径加入同一次检查：

```sh
python scripts/validate_workbench.py --node /actual/node --node-modules /actual/node_modules --skill-validator /actual/skill-creator/scripts/quick_validate.py
```

校验器及其 Python 依赖由该来源提供，证据中记录实际路径/版本或文件指纹。未提供时明确报告 skill 专用格式校验未执行；工具回归通过不等于这一项已完成。无需为校验自动安装全局 skill 或第三方库。

仅执行 `python -m unittest discover -s tests -v` 属于部分检查，未包含历史 HCCL 套件。无 Node/marked 时，直接运行根测试可能跳过渲染；统一入口则会提前报告缺口。

## 本机证据与发布引用

默认引用检查的候选文件集来自 Git 已跟踪文件及未被忽略的新文件；被忽略的本机日志即使实际存在，也不会让发布引用自动通过。检查提交快照时使用：

```sh
python scripts/validate_workbench.py --links-only --links-ref HEAD
```

`--links-ref` 只选择文档检查所用提交树；工具和测试仍来自当前工作目录。检查待发布内容时必须核对最终提交/候选文件清单，工作区未忽略的新文件不等于已提交。

持续维护文档引用未发布的 `tasks/` 或 `.workbench-local/` 原始证据时，在链接名称中明确标注 `local-only`，说明原证据时间、指纹复核时间和可访问范围，正文保留可读结论及适用边界。缺失的公开说明不能用此标记掩盖。原始大日志、个人任务进度和运行回执继续留本机，不为消除断链上传它们。

旧版已跟踪 `tasks/` 资料是历史快照，其中指向未跟踪任务产物或 `.workbench-local/` 的链接按历史本机证据单独列出，不作为跨机器可访问入口验收。引用检查分别输出未标记错误、显式 local-only、历史 local-only 和未检查的依赖仓链接。外部来源允许按用途未初始化，版本/入口可读性由 init/dependencies 的相关检查负责；此工具不证明外部链接、文内锚点或所有 Markdown 语法均有效。

本轮统一的是本地回归入口；仓内没有因此新增远端 CI 执行或 NPU 验收记录。
