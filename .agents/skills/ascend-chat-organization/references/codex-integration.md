# Codex 项目级接入

## 文件归属

维护源为本 skill：脚本 [prompt_hook.py](../scripts/prompt_hook.py)、配置模板 [hooks.example.json](../assets/hooks.example.json)。模板不是实际配置，必须替换占位符。要求 Python 3 标准库，无额外包或模型调用。

实际配置写在用户选定项目的 `.codex/hooks.json`，不写用户级或系统级配置，不修改其他项目。外层项目通过目录联接发现本仓 skill 时，hook 也应登记在外层实际项目中。直接打开工作台的独立入口只有在选定该范围时才单独登记；同一会话可能加载多层配置，避免上下层重复注册。

## 增量启用

首次初始化的启用/不启用选项及未答行为统一见[初始化接入选择](../../ascend-workbench-init/references/operations.md#会话命名接入选择)。明确启用后复用以下安装步骤；旧用户只补本项，不重做初始化。不为批量整理会话自动安装 hook，也不因本机报告缺字段删除现有配置。

1. 确认实际项目、信任层、已有 `.codex/hooks.json` 和 `config.toml` 中的 hook、有效 `features.hooks` 设置，保留其他 handler 和未知字段。不改全局信任或权限来使本 hook 生效。
2. 解析模板，将 `__PYTHON_EXECUTABLE__` 替换为本机已验证可用的 Python 3，将 `__PROMPT_HOOK_SCRIPT__` 替换为本仓脚本的绝对路径。生成 JSON 时用 JSON 序列化处理引号和反斜杠；命令路径必须适配实际平台的 shell。Windows 模板用 `commandWindows` 显式调用 PowerShell，路径可用正斜杠，单引号按 PowerShell 规则转义；其他平台按其 shell 转义。不要把模板直接启用，也不要在项目非 Git 根时依赖 `git rev-parse` 猜脚本位置。
3. 若该层已有内联 hook，则沿用其格式追加一个 handler；否则向项目 `hooks.json` 的 `UserPromptSubmit` 增量合并。重复安装前按解析后的解释器和脚本路径去重；已有同脚本的不同参数先复核，不静默叠加或覆盖。写前备份原文件到忽略的本机任务目录。
4. 以 `{"hook_event_name":"UserPromptSubmit","prompt":"测试"}` 作为 stdin 运行脚本，解析 stdout JSON，确认只有短提醒，没有 prompt 回显、网络访问或状态文件。缺解释器/脚本保持未就绪，不自动安装全局依赖。
5. 由使用者在 Codex 提供的 hook 审核入口审核并信任具体定义；支持 CLI `/hooks` 时可使用该入口。不直接编辑信任记录，不使用绕过信任开关。按客户端支持方式重新加载配置，发送一条新消息，核对实际 hook 事件与标题回读。

脚本本身成功、配置已写入、hook 已信任、客户端已触发和助手已改名是不同状态，应分别记录；不能用手动运行替代客户端事件验收。未能触发时仍可按项目规则直接调用 skill。

## 停用与回退

仅移除本命名 handler，保留其他 hook 和未知字段；若本轮新建配置且没有其他内容才可移除该配置。保留 skill 与正常项目规则仍可手动命名。改名的旧标题在本机清单中保留，需要回退时通过原会话工具恢复并回读，不操作客户端内部数据库。

## 原依据与适配

- [Codex 官方 hook 文档](https://learn.chatgpt.com/docs/hooks)：项目发现、UserPromptSubmit 输入输出、信任和配置合并。运行接入时核对当前客户端支持，文档存在不证明本机生效。
- 命名方法参考目录收录的 [vllm-dev-chat-organization 固定定义](https://github.com/Henry-Avery/ascend-agent-skills/blob/0d34abd7e3b2e599d8bc5d2bbded76d732fa1e4a/skills/vllm-dev-chat-organization/SKILL.md)，原来源声明 MIT；目录审核资源及版本见 [消费声明](upstream-usage.json)。本项目加入中文约定、当前任务自动命名和项目级提醒；本 skill 可独立执行，不运行或安装该历史来源，不用当前同名来源锁冒充原作者仓库。
