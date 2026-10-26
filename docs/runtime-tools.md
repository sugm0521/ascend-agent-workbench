# 原生运行探针与产物核对

两个工具均为 Python 3.10+ 标准库脚本，独立 CLI，无模型、芯片、主机或路径默认值。执行路径从实际工作台根解析；不要将本文示例占位路径原样用于业务环境。远程时通过已经接入的原执行工具在目标环境运行，不新增 SSH 凭据、session 或资源状态。

## 选择范围

| 本次问题 | 工具与动作 | 能证明什么 | 不能证明什么 |
| --- | --- | --- | --- |
| wheel/源码/原生库/缓存搬迁后核对 | `artifact_manifest.py snapshot` + `compare` | 声明覆盖内的版本、字节、文件类型一致性 | ABI、模型精度、服务与 PD 可用性 |
| 核对 wheel 实際覆盖的已安装文件 | `artifact_manifest.py verify-wheel` | wheel 成员映射到指定安装目录后的字节一致性 | pip 是否成功、额外文件、导入实际生效与运行兼容 |
| 原生扩展导入、析构或兼容性问题 | `native_import_probe.py` | 指定解释器下用例主体完成且进程正常退出 | 根因、目标模型/NPU路径正确、所有退出顺序兼容 |
| 普通源码学习、无原生依赖的编辑 | 不默认运行这两个工具 | 按原任务标准验收 | 不因存在工具增加依赖检查 |

从文件核对开始的任务不会自动导入业务包。原生探针仅在相关问题需要且运行环境已经获得授权时启用。导入某些模块本身可能初始化设备或触发库行为，探针不是无副作用沙箱。纯产物核对不需要启动模型；PD 验证只在任务范围包含 PD 时执行。

## 原生导入探针

[脚本](../scripts/native_import_probe.py) 对每个用例开启独立子进程，默认使用调用它的 Python；跨环境时显式指定 `--python`。正常退出 0 且捕获到工具的完成元数据才为 `passed`；主体完成但非零退出仍失败；直接 `os._exit(0)` 等绕过完成记录为 `inconclusive`。

### 配置与调用

配置 JSON 示例（保存为你指定的文件）：

```json
{
  "cases": [
    {"name": "stdlib", "imports": ["ssl", "hashlib"], "timeout_seconds": 30},
    {"name": "dependent", "imports": ["your_extension"], "code": "import your_extension; assert your_extension is not None", "timeout_seconds": 60}
  ]
}
```

第二个示例中的模块和检查须替换为当前任务实际用例。`code` 在单独命名空间执行，import 列表中的模块不会自动绑定为代码变量；代码需要的名字显式 import。`code` 是可信任的 Python 代码，会直接执行，不接受来源不明的配置。

```bash
python scripts/native_import_probe.py --config /path/probes.json --output-dir /path/new-probe-run
```

用例字段：唯一安全 `name`、`imports`（模块名列表）、可选 `code`、可选 `env`（键为变量名，值为字符串；null 表示取消继承）、可选正数 `timeout_seconds`（默认 60）。继承调用者环境，但环境覆盖仅作用于子进程；报告只保存覆盖的变量名，不记录其值。不要在 code 中硬编码凭据，也不要让被测代码输出凭据。

输出：`report.json`、每用例的 stdout/stderr 日志。默认每个流只保留最后 32768 字节，报告记录观测总字节数和截断。截断证据不能用来证明完整日志中没有异常。Linux 子进程记录 `/proc/self/maps` 中最多 128 个已加载 `.so` 路径；其他平台标明 unavailable。模块路径来自实际 import，版本和解释器来自子进程。

状态包括 `passed`、`exit_failure`、`signal`（仅 POSIX）、`timeout`、`launch_error`、`inconclusive`。检查最终报告的整体状态和每个用例；运行中检查点带 `running`，不能作最终结果。退出码：0 全部通过；1 已完成探测但存在失败/无定论；2 配置、输出或运行控制错误。现有输出目录拒绝覆盖，重复运行选新目录以保留原失败。

超时在 POSIX 中终止本探针创建的进程组；Windows 在直接子进程仍存在时使用其 PID 定向结束进程树。子进程自行脱离进程组或在 Windows 先退出后留下后代时，不能保证清理所有后代；不要把该探针用作服务启动器。管道未结束时结果不会通过。不停止任何既有服务。

## 产物清单

[脚本](../scripts/artifact_manifest.py) 提供三种只读动作：

