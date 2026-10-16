# 部署声明与只读预检

用于新建/重建容器、相关挂载或通信方式改变时的确定性检查。通过原有执行工具在**每个目标宿主机**运行 [deployment_preflight.py](../scripts/deployment_preflight.py)，只需 Python 3.10+ 标准库。它不连接远程、不创建/启动/停止容器、不分配设备，不替代现有 serving 或资源工具。普通状态查询不运行整套预检。

## 先选通信方式

先根据本次硬件、拓扑和实际代码/CANN/连接器版本确定通信方式，再准备对应资源。文件缺失不授权切换通信方案或从另一台复制设备端点。

- `static`：使用当前进程会使用的**宿主物理 NPU ID**，检查其 `ub_endpoint_npu_<id>.json` 是非空 JSON 对象；声明宿主端点目录及其到 `ascend_local_comm_res_path` 的 bind mount。不能把逻辑 rank 当物理 ID，也不能仅凭目录存在通过。
- `auto`：只有当前实现支持该自动资源方式时选用。显式声明本版本支持的 `ASCEND_LOCAL_COMM_RES` 版本配置、所需设备/路径及工具；移除连接器里的静态路径，清除冲突的旧全局协议配置。无关的空端点目录不成为必需项。脚本覆盖仅含 `version` 的自动资源配置；其他实现先核对并使用适用的原检查入口，不套用本格式。
- `none`：本次未采用上述资源初始化路径；仍核对声明的挂载及必要路径/工具，不允许夹带静态端点配置。

上述静态文件命名与物理设备映射依据固定版本的 [端点加载实现](https://github.com/vllm-project/vllm-ascend/blob/7759ceecee1c3ea21a4d47d55f93545fca895088/vllm_ascend/utils.py#L690-L721)；自动 UB 与 RoCE 静态资源是不同分支，见同版本的 [部署说明](https://github.com/vllm-project/vllm-ascend/blob/7759ceecee1c3ea21a4d47d55f93545fca895088/docs/source/tutorials/features/pd_disaggregation_mooncake_multi_node.md)。其他版本先核对当前实现，不将此配置推广成所有 A5/连接器的默认值。

## 一份声明用于生成参数和验收

在本次启动记录中保存每节点 JSON。公共构造函数复用角色的共同部分，并填入各节点真实路径/物理 ID；首台试跑与批量节点调用同一构造，不维护两份手写挂载列表。连接器参数也从声明的 `communication.connector_extra_config` 读取，不能在 vLLM 命令中重新填回旧静态路径。

下面仅为字段示例；路径、版本、设备类型和工具须按当前实现替换，不能直接当作已就绪环境：

```json
{
  "schema_version": 1,
  "node": "node-a",
  "container": "example-service",
  "mounts": [
    {"source": "/srv/models/example", "target": "/models", "kind": "directory", "read_only": true}
  ],
  "env": {
    "ASCEND_LOCAL_COMM_RES": "{\"version\":\"1.3\"}",
    "ASCEND_GLOBAL_RESOURCE_CONFIG": ""
  },
  "communication": {"mode": "auto"},
  "required_paths": [
    {"path": "/dev/ummu", "kind": "character_device"},
    {"path": "/dev/uburma", "kind": "character_device"}
  ],
  "required_commands": ["urma_admin"]
}
```

静态方式把 `communication` 换为以下对象，并加入 `source=/srv/comm/endpoints`、`target=/etc/comm-endpoints`、`kind=directory` 的必需挂载；移除自动资源 env 配置。其余所需设备/工具仍按当前实现声明。

```json
{
  "mode": "static",
  "endpoint_directory": "/srv/comm/endpoints",
  "physical_device_ids": [2, 5],
  "connector_extra_config": {"ascend_local_comm_res_path": "/etc/comm-endpoints"}
}
```

`mounts` 只列本次必需的 bind mount，`kind` 为 `file` 或 `directory`，`read_only` 显式布尔值；合法可选挂载由原入口处理，不能混入必需项并静默跳过。`required_paths` 还支持 `character_device`；`required_commands` 可为命令名或明确可执行路径，按宿主当前 PATH 查找。脚本检查自动模式下声明的前置条件，不自动判断设备映射、容器内工具是否可用或初始化是否成功。`env` 的空串用于在 Docker 环境中清除旧值。bind 路径不支持逗号，脚本会明确拒绝。

```bash
python3 scripts/deployment_preflight.py preflight --plan node-a.json
python3 scripts/deployment_preflight.py docker-args --plan node-a.json
```

`docker-args` 成功时输出挂载和环境的 **JSON argv 数组**；失败不输出可用于启动的参数，详情写 stderr。现有启动入口用 `subprocess.run(..., check=True)` 取得它，并将数组展开到同一个 `docker run` 参数列表的容器选项位置（image 之前）；不要拼接为 shell 字符串。示意调用：

```python
declared_args = json.loads(subprocess.check_output(
    [sys.executable, "scripts/deployment_preflight.py", "docker-args", "--plan", plan_path],
    text=True))
# base_args 是原工具已授权的 Docker 选项，image_and_command 来自同一启动方案。
# 同一入口用于首台和批量，不额外追加覆盖声明的 mount/env 或相同目标。
subprocess.run([*base_args, *declared_args, *image_and_command], check=True)
```

脚本不会替调用方执行上面的启动动作。源路径消失、类型错误、缺端点或环境冲突时，保留逐节点错误，在已授权且有验证来源的范围内补齐；否则暂停受影响的启动步骤并说明恢复条件。修复后只重查受影响项及必要关联条件，不重新初始化整套环境。

## 创建后核对实际容器

通过原执行工具读取该节点**实际目标容器**的 inspect，保存同次证据，再用相同声明比对：

```bash
docker inspect example-service > node-a.inspect.json
python3 scripts/deployment_preflight.py verify --plan node-a.json --inspect node-a.inspect.json
```

工具要求 inspect 只含一个同名容器，核对每个必需挂载的 bind 类型、源、目标、读写标志，以及声明的容器环境；错误容器、缺挂载、同目标重复或环境冲突都失败。它不会把容器写层中“恰好存在同名文件”算作挂载，也不阻止原工具添加不冲突的其他必要选项。

这份快照需由原工具关联到实际节点和本次创建；工具不能鉴别人工伪造或旧快照。宿主前置检查不能替代容器内的路径类型/可执行工具核验；映射设备和工具应由原入口在容器内只读确认。必需项全部通过后再启动模型，并按当前通信实现核对资源初始化、数据平面和最小业务请求。预检 `ok=true` 只代表声明覆盖的文件、挂载、环境条件符合，不能作为 NPU、UB/HCCL、模型或 PD 验收。

退出码：`0` 声明覆盖的检查通过；`1` 检查不符合；`2` 输入/文件读取错误。合成回归由根测试自动发现，也可单独运行：

```bash
python -m unittest discover -s tests -p test_deployment_preflight.py -v
```
