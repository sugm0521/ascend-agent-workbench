# 已有 GPQA 客户端的多组执行

这些辅助脚本复用已验证的 AISBench GPQA run，准备新的独立输出目录并监督本次 HTTP 客户端命令。运行时使用原精度客户端的 AISBench 版本、数据和配置；它们不准备模型服务或远程环境。执行前固定所用客户端版本和原 run 的来源，沿用任务已确认的采样参数与验收标准。

## 入口与输入

| 入口 | 用途与前提 |
|---|---|
| [gpqa_batch_prepare.py](../../scripts/gpqa_batch_prepare.py) | 从显式旧 run 校验数据/config 哈希，准备新的分组根目录；组数参数化，仅改已知路径常量 |
| [gpqa_batch_supervisor.py](../../scripts/gpqa_batch_supervisor.py) | 读取明确 plan，串行 evaluate → collect，记录客户端身份、日志、退出状态及结果哈希 |
| [gpqa_collect_run.py](../../scripts/gpqa_collect_run.py) | 在已有 AISBench 精度环境内调用 GPQA 官方后处理与 evaluator，对照官方结果，要求唯一实验及完整请求证据 |
| [gpqa_batch_status.py](../../scripts/gpqa_batch_status.py) | 只读指定 plan/state 及文件计数；文件数不能代替完成的题数 |

旧 run 需要 `setup/eval-manifest.json`、manifest 指定的数据与哈希，以及 `configs/models/kimi_gpqa.py`、`configs/datasets/gpqa_diamond.py`、`setup/observed_api.py`。这些是该客户端的具体输入合同；没有对应材料时保留缺口，不能套用到其他评测器。完整原 run 留在使用者的环境，不随工具发布。

## 准备与执行

在工作台根使用实际路径替换占位值：

```sh
python scripts/gpqa_batch_prepare.py --source-run /task/verified-old-run \
  --output-root /task/fresh-attempt --groups 5 \
  --health-url http://SERVICE/healthcheck
python scripts/gpqa_batch_supervisor.py --plan /task/fresh-attempt/batch-plan.json \
  --state-file /task/fresh-attempt/batch-state.json --validate-only
```

prepare 默认使用同目录的 collector，也可通过 `--collector` 指定已准备到精度客户端的同一文件。prepare 和 validate-only 不发送模型负载。plan 中的实际解释器、命令及路径应属于执行客户端；跨环境搬运时通过原执行工具保持这些路径有效，不把本机目录当远端目录。

实际执行需要 Bash，以及执行环境 PATH 中可用的 `ais_bench`。collector 命令固定使用生成 plan 时的 Python，因此应在已验证的 AISBench 精度环境中运行 prepare，并核对该 Python 与 PATH 中的 `ais_bench` 属于预期兼容环境。生成的启动脚本会在客户端进程中清除大小写的 FTP、HTTP、HTTPS、ALL 代理变量；监督器的健康检查也使用直连。执行前确认客户端到目标服务的直连可达性，依赖代理的环境不能直接套用该启动方式；`--validate-only` 不验证这些运行条件。

确认新 plan 与环境后，使用同一监督器命令去掉 `--validate-only` 执行；通过 status 读取本次 plan/state。控制命令启动成功不代表全部组完成，读取结果前核对每组退出状态和输出文件。监督器只管理本次客户端，不控制模型服务。

## 恢复与结果

同一 plan 显式传 `--resume` 才恢复。已运行的监督器或客户端拒绝重复启动；完成组须有匹配的结果哈希才跳过；仅确定 pending 的组继续。身份未知、plan 改变、失败组或缺失 state 时保留原失败，先核对实际状态；需要新尝试则使用新的输出根，不覆盖旧 run。

逐组报告原生评分、分母、有效答案与结束原因，再汇总。需要输出审计时使用[证据报告](aisbench-evidence.md)，不能用异常候选直接推断模型根因。现有服务的 profiling 按[原执行入口](../../upstream/skill-mapping.md#运行体系与执行入口)处理，采样轮与正式性能轮分别记录。

本机合成回归验证输入约束与监督器行为，不能证明 AISBench 评分环境、远端服务或 NPU 已验收；可复验入口见[验证说明](../maintenance/validation.md)。