```bash
python scripts/artifact_manifest.py snapshot --root source=/path/source --root cache=/path/cache --wheel extension=/path/extension.whl --distribution package-name --exclude '**/__pycache__/*' --output /path/reports/baseline.json
python scripts/artifact_manifest.py snapshot --root source=/other/source --root cache=/other/cache --wheel extension=/other/extension.whl --distribution package-name --exclude '**/__pycache__/*' --output /path/reports/candidate.json
python scripts/artifact_manifest.py compare --expected /path/reports/baseline.json --actual /path/reports/candidate.json --output /path/reports/comparison.json
```

跨主机保持相同逻辑 label 和过滤条件；实际根目录可以不同。清单输出放在被核对目录之外，避免后续把报告本身纳入清单。所有输出文件拒绝覆盖；每次新建报告文件。工具不安装、打包、提取、恢复或清理产物。

`snapshot` 至少指定一项 `--root LABEL=PATH`、`--wheel LABEL=PATH` 或 `--distribution NAME`，可重复指定。树按原始字节流式 SHA-256，包含目录和文件类型；符号链接记录目标字符串，不跟随链接核对目标内容。需要检查链接目标时另显式提供目标根。不会将二进制中的 CRLF 替换为 LF。`--exclude` 为相对 POSIX 路径 glob，仅作用于树；过滤条件参与比较。

文件读取时发现大小、修改时间或 inode 变化会记录错误；清单不是原子文件系统快照，运行中的源码或缓存仍可能变化。使用已稳定的目录或原工具支持的快照，不能据此冻结正在编译的服务。

`--distribution` 从当前解释器的安装元数据记录版本、安装根、文件及可用的顶层模块位置，不 import 目标包。模块位置查找仅使用标准 PathFinder，不覆盖任意自定义导入 hook；editable source 或缺少文件清单时需要另指定源码根，不能把 `.pth` 一致当作源码一致。要确认实际导入位置，使用原生探针的实际模块路径。不会保存可能包含凭据的 direct_url 原文。

`compare` 默认核对内容、类型、链接目标、包版本及 wheel 原始归档哈希；绝对目录、采集时间和解释器信息只作证据，不默认要求跨机相同。`--check-modes` 适用于需核对 POSIX 文件权限的场景；`--check-origins` 适用于预期安装位置必须相同的场景。缺失、额外、不同及不完整清单分别记录；任一采集失败时比较为 `inconclusive`，不能返回 matched。

### wheel 安装路径核对

```bash
python scripts/artifact_manifest.py verify-wheel --wheel /path/package.whl --site-root /path/site-packages --output /path/reports/wheel-check.json
```

普通成员映射到 site-root；`*.data/purelib` 和 `*.data/platlib` 映射到各安装根（默认同 site-root）。额外 scheme 通过 `--scheme scripts=/path/bin`、`--scheme data=/path/prefix`、`--scheme headers=/path/include` 或 purelib/platlib 覆盖指定。缺失 scheme 不跳过，标记无定论。

不解包归档；拒绝绝对路径、路径穿越、重复成员及 wheel 符号链接；已安装路径解析后不能逃出所选根。安装器会改写的 `.dist-info/RECORD` 及签名明确列为 excluded，其他成员逐字节比较。脚本头部重写、后处理原生库等安装修改可能合理，但本工具仍报告字节差异，由任务解释，不把差异直接当作 pip 或算子故障。

排除后没有可核对成员时（例如只有 `RECORD` 或其签名），报告 `checked_files=0`、明确错误及 `inconclusive`，退出 1。该工具不验证完整 wheel 打包规范；`matched` 仅说明至少一个非排除成员在所选安装路径的字节匹配，不证明 wheel 结构完整或安装成功。

清单状态 complete/incomplete；比较和 wheel 核对状态 matched/different/inconclusive。退出码：0 完整采集或一致；1 采集不完整、存在差异或无定论；2 配置、schema、读取或输出错误。大型清单留在服务器侧，单次上传另检查文件字节数，不自动上传。

## 验证与来源

```bash
python -m unittest discover -s tests -p 'test_runtime_tools.py' -v
```

测试使用真实本地子进程、临时目录、生成的 wheel，不占 NPU。Linux 信号/进程组及 `.so` 映射需在 Linux 执行对应测试；Windows 测试通过不能代替目标原生库、服务或模型验收。

方法来自历史工程中的导入矩阵、运行文件核对和 wheel 映射；原业务运行回执留各自本机，历史观察不能由公共回归独立复验。公共代码重新实现，仅保留退出状态与显式覆盖方法，未复制固定主机/路径或第三方源码；没有新增第三方运行依赖。
