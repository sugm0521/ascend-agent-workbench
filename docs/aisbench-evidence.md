# AISBench结果证据报告

[aisbench_evidence_report.py](../scripts/aisbench_evidence_report.py)是Python标准库的离线工具，只消费明确指定的已有评测结果；不安装AISBench、不发请求、不修改评分、不控制服务。官方指标、独立格式检查、API结束状态和输出审计分别呈现。没有阈值或对照时给出测量，不自动宣称精度通过。

## 输入与调用

创建任务专属spec，路径相对spec所在目录，或显式绝对路径。每个run独立指定样本文件、解析器与预期条数，不默认选择最新目录。示例中的题数、选项、字段和路径只演示接口，不是默认GPQA配置：

```json
{
  "runs": [
    {
      "id": "round1",
      "format": "aisbench",
      "samples": "eval/selected-run/predictions/model/dataset.jsonl",
      "evidence_dir": "api-evidence",
      "expected_count": 198,
      "parser": {
        "type": "choice",
        "source": "final_content",
        "pattern": "(?i)ANSWER\\s*:\\s*([A-D])\\b",
        "choices": ["A", "B", "C", "D"],
        "normalize": "upper"
      },
      "official_result": "eval/selected-run/results/model/dataset.json",
      "expected_request": {"max_tokens": 81920, "temperature": 1, "top_p": 1, "reasoning_effort": "max"}
    }
  ]
}
```

```bash
python scripts/aisbench_evidence_report.py --spec /task/selected-runs.json --output-dir /task/new-report
```

输出目录必须是新的，保留旧报告。正常交付用基本检查；用户要求审计，或有效答案/字符等已有证据异常时，加`--audit-output --example-budget-bytes 65536 --max-examples 8`。预算按每组的样例文件计算，stdout默认最多16384字节，只给报告路径、字节数、SHA和状态。

## 明确选择输入schema和解析器

| format | 样本结构与证据边界 |
|---|---|
| `aisbench` | 显式JSON/JSONL预测文件，每条为`id/uuid/prediction/gold/success`或AISBench的ID→记录映射；提供evidence_dir时用`request.output_uuid`关联`.request.json`及同名前缀`.response.json` |
| `samples` | JSON列表或JSONL，显式`id`、可选`uuid/prediction/gold/success`；已有API证据可内嵌`request/response`，response采用chat completions结构；不导出请求体、头或鉴权 |
| `answer-index` | 已保存的逐题答案索引，如`id/predicted/gold/finish_reason/completion_tokens`；仅回放记录的字段，不冒充原始API或全文输出审计 |

JSONL只按文件实际LF读取，输出中的U+2028不会被当换行切开。解析器必须声明`type`：`choice`需选项列表，`regex`需匹配规则，`nonempty`只检查非空、不计算精度。pattern有且只有一个捕获组；省略pattern时匹配整个去空白文本。`source=prediction`消费预测/已提取答案，`source=final_content`消费原始API最终正文，不能把缺少正文的reasoning当成最终答案。

独立格式分数是该显式解析器下的精确匹配统计，可能不同于官方数据集后处理；官方数值保持原尺度。`official_metric_keys`可指定原结果中需要呈现的数字指标。任务reference、阈值和基线比较继续由原correctness流程负责，不由本工具生成另一套精度通过规则。

request证据只核对显式expected_request中的生成字段（model/max_tokens/temperature/top_p/reasoning_effort/stream/seed/ignore_eos）。缺失字段不当作已确认，重复ID、缺失响应、参数不符、样本数不符和歧义的多次成功重试均显式列为报告不完整；不按文件遍历顺序默选最后一个成功响应。先查已有请求关联，必要时明确最终响应后再报告，不自动重发题目。

## 输出与判断边界

- `report.json`/`report.md`先列每组，再汇总；汇总的独立格式分数按实际有gold的样本加权，并与各组官方指标分开。
- 各组`<id>.samples.jsonl`保存行级统计、标记与参数差异，`<id>.examples.jsonl`保存有限的正文/推理尾部。完整长回答和原始报告仍在输入位置。
- `stop_without_valid_answer_candidate`只是缺少有效答案候选，`reported_length_limit`才对应API的length。文本是否异常提前结束需要读取尾部确认；工具不自动归因EOS、PD、CANN或DSpark。
- U+FFFD、异常控制字符、隐藏字符分别记录。`known_special_tokens`可显式填写已核对模型的token字面量清单；未分类的`<|...|>`或类似串仅作候选，因此数学式`<|v_i - v_j|>`不能直接算特殊token错误。重复题干、蛋白序列等仅标重复候选，不称死循环；逻辑错误需要独立推理或计算证据。
- 原始响应不可用时，不能用答案索引声称完成全文乱码检查。审计层级、缺失字段与不完整结果在报告中可见。

退出码：0完整生成报告（不代表模型精度通过）；1已生成但输入证据不完整；2配置、输入或写入错误。读取结果前核对status及原生证据，不能把控制命令exit0当业务完成。

## 本任务SSH通道和多组脚本

[image_batch_session.py](../tasks/1014/scripts/image_batch_session.py)继续原连接方式，仅将输出读取交给[ssh_output_capture.py](../tasks/1014/scripts/ssh_output_capture.py)。两个流均持续排空，保留有界尾部，记录observed_bytes/retained_bytes/truncated和保留文本UTF-8解码问题。`command_exit_code`与`business_completion=not_checked`分开；旧每节点`exit_code`仅为兼容字段，批次不再输出含糊的passed。解析JSON前要求`output_complete=true`；不完整时按已有传输路径取得文件，不直接解析尾部或将通道截断误认模型截断。超时关闭控制channel，不推断远端进程已退出，也不自动重试。完整上传payload（含TASK_NODE前缀）必须小于1MB。

本任务的多组客户端重构和已有服务profiling步骤见[任务调用说明](../tasks/1014/多组评测与Profiling-调用说明.md)，没有建设新的SSH、资源或服务调度系统。
