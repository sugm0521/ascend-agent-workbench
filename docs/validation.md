# 干净克隆验证

所需运行时为 Python 3.10+、Git 和 Node.js 22.12+。周报渲染的 `marked` 版本由仓库的 `package.json` / `package-lock.json` 固定；不需要当前作者的客户端缓存、私有模块目录或历史实验文件。

在新克隆的工作台根运行：

```sh
npm ci --ignore-scripts
python scripts/validate_workbench.py
```

依赖安装采用所选网络环境的正常 registry/proxy/CA 配置，不关闭 TLS 验证。安装目录 `node_modules/` 不提交。统一检查覆盖根测试、真实 Node 渲染和 HCCL helper 的合成测试；不连接服务器、不占用 NPU、不安装领域子模块或启动模型。平台权限或 POSIX 语义导致的用例跳过会在摘要中列出，不能当作该分支已实测。

## 可选客户端集成

默认从 `NODE_BINARY` 或 PATH 定位 Node，使用项目安装的 `marked`。已有兼容运行时可用 `--node` 指定；`--node-modules` / `NODE_PATH` 仅用于现有环境的附加模块搜索，不是干净克隆的必需条件。

客户端提供的 skill-creator `quick_validate.py` 是可选的附加格式检查；可通过 `--skill-validator` 指向实际可用校验器，缺省会明确报告未执行。它不参与项目代码、报告渲染或根测试的必需执行路径。涉及 skill 修改时仍按相应 skill 开发规范完成适用校验，不伪造未运行的结果。

仅运行 `python -m unittest discover -s tests -v` 不包含历史路径下的 HCCL 套件。直接运行根测试时缺 Node/marked 可能跳过渲染；统一入口会提前报告依赖缺口，不以漏测代替完整通过。

## 发布引用检查

引用检查使用 Git 候选文件集，不依赖当前机器的文件存在性。已忽略文件、已删除文件或作者本机材料不能满足仓内引用。检查最终提交树：

```sh
python scripts/validate_workbench.py --links-only --links-ref HEAD
```

`--links-ref` 只选择文档来源；工具和测试仍来自当前工作目录。默认候选集包括未被忽略的新文件，发布时还须核对最终提交白名单。

本机原始资料及其路径、文件名、大小和哈希索引不进入仓库。缺失文件链接、作者本机绝对文件链接一律报错；`local-only` 标签和历史任务目录没有放行例外。原始实验可在个人环境保留，仓库正文须给出自包含的方法与结论边界，必要代码、合成回归材料必须随仓库发布。

领域依赖允许按用途未初始化，因此本检查单独列出依赖仓链接未验项；其固定来源与准备方法由 README、source lock 及 init/dependencies 管理。检查不验证外部网站、文内锚点或所有 Markdown 语法，也不把合成回归当作真实 HCCL/NPU/模型验收。
